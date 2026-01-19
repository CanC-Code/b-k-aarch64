package com.bkawrapper;

import android.app.Activity;
import android.content.res.AssetManager;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.opengl.GLSurfaceView;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

    private GLSurfaceView glSurfaceView;
    private Button loadButton;
    private LinearLayout progressOverlay;
    private ProgressBar progressBar;
    private TextView progressText;
    private ExecutorService executor;

    static {
        System.loadLibrary("wrapper");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface);
        loadButton = findViewById(R.id.button_load_game);
        progressOverlay = findViewById(R.id.progress_overlay);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(new GLRenderer(this));

        executor = Executors.newSingleThreadExecutor();

        loadButton.setOnClickListener(v -> loadGame());
    }

    private void loadGame() {
        progressOverlay.setVisibility(View.VISIBLE);
        progressBar.setProgress(0);
        progressText.setText("0%");

        executor.submit(() -> {
            try {
                AssetManager assets = getAssets();
                boolean success = NativeBridge.loadEmbeddedOTRAssets(this, assets, progress -> runOnUiThread(() -> {
                    progressBar.setProgress((int)(progress * 100));
                    progressText.setText((int)(progress * 100) + "%");
                }));

                runOnUiThread(() -> {
                    progressOverlay.setVisibility(View.GONE);
                    if (!success) {
                        progressText.setText("Failed to load OTR");
                    }
                });
            } catch (Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> {
                    progressOverlay.setVisibility(View.GONE);
                    progressText.setText("Error: " + e.getMessage());
                });
            }
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }
}