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

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    private ActivityResultLauncher<String[]> romPickerLauncher;
    private Button loadButton;
    private LinearLayout menuOverlay;
    private LinearLayout progressOverlay;
    private ProgressBar otrProgressBar;
    private TextView otrProgressText;

    private boolean romReady = false;
    private boolean surfaceReady = false;
    private boolean generatingOTR = false;

    private HandlerThread progressThread;
    private Handler progressHandler;

    private MenuController menuController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        menuOverlay = findViewById(R.id.menu_overlay);
        menuController = new MenuController(this, menuOverlay);

        glSurfaceView = findViewById(R.id.surface_gl);
        loadButton = findViewById(R.id.button_load_game);
        progressOverlay = findViewById(R.id.progress_overlay);
        otrProgressBar = findViewById(R.id.otr_progress_bar);
        otrProgressText = findViewById(R.id.otr_progress_text);

        setupGL();
        setupRomPicker();
        setupOTRProgressThread();

        Log.i("MAIN_ACTIVITY", "App started – waiting for ROM");
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
                this::loadRom
        );
        loadButton.setOnClickListener(v ->
                romPickerLauncher.launch(new String[]{"*/*"})
        );
    }

    private void setupOTRProgressThread() {
        progressThread = new HandlerThread("OTRProgressThread");
        progressThread.start();
        progressHandler = new Handler(progressThread.getLooper());
    }

    private void loadRom(Uri uri) {
        NativeBridge.loadRomFromUri(getContentResolver(), uri);
        showOTRProgress();
        generatingOTR = true;
        progressHandler.post(this::pollOTRProgress);
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

    void onSurfaceReady() {
        surfaceReady = true;
        NativeBridge.initTexture();
        NativeBridge.startGameLoop();
    }

    @Override
    public void onBackPressed() {
        if (menuController != null && menuController.onBackPressed()) return;
        super.onBackPressed();
    }

    @Override
    public boolean onTouchEvent(android.view.MotionEvent event) {
        if (menuController != null && menuController.onTouchEvent(event)) return true;
        return super.onTouchEvent(event);
    }
}