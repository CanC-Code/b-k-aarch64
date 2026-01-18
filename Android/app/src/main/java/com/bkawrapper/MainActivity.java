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

        // 🔴 Set AssetManager before any native calls
        NativeBridge.setAssetManager(getAssets());

        // --- bind views ---
        glSurfaceView   = findViewById(R.id.surface_gl);
        progressOverlay = findViewById(R.id.progressOverlay);
        loadButton      = findViewById(R.id.button_load_game);

        // --- setup GLSurfaceView ---
        glRenderer = new GLRenderer(this);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        loadButton.setOnClickListener(v -> pickRom());
    }

    // Called by GLRenderer when surface is ready
    public void onSurfaceReady() {
        // reserved for later native surface init
    }

    private void pickRom() {
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.setType("*/*");
        startActivityForResult(
                Intent.createChooser(intent, "Select ROM"),
                PICK_ROM_REQUEST
        );
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == PICK_ROM_REQUEST && resultCode == RESULT_OK && data != null) {
            Uri uri = data.getData();
            if (uri == null) return;

            // Show progress overlay
            progressOverlay.setVisibility(View.VISIBLE);

            // Load and process ROM in background thread
            new Thread(() -> {
                try {
                    NativeBridge.loadRomFromUri(getContentResolver(), uri);
                    NativeBridge.processRom();

                    // Retrieve OTR bytes after generation completes
                    byte[] otrData;
                    while (NativeBridge.getOTRProgress() < 1.0f) {
                        // Wait for OTR to finish; GLRenderer updates progress
                        Thread.sleep(16);
                    }
                    otrData = NativeBridge.getOTR();

                    // Attach texture to renderer
                    glRenderer.setOTRData(otrData);

                } catch (IOException | InterruptedException e) {
                    runOnUiThread(() -> {
                        progressOverlay.setVisibility(View.GONE);
                        Toast.makeText(
                                MainActivity.this,
                                "Failed to load ROM: " + e.getMessage(),
                                Toast.LENGTH_LONG
                        ).show();
                    });
                }
            }).start();
        }
    }
}