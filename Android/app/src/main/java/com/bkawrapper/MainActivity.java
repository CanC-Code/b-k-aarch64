// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.view.Surface;
import android.widget.Button;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

public class MainActivity extends AppCompatActivity {

    private ActivityResultLauncher<String[]> romPickerLauncher;
    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

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

        loadGameBtn.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"application/octet-stream"})
        );
    }

    private void handleRomUri(Uri uri) {
        // Load ROM and generate BK.OTR in memory
        NativeBridge.loadRomFromUri(getContentResolver(), uri);

        // Initialize game with OpenGL surface
        Surface surface = glSurfaceView.getHolder().getSurface();
        NativeBridge.initGame(surface);

        // Initialize GL texture in renderer
        glRenderer.initTexture();

        // Start the native game loop
        NativeBridge.startGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
        NativeBridge.startGameLoop();
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();
        NativeBridge.stopGameLoop();
        NativeBridge.cleanupGame();
    }

    static {
        System.loadLibrary("bka_wrapper"); // Load native JNI wrapper
    }
}