// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.opengl.GLSurfaceView;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BK_APP";

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private ActivityResultLauncher<String[]> romPickerLauncher;

    private Button loadButton;
    private LinearLayout menuOverlay;
    private LinearLayout progressOverlay;
    private ProgressBar otrProgressBar;
    private TextView otrProgressText;

    // Launch gates
    private boolean surfaceReady = false;
    private boolean romReady = false;
    private boolean gameInitialized = false;
    private boolean gameRunning = false;

    // Swipe gesture tracking for menu
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    private HandlerThread progressThread;
    private Handler progressHandler;
    private boolean generatingOTR = false;

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

        // OpenGL setup
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // ROM picker
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) loadRom(uri);
                }
        );

        loadButton.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );

        // Menu buttons
        menuOverlay.findViewById(R.id.button_resume).setOnClickListener(v -> hideMenu());
        menuOverlay.findViewById(R.id.button_exit).setOnClickListener(v -> finish());
        menuOverlay.findViewById(R.id.button_settings).setOnClickListener(v ->
                Log.i(TAG, "Settings clicked (stub)"));
        menuOverlay.findViewById(R.id.button_controller).setOnClickListener(v ->
                Log.i(TAG, "Controller Layout clicked (stub)"));

        Log.i(TAG, "App started – waiting for ROM");

        // Setup progress polling thread
        progressThread = new HandlerThread("OTRProgressThread");
        progressThread.start();
        progressHandler = new Handler(progressThread.getLooper());
    }

    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM...");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);

            // Start OTR progress overlay
            showOTRProgress();

            // Start polling OTR progress
            generatingOTR = true;
            progressHandler.post(this::pollOTRProgress);

        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
        }
    }

    private void showOTRProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.VISIBLE));
    }

    private void hideOTRProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));
    }

    private void pollOTRProgress() {
        if (!generatingOTR) return;

        float progress = NativeBridge.getOTRProgress();
        int percent = Math.min(100, Math.max(0, (int)(progress * 100)));

        runOnUiThread(() -> {
            otrProgressBar.setProgress(percent);
            otrProgressText.setText(percent + "%");
        });

        if (progress >= 1.0f) {
            // OTR generation finished
            generatingOTR = false;
            hideOTRProgress();
            runOnUiThread(() -> {
                romReady = true;
                loadButton.setVisibility(View.GONE);
                tryStartGame();
            });
        } else {
            progressHandler.postDelayed(this::pollOTRProgress, 50);
        }
    }

    void onSurfaceReady() {
        surfaceReady = true;
        Log.i(TAG, "GL surface ready");
        tryStartGame();
    }

    private void tryStartGame() {
        if (!surfaceReady || !romReady || gameInitialized) return;

        Log.i(TAG, "Initializing game");

        NativeBridge.initGame(glSurfaceView.getHolder().getSurface());
        NativeBridge.initTexture();

        gameInitialized = true;

        NativeBridge.startGameLoop();
        gameRunning = true;
        Log.i(TAG, "Game running");
    }

    private void showMenu() {
        menuOverlay.setVisibility(View.VISIBLE);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_WHEN_DIRTY);
    }

    private void hideMenu() {
        menuOverlay.setVisibility(View.GONE);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
    }

    @Override
    public void onBackPressed() {
        if (menuOverlay.getVisibility() == View.VISIBLE) {
            hideMenu();
        } else {
            showMenu();
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        // Detect top-left swipe down for menu
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) { // top-left corner
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) { // swipe down threshold
                        showMenu();
                        return true;
                    }
                }
                break;
        }
        return super.onTouchEvent(event);
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();

        if (gameRunning) {
            NativeBridge.stopGameLoop();
            NativeBridge.cleanupGame();
            gameRunning = false;
            gameInitialized = false;
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        progressThread.quitSafely();
    }

    static {
        System.loadLibrary("wrapper");
    }
}