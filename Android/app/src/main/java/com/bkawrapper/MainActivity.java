package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_ROM_FILE = 1;

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private Button loadGameButton;
    private LinearLayout progressOverlay;
    private ProgressBar progressBar;
    private TextView progressText;

    private Handler uiHandler = new Handler();
    private Runnable progressRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);

        loadGameButton = findViewById(R.id.button_load_game);
        progressOverlay = findViewById(R.id.progress_overlay);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

        loadGameButton.setOnClickListener(v -> openROMFilePicker());

        // Initialize native system with AssetManager
        NativeBridge.nativeInit(getAssets());
    }

    private void openROMFilePicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*"); // ROM file type
        startActivityForResult(intent, REQUEST_ROM_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_ROM_FILE && resultCode == Activity.RESULT_OK) {
            if (data != null) {
                Uri romUri = data.getData();
                loadROMAndGenerateOTR(romUri);
            }
        }
    }

    private void loadROMAndGenerateOTR(Uri romUri) {
        try {
            // Load ROM bytes from SAF
            InputStream romStream = getContentResolver().openInputStream(romUri);
            ByteArrayOutputStream romBuffer = new ByteArrayOutputStream();
            byte[] temp = new byte[8192];
            int read;
            while ((read = romStream.read(temp)) != -1) {
                romBuffer.write(temp, 0, read);
            }
            romStream.close();
            byte[] romBytes = romBuffer.toByteArray();

            // Select YAML from assets (example: pal)
            String yamlAssetPath = "otr_yaml/decompressed.pal.yaml";

            progressOverlay.setVisibility(View.VISIBLE);
            progressBar.setProgress(0);
            progressText.setText("0%");

            // Update progress periodically
            progressRunnable = new Runnable() {
                @Override
                public void run() {
                    float progress = NativeBridge.nativeGetProgress();
                    progressBar.setProgress((int) (progress * 100));
                    progressText.setText((int) (progress * 100) + "%");
                    if (progress < 1.0f) {
                        uiHandler.postDelayed(this, 50);
                    }
                }
            };
            uiHandler.post(progressRunnable);

            // Generate OTR
            new Thread(() -> {
                boolean success = NativeBridge.nativeGenerateOTR(romBytes, yamlAssetPath, getFilesDir().getAbsolutePath());
                uiHandler.post(() -> {
                    uiHandler.removeCallbacks(progressRunnable);
                    progressOverlay.setVisibility(View.GONE);
                    if (success) {
                        // Retrieve in-memory OTR from native
                        byte[] generatedOTR = NativeBridge.getGeneratedOTRBytes();
                        glRenderer.loadOTR(generatedOTR);
                    }
                });
            }).start();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}