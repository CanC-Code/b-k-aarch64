package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.opengl.GLSurfaceView;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

public class MainActivity extends AppCompatActivity implements NativeBridge.OtrCompletionListener {
    private GLSurfaceView glSurfaceView;
    private boolean isGameStarted = false;

    private View otrUiContainer;
    private View menuOverlay; 
    private ProgressBar progressBar;
    private TextView progressText;
    private TextView artifactText;

    private final ActivityResultLauncher<Intent> filePickerLauncher =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri uri = result.getData().getData();
                if (uri != null) {
                    // Grant permission to keep the file accessible in the background service
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);

                    if (menuOverlay != null) menuOverlay.setVisibility(View.GONE);
                    if (otrUiContainer != null) otrUiContainer.setVisibility(View.VISIBLE);

                    // Launch the Service to handle the heavy extraction
                    Intent serviceIntent = new Intent(this, OtrService.class);
                    serviceIntent.putExtra("uri", uri.toString());
                    serviceIntent.putExtra("outDir", getFilesDir().getAbsolutePath());
                    startForegroundService(serviceIntent);
                }
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // UI Binding with null-safety
        glSurfaceView = findViewById(R.id.gl_surface_view);
        otrUiContainer = findViewById(R.id.otr_ui_container);
        menuOverlay = findViewById(R.id.menu_overlay);
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);
        artifactText = findViewById(R.id.otr_current_artifact);

        if (glSurfaceView != null) {
            glSurfaceView.setEGLContextClientVersion(2);
            glSurfaceView.setRenderer(new GLRenderer(this));
            glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
        }

        // Register for native callbacks
        NativeBridge.setOtrCompletionListener(this);
        NativeBridge.nativeInit(this); 

        View selectBtn = findViewById(R.id.btn_select_rom);
        if (selectBtn != null) {
            selectBtn.setOnClickListener(v -> openFilePicker());
        }
    }

    @Override
    public void onOtrComplete() {
        runOnUiThread(() -> {
            if (otrUiContainer != null) otrUiContainer.setVisibility(View.GONE);
            if (!isGameStarted) {
                NativeBridge.startGameLoop();
                isGameStarted = true;
            }
        });
    }

    // This method is called by C++ via JNI
    public void updateOtrProgress(int percent, String fileName) {
        runOnUiThread(() -> {
            if (progressBar != null) progressBar.setProgress(percent);
            if (artifactText != null) artifactText.setText(fileName);
            if (progressText != null) progressText.setText("Generating OTR: " + percent + "%");
        });
    }

    public void openFilePicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        filePickerLauncher.launch(intent);
    }
}
