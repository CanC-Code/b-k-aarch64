package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.widget.Button;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BK_APP";

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private ActivityResultLauncher<String[]> romPickerLauncher;

    private boolean surfaceReady = false;
    private boolean romReady = false;
    private boolean gameRunning = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button loadBtn = findViewById(R.id.button_load_game);
        glSurfaceView = findViewById(R.id.surface_gl);

        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

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
    }

    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);
            romReady = true;
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
        if (!surfaceReady || !romReady || gameRunning) return;

        Log.i(TAG, "Initializing native core");

        NativeBridge.initGame(glSurfaceView.getHolder().getSurface());

        int texId = NativeBridge.initTexture();
        glRenderer.attachTexture(texId);

        NativeBridge.startGameLoop();
        gameRunning = true;

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
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
    }

    static {
        System.loadLibrary("wrapper");
    }
}