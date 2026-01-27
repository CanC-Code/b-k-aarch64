package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.opengl.GLSurfaceView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.view.View;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

public class MainActivity extends AppCompatActivity {
    private GLSurfaceView glSurfaceView;
    private MenuController menuController;
    private boolean isGameStarted = false;
    
    // UI components for OTR Progress
    private ProgressBar progressBar;
    private TextView progressText;
    private View progressContainer;

    private final ActivityResultLauncher<Intent> filePickerLauncher =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri uri = result.getData().getData();
                if (uri != null) {
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    
                    // Show the progress UI
                    if (progressContainer != null) progressContainer.setVisibility(View.VISIBLE);

                    // IMPORTANT: Run extraction in a background thread to prevent black screen freeze
                    new Thread(() -> {
                        NativeBridge.loadRomFromUri(getContentResolver(), uri);

                        // Once extraction is done, start the game on the Main Thread
                        runOnUiThread(() -> {
                            if (progressContainer != null) progressContainer.setVisibility(View.GONE);
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

        // Link UI
        glSurfaceView = findViewById(R.id.gl_surface_view);
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);
        progressContainer = findViewById(R.id.otr_ui_container); // Assuming a wrapper layout

        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(new GLRenderer(this));
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        menuController = new MenuController(this);
        NativeBridge.nativeInit(this); 
    }

    // This method is called by C++ via JNI (ensure the JNI signatures match)
    public void updateOtrProgress(int percent, String fileName) {
        runOnUiThread(() -> {
            if (progressBar != null) progressBar.setProgress(percent);
            if (progressText != null) {
                progressText.setText("Extracting: " + fileName + " (" + percent + "%)");
            }
        });
    }

    public void openFilePicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        filePickerLauncher.launch(intent);
    }

    @Override
    public void onBackPressed() {
        if (menuController != null) menuController.toggle();
        else super.onBackPressed();
    }
}
