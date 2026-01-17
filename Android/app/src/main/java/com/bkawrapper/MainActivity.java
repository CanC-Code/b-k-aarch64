// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.View;
import android.widget.Button;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BK_APP";

    // OpenGL
    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    // ROM
    private ActivityResultLauncher<String[]> romPickerLauncher;
    private boolean romReady = false;

    // Game state
    private boolean surfaceReady = false;
    private boolean gameInitialized = false;
    private boolean gameRunning = false;

    // Menu overlay
    private View menuOverlay;
    private boolean menuVisible = false;

    // Gesture
    private float gestureStartX = 0;
    private float gestureStartY = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Views
        glSurfaceView = findViewById(R.id.surface_gl);
        menuOverlay = findViewById(R.id.menu_overlay);
        Button loadBtn = findViewById(R.id.button_load_game);

        // OpenGL setup
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // SAF ROM picker
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) loadRom(uri);
                }
        );

        loadBtn.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );

        Log.i(TAG, "App started – waiting for ROM");

        // Menu buttons
        Button btnResume = menuOverlay.findViewById(R.id.button_resume);
        btnResume.setOnClickListener(v -> hideMenu());

        Button btnExit = menuOverlay.findViewById(R.id.button_exit);
        btnExit.setOnClickListener(v -> finish());

        Button btnSettings = menuOverlay.findViewById(R.id.button_settings);
        btnSettings.setOnClickListener(v -> {
            Log.i(TAG, "Settings clicked (stub)");
        });

        Button btnController = menuOverlay.findViewById(R.id.button_controller);
        btnController.setOnClickListener(v -> {
            Log.i(TAG, "Controller Layout clicked (stub)");
        });
    }

    // --------------------
    // ROM / Game
    // --------------------
    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM...");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);
            romReady = true;
            Log.i(TAG, "ROM + OTR ready");
            tryStartGame();
        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
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
        gameRunning = true;

        NativeBridge.startGameLoop();
        Log.i(TAG, "Game running");
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

    // --------------------
    // Menu handling
    // --------------------
    @Override
    public void onBackPressed() {
        if (!menuVisible) {
            showMenu();
        } else {
            hideMenu();
        }
    }

    private void showMenu() {
        menuOverlay.setVisibility(View.VISIBLE);
        menuVisible = true;
    }

    private void hideMenu() {
        menuOverlay.setVisibility(View.GONE);
        menuVisible = false;
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                gestureStartX = event.getX();
                gestureStartY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                float dx = event.getX() - gestureStartX;
                float dy = event.getY() - gestureStartY;

                // Top-left swipe down > 200 px
                if (gestureStartX < 150 && gestureStartY < 150 && dy > 200) {
                    showMenu();
                    return true;
                }
                break;
        }
        return super.onTouchEvent(event);
    }

    static {
        System.loadLibrary("wrapper");
    }
}