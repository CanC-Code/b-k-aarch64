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

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button loadGameBtn = findViewById(R.id.button_load_game);
        glSurfaceView = findViewById(R.id.surface_gl);

        // Setup OpenGL ES 2.0
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer();
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // SAF launcher for ROM selection
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) handleRomUri(uri);
                }
        );

        loadGameBtn.setOnClickListener(v -> romPickerLauncher.launch(new String[]{"application/octet-stream"}));
    }

    private void handleRomUri(Uri uri) {
        // Load ROM safely
        NativeBridge.loadRomFromUri(getContentResolver(), uri);

        Log.i("BK_APP", "ROM loaded via SAF");
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();

        if (surfaceReady) {
            Log.i("BK_APP", "Starting game loop onResume");
            NativeBridge.startGameLoop();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();

        Log.i("BK_APP", "Stopping game loop onPause");
        NativeBridge.stopGameLoop();
        NativeBridge.cleanupGame();
    }

    // Called from GLRenderer when surface is created
    void onSurfaceReady() {
        surfaceReady = true;
        Log.i("BK_APP", "GL surface ready, initializing game");
        NativeBridge.initGame(glSurfaceView.getHolder().getSurface());
    }

    static {
        System.loadLibrary("wrapper"); // Match your CMake add_library
    }
}