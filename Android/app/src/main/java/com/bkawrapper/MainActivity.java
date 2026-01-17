// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.os.Bundle;
import android.view.View;
import android.net.Uri;
import android.util.Log;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.opengl.GLSurfaceView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "MainActivity";

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private Button loadButton;
    private LinearLayout menuOverlay;
    private LinearLayout progressOverlay;
    private ProgressBar otrProgressBar;
    private TextView otrProgressText;

    private boolean romReady = false;

    private ActivityResultLauncher<String[]> romPickerLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.surface_gl);
        loadButton = findViewById(R.id.button_load_game);
        menuOverlay = findViewById(R.id.menu_overlay);
        progressOverlay = findViewById(R.id.progress_overlay);
        otrProgressBar = findViewById(R.id.otr_progress_bar);
        otrProgressText = findViewById(R.id.otr_progress_text);

        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) loadRom(uri);
                });

        loadButton.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );

        menuOverlay.findViewById(R.id.button_resume).setOnClickListener(v -> hideMenu());
        menuOverlay.findViewById(R.id.button_exit).setOnClickListener(v -> finish());
    }

    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM...");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);
            runOnUiThread(() -> {
                romReady = true;
                loadButton.setVisibility(View.GONE);
                tryStartGame();
            });
        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
        }
    }

    private void showProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.VISIBLE));
    }

    private void hideProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));
    }

    private void updateProgress() {
        float progress = NativeBridge.getOTRProgress(); // returns 0.0 to 1.0
        runOnUiThread(() -> {
            otrProgressBar.setProgress((int) (progress * 100));
            otrProgressText.setText(String.format("%.1f%%", progress * 100));
        });
    }

    private void tryStartGame() {
        // Implement your game-start logic here
        Log.i(TAG, "Starting game...");
    }

    private void hideMenu() {
        menuOverlay.setVisibility(View.GONE);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Cleanup code here
    }
}