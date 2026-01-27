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

public class MainActivity extends AppCompatActivity {
    private GLSurfaceView glSurfaceView;
    private MenuController menuController;
    private boolean isGameStarted = false;
    
    private View otrUiContainer;
    private ProgressBar progressBar;
    private TextView progressText;

    private final ActivityResultLauncher<Intent> filePickerLauncher =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri uri = result.getData().getData();
                if (uri != null) {
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    
                    // Show Progress UI
                    otrUiContainer.setVisibility(View.VISIBLE);

                    // Run in background so UI doesn't freeze (Black Screen)
                    new Thread(() -> {
                        NativeBridge.loadRomFromUri(getContentResolver(), uri);

                        runOnUiThread(() -> {
                            otrUiContainer.setVisibility(View.GONE);
                            if (!isGameStarted) {
                                NativeBridge.startGameLoop();
                                isGameStarted = true;
                                if (menuController != null) menuController.hide();
                            }
                        });
                    }).start();
                }
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface_view);
        otrUiContainer = findViewById(R.id.otr_ui_container);
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);

        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(new GLRenderer(this));
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        menuController = new MenuController(this);
        NativeBridge.nativeInit(this); 
    }

    // Called by wrapper.cpp via JNI during extract_assets_to_otr
    public void updateOtrProgress(int percent, String fileName) {
        runOnUiThread(() -> {
            if (progressBar != null) progressBar.setProgress(percent);
            if (progressText != null) progressText.setText("Extracting: " + fileName);
        });
    }

    public void openFilePicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        filePickerLauncher.launch(intent);
    }
}
