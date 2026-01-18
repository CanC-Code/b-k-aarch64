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

        // Set AssetManager for native use
        NativeBridge.setAssetManager(getAssets());

        glSurfaceView   = findViewById(R.id.surface_gl);
        progressOverlay = findViewById(R.id.progressOverlay);
        progressBar     = findViewById(R.id.otrProgressBar);
        progressText    = findViewById(R.id.otrProgressText);
        loadButton      = findViewById(R.id.button_load_game);

        glRenderer = new GLRenderer(this);
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

        if (requestCode == PICK_ROM_REQUEST && resultCode == RESULT_OK && data != null) {
            Uri uri = data.getData();
            if (uri == null) return;

            progressOverlay.setVisibility(View.VISIBLE);
            progressBar.setProgress(0);
            progressText.setText("0%");

            NativeBridge.loadRomFromUri(getContentResolver(), uri);
            NativeBridge.processRom();

            // Progress updater thread
            new Thread(() -> {
                while (NativeBridge.getOTRProgress() < 1.0f) {
                    float prog = NativeBridge.getOTRProgress();
                    runOnUiThread(() -> {
                        progressBar.setProgress((int)(prog*100));
                        progressText.setText((int)(prog*100) + "%");
                    });
                    try { Thread.sleep(50); } catch (InterruptedException ignored) {}
                }

                runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));

                // Get OTR data and update GLRenderer on GL thread
                byte[] otrData = NativeBridge.getOTR();
                glSurfaceView.queueEvent(() -> glRenderer.setOTRData(otrData));

            }).start();
        }
    }
}