package com.bkawrapper;

import android.content.res.AssetManager;
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

    private boolean surfaceReady = false;
    private boolean romReady = false;
    private boolean gameInitialized = false;
    private boolean gameRunning = false;

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

        // AssetManager setup for native OTR loading
        AssetManager assetManager = getAssets();
        NativeBridge.setAssetManager(assetManager);

        // ROM picker
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) {
                        loadRom(uri);
                    }
                }
        );

        loadButton.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );

        // Menu buttons
        menuOverlay.findViewById(R.id.button_resume).setOnClickListener(v -> hideMenu());
        menuOverlay.findViewById(R.id.button_exit).setOnClickListener(v -> finish());
        menuOverlay.findViewById(R.id.button_settings).setOnClickListener(v ->
                Log.i(TAG, "Settings clicked (stub)")
        );
        menuOverlay.findViewById(R.id.button_controller).setOnClickListener(v ->
                Log.i(TAG, "Controller Layout clicked (stub)")
        );

        Log.i(TAG, "App started – waiting for ROM");

        // Progress polling thread
        progressThread = new HandlerThread("OTRProgressThread");
        progressThread.start();
        progressHandler = new Handler(progressThread.getLooper());
    }

    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Reading ROM");

            // Ensure AssetManager is ready; native layer handles bytes
            if (getContentResolver().openInputStream(uri) == null) {
                Log.e(TAG, "ROM stream is null");
                return;
            }

            showOTRProgress();
            generatingOTR = true;
            progressHandler.post(this::pollOTRProgress);

            // Kick off native OTR generation
            NativeBridge.processRom();

        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
        }
    }

    private void showOTRProgress() {
        runOnUiThread(() -> {
            progressOverlay.setVisibility(View.VISIBLE);
            loadButton.setVisibility(View.GONE);
        });
    }

    private void hideOTRProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));
    }

    private void pollOTRProgress() {
        if (!generatingOTR) return;

        float progress = NativeBridge.getOTRProgress();
        int percent = Math.min(100, Math.max(0, (int) (progress * 100)));

        runOnUiThread(() -> {
            otrProgressBar.setProgress(percent);
            otrProgressText.setText(percent + "%");
        });

        if (progress >= 1.0f) {
            generatingOTR = false;
            hideOTRProgress();

            runOnUiThread(() -> {
                romReady = true;

                // Retrieve generated OTR and upload to GPU
                byte[] otrBytes = NativeBridge.getOTR();
                if (otrBytes != null && otrBytes.length > 0) {
                    NativeBridge.initTextureWithOTR(otrBytes);           // Upload texture to native
                    int texId = NativeBridge.getTextureId();           // Get GPU texture ID
                    glRenderer.attachTexture(texId);                   // Attach to renderer
                    tryStartGame();
                } else {
                    Log.e(TAG, "OTR is empty after generation");
                }
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
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) {
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) {
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