package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;
import android.view.MotionEvent;

public class MainActivity extends AppCompatActivity {

    private static final String TAG = "BK_MAIN";

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private ActivityResultLauncher<String[]> romPickerLauncher;

    private Button loadButton;
    private LinearLayout menuOverlay;
    private LinearLayout progressOverlay;
    private OTRProgressBar otrProgressBar;
    private OTRProgressText otrProgressText;

    private boolean romReady = false;
    private boolean gameInitialized = false;
    private boolean gameRunning = false;

    private HandlerThread progressThread;
    private Handler progressHandler;
    private boolean generatingOTR = false;

    // ========================
    // Menu system
    // ========================
    private MenuController menuController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        bindViews();
        setupGL();
        setupRomPicker();
        setupMenuController();
        setupOTRProgressThread();

        Log.i(TAG, "App started – waiting for ROM");
    }

    private void bindViews() {
        glSurfaceView = findViewById(R.id.surface_gl);
        loadButton = findViewById(R.id.button_load_game);
        menuOverlay = findViewById(R.id.menu_overlay);
        progressOverlay = findViewById(R.id.progress_overlay);
        otrProgressBar = findViewById(R.id.otr_progress_bar);
        otrProgressText = findViewById(R.id.otr_progress_text);
    }

    private void setupGL() {
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
    }

    private void setupRomPicker() {
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) loadRom(uri);
                }
        );

        loadButton.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );
    }

    private void setupMenuController() {
        menuController = new MenuController(this, menuOverlay);
    }

    private void setupOTRProgressThread() {
        progressThread = new HandlerThread("OTRProgressThread");
        progressThread.start();
        progressHandler = new Handler(progressThread.getLooper());
    }

    // ========================
    // ROM + OTR FLOW
    // ========================
    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);

            showOTRProgress();
            generatingOTR = true;
            progressHandler.post(this::pollOTRProgress);
        } catch (Exception e) {
            Log.e(TAG, "Failed to load ROM", e);
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
                loadButton.setVisibility(View.GONE);
            });
        } else {
            progressHandler.postDelayed(this::pollOTRProgress, 100);
        }
    }

    // ========================
    // GAME BOOT
    // ========================
    void onSurfaceReady() {
        glSurfaceView.queueEvent(() -> {
            NativeBridge.initTexture();
            gameInitialized = true;
            NativeBridge.startGameLoop();
            gameRunning = true;
            Log.i(TAG, "Game running");
        });
    }

    // ========================
    // MENU CONTROL (FORWARD EVENTS)
    // ========================
    @Override
    public void onBackPressed() {
        if (menuController != null && menuController.onBackPressed()) return;
        super.onBackPressed();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (menuController != null && menuController.onTouchEvent(event)) return true;
        return super.onTouchEvent(event);
    }

    // ========================
    // LIFECYCLE
    // ========================
    @Override
    protected void onPause() {
        super.onPause();
        // Possibly pause GL / emulation
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Possibly resume GL / emulation
    }
}