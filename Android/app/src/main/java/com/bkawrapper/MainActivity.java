package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.Toast;
import android.opengl.GLSurfaceView;

import java.io.IOException;

public class MainActivity extends Activity {

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private FrameLayout progressOverlay;
    private Button loadButton;

    private static final int PICK_ROM_REQUEST = 1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // --- bind views ---
        glSurfaceView = findViewById(R.id.glSurfaceView);
        progressOverlay = findViewById(R.id.progressOverlay);
        loadButton = findViewById(R.id.loadButton);

        // --- setup GLSurfaceView ---
        glRenderer = new GLRenderer(this);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // --- button click to load ROM ---
        loadButton.setOnClickListener(v -> pickRom());
    }

    /** Called by GLRenderer when the surface is ready */
    public void onSurfaceReady() {
        // Optional: attach texture if OTR bytes already exist
    }

    /** Open file picker to select ROM */
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

                new Thread(() -> {
                    try {
                        // Load ROM via NativeBridge
                        NativeBridge.loadRomFromUri(getContentResolver(), uri);
                        NativeBridge.processRom();

                        // Retrieve OTR bytes (GPU texture)
                        byte[] otrData = NativeBridge.getOTR();

                        runOnUiThread(() -> {
                            if (otrData != null && otrData.length > 0) {
                                glRenderer.setOTRData(otrData);
                            }
                            progressOverlay.setVisibility(View.GONE);
                        });
                    } catch (IOException e) {
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