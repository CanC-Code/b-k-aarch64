package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.util.Log;
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

    private static final String TAG = "BK_MAIN";

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private ActivityResultLauncher<String[]> romPickerLauncher;

    private Button loadButton;
    private LinearLayout menuOverlay;
    private LinearLayout progressOverlay;
    private ProgressBar otrProgressBar;
    private TextView otrProgressText;

    private boolean romReady = false;
    private boolean gameInitialized = false;
    private boolean gameRunning = false;

    private HandlerThread progressThread;
    private Handler progressHandler;
    private boolean generatingOTR = false;

    private Menu menu;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        bindViews();
        setupGL();
        setupRomPicker();
        setupMenuButtons();
        setupOTRProgressThread();

        menu = new Menu(this);

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
                uri -> loadRom(uri)
        );

        loadButton.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );
    }

    private void setupMenuButtons() {
        findViewById(R.id.button_resume).setOnClickListener(v -> menu.toggleMenu());
        findViewById(R.id.button_exit).setOnClickListener(v -> finish());
        findViewById(R.id.button_settings).setOnClickListener(v ->
                Log.i(TAG, "Settings clicked (stub)")
        );
        findViewById(R.id.button_controller).setOnClickListener(v ->
                Log.i(TAG, "Controller layout clicked (stub)")
        );
    }

    private void setupOTRProgressThread() {
        progressThread = new HandlerThread("OTRProgressThread");
        progressThread.start();
        progressHandler = new Handler(progressThread.getLooper());
    }

    /* =======================
       ROM + OTR FLOW
       ======================= */
    private void loadRom(Uri uri) {
        try {
            Log.i(TAG, "Loading ROM");
            NativeBridge.loadRomFromUri(getContentResolver(), uri);

            showOTRProgress();

            generatingOTR = true;
            progressHandler.post(this::pollOTRProgress);
        } catch (Exception e) {
            Log.e(TAG, "ROM load failed", e);
        }
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

    private void showOTRProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.VISIBLE));
    }

    private void hideOTRProgress() {
        runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));
    }

    /* =======================
       GAME BOOT
       ======================= */
    public void onSurfaceReady() {
        NativeBridge.initTexture();

        gameInitialized = true;
        NativeBridge.startGameLoop();
        gameRunning = true;

        Log.i(TAG, "Game running");
    }

    /* =======================
       BACK BUTTON / MENU
       ======================= */
    @Override
    public void onBackPressed() {
        if (!romReady) {
            super.onBackPressed();
            return;
        }
        menu.toggleMenu();
    }

    /* =======================
       LIFECYCLE
       ======================= */
    @Override
    protected void onPause() {
        super.onPause();
        if (gameRunning) {
            NativeBridge.stopGameLoop();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (gameInitialized && !gameRunning) {
            NativeBridge.startGameLoop();
        }
    }
}