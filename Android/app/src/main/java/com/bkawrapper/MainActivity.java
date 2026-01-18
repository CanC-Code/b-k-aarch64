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

        // --- bind views ---
        glSurfaceView = findViewById(R.id.surface_gl);
        progressOverlay = findViewById(R.id.progress_overlay);
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);
        loadButton = findViewById(R.id.button_load_game);

        // --- setup GLSurfaceView ---
        glRenderer = new GLRenderer(this);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // --- button click to load ROM ---
        loadButton.setOnClickListener(v -> pickRom());
    }

    // Called by GLRenderer when surface is ready
    public void onSurfaceReady() {
        // Optional: start game loop if already loaded
    }

    private void pickRom() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("*/*"); // accept all files
        startActivityForResult(Intent.createChooser(intent, "Select ROM"), PICK_ROM_REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == PICK_ROM_REQUEST && resultCode == RESULT_OK) {
            Uri uri = data.getData();
            if (uri != null) {
                progressOverlay.setVisibility(View.VISIBLE);
                progressBar.setProgress(0);
                progressText.setText("0%");

                new Thread(() -> {
                    try {
                        NativeBridge.loadRomFromUri(getContentResolver(), uri);
                        NativeBridge.processRom();

                        // Poll OTR progress until generation completes
                        byte[] otrData;
                        while ((otrData = NativeBridge.getOTR()) == null) {
                            float progress = NativeBridge.getOTRProgress() * 100f;
                            runOnUiThread(() -> {
                                progressBar.setProgress((int) progress);
                                progressText.setText(String.format("%.0f%%", progress));
                            });
                            Thread.sleep(50);
                        }

                        // OTR is ready, attach texture
                        byte[] finalOtrData = otrData;
                        runOnUiThread(() -> {
                            glRenderer.setOTRData(finalOtrData);
                            progressOverlay.setVisibility(View.GONE);
                            loadButton.setVisibility(View.GONE);
                        });

                    } catch (IOException | InterruptedException e) {
                        runOnUiThread(() -> {
                            progressOverlay.setVisibility(View.GONE);
                            Toast.makeText(this, "Failed to load ROM: " + e.getMessage(), Toast.LENGTH_LONG).show();
                        });
                    }
                }).start();
            }
        }
    }
}