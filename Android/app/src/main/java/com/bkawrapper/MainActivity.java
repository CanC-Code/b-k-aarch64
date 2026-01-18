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
        glSurfaceView = findViewById(R.id.surface_gl);
        progressOverlay = findViewById(R.id.progress_overlay);
        loadButton = findViewById(R.id.button_load_game);

        // --- setup GLSurfaceView ---
        glRenderer = new GLRenderer(this);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // --- button click to load ROM ---
        loadButton.setOnClickListener(v -> pickRom());
    }

    /**
     * Called by GLRenderer when surface is ready.
     * Optional: attach existing OTR texture or start loop.
     */
    public void onSurfaceReady() {
        // Example: glRenderer.attachTexture(NativeBridge.getTextureId());
    }

    /**
     * Start Android file picker for ROM selection.
     */
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

                // Process ROM on background thread
                new Thread(() -> {
                    try {
                        NativeBridge.loadRomFromUri(getContentResolver(), uri);
                        NativeBridge.processRom();

                        // retrieve OTR bytes
                        byte[] otrData = NativeBridge.getOTR();

                        runOnUiThread(() -> {
                            glRenderer.setOTRData(otrData);
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