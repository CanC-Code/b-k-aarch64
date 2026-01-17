// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.view.Surface;
import android.widget.Button;
import android.util.Log;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

public class MainActivity extends AppCompatActivity {

    private ActivityResultLauncher<String[]> romPickerLauncher;
    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private boolean surfaceReady = false;
    private boolean romLoaded = false;
    private boolean gameStarted = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button loadGameBtn = findViewById(R.id.button_load_game);
        glSurfaceView = findViewById(R.id.surface_gl);

        // Setup OpenGL ES 2.0
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this::onSurfaceReady);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // SAF launcher for ROM selection
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) handleRomUri(uri);
                }
        );

        loadGameBtn.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"application/octet-stream"})
        );
    }

    private void handleRomUri(Uri uri) {
        NativeBridge.loadRomFromUri(getContentResolver(), uri);
        romLoaded = true;
        Log.i("BK_APP", "ROM loaded via SAF");

        // Start game loop if surface is ready
        startGameIfReady();
    }

    private void onSurfaceReady() {
        if (surfaceReady) return;
        surfaceReady = true;
        Log.i("BK_APP", "GL surface ready, initializing game");
        NativeBridge.initGame(glSurfaceView.getHolder().getSurface());

        // Start game loop if ROM is already loaded
        startGameIfReady();
    }

    private void startGameIfReady() {
        if (surfaceReady && romLoaded && !gameStarted) {
            NativeBridge.startGameLoop();
            gameStarted = true;
            Log.i("BK_APP", "Game loop started");
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();

        Log.i("BK_APP", "Stopping game loop onPause");
        NativeBridge.stopGameLoop();
        NativeBridge.cleanupGame();
        gameStarted = false;
    }

    static {
        System.loadLibrary("wrapper"); // Match your CMake add_library
    }
}