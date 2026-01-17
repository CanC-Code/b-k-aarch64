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

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private ActivityResultLauncher<String[]> romPickerLauncher;

    private boolean gameStarted = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button loadGameBtn = findViewById(R.id.button_load_game);
        glSurfaceView = findViewById(R.id.surface_gl);

        // -------------------------
        // GL setup
        // -------------------------
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer();
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // -------------------------
        // File picker
        // -------------------------
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                this::onRomSelected
        );

        loadGameBtn.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"application/octet-stream"})
        );
    }

    private void onRomSelected(Uri uri) {
        if (uri == null) return;

        NativeBridge.loadRomFromUri(getContentResolver(), uri);

        Surface surface = glSurfaceView.getHolder().getSurface();
        NativeBridge.initGame(surface);

        NativeBridge.startGameLoop();
        gameStarted = true;
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();

        if (gameStarted) {
            NativeBridge.startGameLoop();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();

        if (gameStarted) {
            NativeBridge.stopGameLoop();
        }

        glSurfaceView.onPause();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        if (gameStarted) {
            NativeBridge.stopGameLoop();
            NativeBridge.cleanupGame();
            gameStarted = false;
        }
    }
}