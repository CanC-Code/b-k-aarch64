package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.opengl.GLSurfaceView;

import java.io.IOException;

public class MainActivity extends Activity {

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private FrameLayout progressOverlay;
    private ProgressBar progressBar;
    private TextView progressText;
    private Button loadButton;

    private static final int PICK_ROM_REQUEST = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Set AssetManager before any native calls
        NativeBridge.setAssetManager(getAssets());

        // Bind views
        glSurfaceView   = findViewById(R.id.surface_gl);
        progressOverlay = findViewById(R.id.progressOverlay);
        progressBar     = findViewById(R.id.otrProgressBar);
        progressText    = findViewById(R.id.otrProgressText);
        loadButton      = findViewById(R.id.button_load_game);

        // Setup GLSurfaceView and Renderer
        glRenderer = new GLRenderer(glSurfaceView, progressBar, progressText, progressOverlay);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        loadButton.setOnClickListener(v -> pickRom());
    }

    private void pickRom() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("*/*");
        startActivityForResult(Intent.createChooser(intent, "Select ROM"), PICK_ROM_REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode != PICK_ROM_REQUEST || resultCode != RESULT_OK || data == null) return;

        Uri uri = data.getData();
        if (uri == null) return;

        // Show progress overlay
        progressOverlay.setVisibility(View.VISIBLE);
        progressBar.setProgress(0);
        progressText.setText("0%");

        // Background thread for ROM load + OTR generation
        new Thread(() -> {
            try {
                NativeBridge.loadRomFromUri(getContentResolver(), uri);
                NativeBridge.processRom();

                // Poll progress
                while (NativeBridge.getOTRProgress() < 1.0f) {
                    float progress = NativeBridge.getOTRProgress();
                    runOnUiThread(() -> {
                        progressBar.setProgress((int)(progress * 100));
                        progressText.setText((int)(progress * 100) + "%");
                    });
                    Thread.sleep(16);
                }

                // Retrieve OTR bytes
                byte[] otrData = NativeBridge.getOTR();

                // Apply OTR on GL thread
                runOnUiThread(() -> glRenderer.setOTRData(otrData));

            } catch (IOException | InterruptedException e) {
                runOnUiThread(() -> {
                    progressOverlay.setVisibility(View.GONE);
                    Toast.makeText(MainActivity.this,
                            "Failed to load ROM: " + e.getMessage(),
                            Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }
}