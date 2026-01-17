package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BK_APP";

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private ActivityResultLauncher<String[]> romPickerLauncher;

    private Button loadButton;
    private LinearLayout menuOverlay;

    // OTR generation UI
    private LinearLayout progressLayout;
    private ProgressBar progressBar;
    private TextView progressText;

    // Launch gates
    private boolean surfaceReady = false;
    private boolean romReady = false;
    private boolean gameInitialized = false;
    private boolean gameRunning = false;

    // Swipe gesture tracking for menu
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.surface_gl);
        loadButton = findViewById(R.id.button_load_game);
        menuOverlay = findViewById(R.id.menu_overlay);

        progressLayout = findViewById(R.id.progress_layout);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

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
    }

    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM...");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);
            romReady = true;

            // Hide load button once ROM is loaded
            loadButton.setVisibility(View.GONE);

            // Start OTR generation with progress
            startOTRGeneration();
        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
        }
    }

    private void startOTRGeneration() {
        progressLayout.setVisibility(View.VISIBLE);
        progressBar.setProgress(0);
        progressText.setText("Generating OTR...");

        new Thread(() -> {
            // Call native to build OTR
            NativeBridge.processRom(); // or call separate generateOTR if you implement

            // Poll progress
            int progress = 0;
            while (progress < 100) {
                progress = NativeBridge.getOTRProgress(); // stub for native
                int finalProgress = progress;
                mainHandler.post(() -> {
                    progressBar.setProgress(finalProgress);
                    progressText.setText("Generating OTR: " + finalProgress + "%");
                });

                try { Thread.sleep(100); } catch (InterruptedException ignored) {}
            }

            mainHandler.post(() -> {
                progressLayout.setVisibility(View.GONE);
                Log.i(TAG, "OTR generation complete, size: " + NativeBridge.getOTRData().length);
                tryStartGame();
            });
        }).start();
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

    static {
        System.loadLibrary("wrapper");
    }
}