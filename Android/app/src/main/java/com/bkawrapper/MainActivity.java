package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.Nullable;

import android.opengl.GLSurfaceView;

import java.io.InputStream;

public class MainActivity extends Activity {

    private static final int REQUEST_CODE_OPEN_ROM = 1001;

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private Button loadGameButton;
    private LinearLayout progressOverlay;
    private ProgressBar progressBar;
    private TextView progressText;

    private Handler uiHandler;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        uiHandler = new Handler(Looper.getMainLooper());

        glSurfaceView = findViewById(R.id.gl_surface);
        loadGameButton = findViewById(R.id.button_load_game);
        progressOverlay = findViewById(R.id.progress_overlay);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

        glRenderer = new GLRenderer(this);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);

        // Initialize native side with AssetManager
        AssetManager assetManager = getAssets();
        NativeBridge.nativeInit(assetManager);

        loadGameButton.setOnClickListener(v -> openRomFile());
    }

    /** Open ROM using SAF */
    private void openRomFile() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(intent, REQUEST_CODE_OPEN_ROM);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_CODE_OPEN_ROM && resultCode == RESULT_OK && data != null) {
            Uri romUri = data.getData();
            if (romUri != null) {
                try (InputStream is = getContentResolver().openInputStream(romUri)) {
                    byte[] romBytes = new byte[is.available()];
                    is.read(romBytes);

                    startOTRGeneration(romBytes);

                } catch (Exception e) {
                    e.printStackTrace();
                    Toast.makeText(this, "Failed to read ROM: " + e.getMessage(), Toast.LENGTH_LONG).show();
                }
            }
        }
    }

    /** Trigger OTR generation in native code */
    private void startOTRGeneration(byte[] romBytes) {
        progressOverlay.setVisibility(View.VISIBLE);
        progressBar.setProgress(0);
        progressText.setText("0%");

        new Thread(() -> {
            boolean success = NativeBridge.nativeGenerateOTR(
                    romBytes,
                    "otr_yaml/decompressed.us.v10.yaml",
                    getFilesDir().getAbsolutePath()
            );

            if (success) {
                // Wait for progress to reach 1.0
                while (NativeBridge.nativeGetProgress() < 1.0f) {
                    float progress = NativeBridge.nativeGetProgress();
                    uiHandler.post(() -> {
                        progressBar.setProgress((int)(progress * 100));
                        progressText.setText(String.format("%d%%", (int)(progress * 100)));
                    });

                    try { Thread.sleep(50); } catch (InterruptedException ignored) {}
                }

                uiHandler.post(() -> {
                    progressBar.setProgress(100);
                    progressText.setText("100%");
                    progressOverlay.setVisibility(View.GONE);

                    // Notify GLRenderer to refresh OTR
                    glRenderer.refreshOTR();
                    Toast.makeText(this, "OTR generation complete", Toast.LENGTH_SHORT).show();
                });

            } else {
                uiHandler.post(() -> {
                    progressOverlay.setVisibility(View.GONE);
                    Toast.makeText(this, "OTR generation failed", Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }
}