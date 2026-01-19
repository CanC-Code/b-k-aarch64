package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.net.Uri;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.database.Cursor;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;

public class MainActivity extends Activity {

    private static final int REQUEST_LOAD_ROM = 1001;

    private GLSurfaceView glSurfaceView;
    private LinearLayout progressOverlay;
    private ProgressBar progressBar;
    private TextView progressText;
    private Button loadButton;

    private final Handler uiHandler = new Handler(Looper.getMainLooper());
    private volatile boolean buildingOTR = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface);
        progressOverlay = findViewById(R.id.progress_overlay);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);
        loadButton = findViewById(R.id.button_load_game);

        // OpenGL setup (renderer can be swapped later)
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(new GLRenderer());
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // Initialize native side
        AssetManager assetManager = getAssets();
        NativeBridge.nativeInit(assetManager);

        loadButton.setOnClickListener(v -> openRomPicker());
    }

    private void openRomPicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(intent, REQUEST_LOAD_ROM);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_LOAD_ROM && resultCode == RESULT_OK && data != null) {
            Uri romUri = data.getData();
            if (romUri != null) {
                loadAndProcessRom(romUri);
            }
        }
    }

    private void loadAndProcessRom(Uri romUri) {
        try {
            byte[] romData = readAllBytes(romUri);
            String yamlPath = selectYamlForRom(romData);

            progressOverlay.setVisibility(View.VISIBLE);
            progressBar.setProgress(0);
            progressText.setText("0%");
            buildingOTR = true;

            String outputDir = getFilesDir().getAbsolutePath();

            new Thread(() -> {
                boolean success = NativeBridge.nativeGenerateOTR(
                        romData,
                        yamlPath,
                        outputDir
                );

                if (!success) {
                    buildingOTR = false;
                    uiHandler.post(() -> progressText.setText("Failed"));
                    return;
                }

                // Poll progress
                while (buildingOTR) {
                    float p = NativeBridge.nativeGetProgress();
                    int percent = (int) (p * 100f);

                    uiHandler.post(() -> {
                        progressBar.setProgress(percent);
                        progressText.setText(percent + "%");
                    });

                    if (p >= 1.0f) {
                        buildingOTR = false;
                        break;
                    }

                    try {
                        Thread.sleep(50);
                    } catch (InterruptedException ignored) {}
                }

                uiHandler.post(() -> {
                    progressOverlay.setVisibility(View.GONE);
                    String otrPath = outputDir + "/game.otr";
                    NativeBridge.nativeLoadOTR(otrPath);
                });

            }).start();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private byte[] readAllBytes(Uri uri) throws Exception {
        try (InputStream in = getContentResolver().openInputStream(uri);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {

            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
            return out.toByteArray();
        }
    }

    /**
     * Minimal, deterministic ROM region check.
     * You can replace this with CRC/MD5 later.
     */
    private String selectYamlForRom(byte[] rom) {
        // N64 ROM country byte is at 0x3E
        if (rom.length > 0x3E) {
            byte region = rom[0x3E];
            if (region == 'P') {
                return "otr_yaml/decompressed.pal.yaml";
            }
        }
        return "otr_yaml/decompressed.us.v10.yaml";
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
    }
}