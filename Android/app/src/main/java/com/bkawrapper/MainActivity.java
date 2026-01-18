package com.bkawrapper;

import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BK_APP";

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private FrameLayout progressOverlay;
    private Button loadButton;

    private boolean generatingOTR = false;
    private boolean romReady = false;
    private boolean gameInitialized = false;

    private Handler progressHandler = new Handler();
    private ActivityResultLauncher<String[]> romPickerLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.glSurfaceView);
        progressOverlay = findViewById(R.id.progressOverlay);
        loadButton = findViewById(R.id.loadButton);

        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // AssetManager setup for native OTR loading
        AssetManager assetManager = getAssets();
        NativeBridge.setAssetManager(assetManager);

        // ROM picker
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) loadRom(uri);
                }
        );

        loadButton.setOnClickListener(v -> romPickerLauncher.launch(new String[]{"application/octet-stream"}));
    }

    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM from URI: " + uri);

            // Pass URI to native bridge
            NativeBridge.loadRom(uri);

            // Show progress overlay
            showOTRProgress();
            generatingOTR = true;

            // Kick off native OTR generation
            NativeBridge.processRom();

            // Poll for progress
            progressHandler.post(this::pollOTRProgress);

        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
        }
    }

    private void showOTRProgress() {
        runOnUiThread(() -> {
            progressOverlay.setVisibility(View.VISIBLE);
            loadButton.setVisibility(View.GONE); // hide ROM picker
        });
    }

    private void hideOTRProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));
    }

    private void pollOTRProgress() {
        float progress = NativeBridge.getOTRProgress();
        Log.d(TAG, "OTR progress: " + (int)(progress * 100) + "%");

        if (progress >= 1.0f) {
            generatingOTR = false;
            romReady = true;

            // Attach the native texture ID
            int texId = NativeBridge.getTextureId();
            if (texId != 0) {
                glRenderer.attachTexture(texId);
                hideOTRProgress();
                tryStartGame();
            } else {
                Log.e(TAG, "Native texture ID not available after OTR generation");
                // Retry after a short delay
                progressHandler.postDelayed(this::pollOTRProgress, 50);
                return;
            }
        } else {
            progressHandler.postDelayed(this::pollOTRProgress, 50);
        }
    }

    private void tryStartGame() {
        if (!romReady || gameInitialized) return;

        Log.i(TAG, "Initializing game");

        NativeBridge.initGame(glSurfaceView.getHolder().getSurface());
        gameInitialized = true;
        NativeBridge.startGameLoop();
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();
        NativeBridge.stopGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
        if (gameInitialized) NativeBridge.startGameLoop();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        NativeBridge.cleanupGame();
    }
}