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

        // REQUIRED: set AssetManager before any native calls
        NativeBridge.setAssetManager(getAssets());

        // --- bind views (MATCH XML IDS EXACTLY) ---
        glSurfaceView   = findViewById(R.id.surface_gl);
        progressOverlay = findViewById(R.id.progressOverlay);
        progressBar     = findViewById(R.id.otrProgressBar);
        progressText    = findViewById(R.id.otrProgressText);
        loadButton      = findViewById(R.id.button_load_game);

        // --- setup GLSurfaceView ---
        glRenderer = new GLRenderer(this);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        loadButton.setOnClickListener(v -> pickRom());
    }

    public void onSurfaceReady() {
        // Reserved for later native surface init
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

        if (requestCode != PICK_ROM_REQUEST || resultCode != RESULT_OK || data == null) return;

        Uri uri = data.getData();
        if (uri == null) return;

        progressOverlay.setVisibility(View.VISIBLE);
        progressBar.setProgress(0);
        progressText.setText("0%");

        new Thread(() -> {
            try {
                NativeBridge.loadRomFromUri(getContentResolver(), uri);
                NativeBridge.processRom();

                // Poll progress while building
                while (NativeBridge.getOTRProgress() < 1.0f) {
                    float p = NativeBridge.getOTRProgress();
                    runOnUiThread(() -> {
                        progressBar.setProgress((int)(p*100));
                        progressText.setText((int)(p*100) + "%");
                    });
                    Thread.sleep(50);
                }

                // Retrieve OTR safely
                byte[] otrData = NativeBridge.getOTR();
                if (otrData != null && otrData.length > 0) {
                    runOnUiThread(() -> {
                        glRenderer.setOTRData(otrData);
                        progressOverlay.setVisibility(View.GONE);
                    });
                } else {
                    runOnUiThread(() -> {
                        Toast.makeText(this,
                                "OTR generation failed",
                                Toast.LENGTH_LONG).show();
                        progressOverlay.setVisibility(View.GONE);
                    });
                }

            } catch (IOException | InterruptedException e) {
                runOnUiThread(() -> {
                    progressOverlay.setVisibility(View.GONE);
                    Toast.makeText(this,
                            "Failed to load ROM: " + e.getMessage(),
                            Toast.LENGTH_LONG).show();
                });
            }
        }).start();
    }
}