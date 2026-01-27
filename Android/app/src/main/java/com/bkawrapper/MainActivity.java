package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.opengl.GLSurfaceView;
import android.os.ParcelFileDescriptor;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import java.io.IOException;

public class MainActivity extends AppCompatActivity {
    private GLSurfaceView glSurfaceView;
    private MenuController menuController;
    private boolean isGameStarted = false;

    private View otrUiContainer;
    private View menuOverlay; 
    private ProgressBar progressBar;
    private TextView progressText;
    private TextView artifactText; // Added reference

    private final ActivityResultLauncher<Intent> filePickerLauncher =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri uri = result.getData().getData();
                if (uri != null) {
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);

                    if (menuOverlay != null) menuOverlay.setVisibility(View.GONE);
                    if (otrUiContainer != null) otrUiContainer.setVisibility(View.VISIBLE);

                    new Thread(() -> {
                        try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(uri, "r")) {
                            if (pfd != null) {
                                String outDir = getFilesDir().getAbsolutePath();
                                NativeBridge.runOtrGeneration(
                                    pfd.getFd(), 
                                    this.getAssets(), 
                                    outDir
                                );
                            }
                        } catch (IOException e) {
                            e.printStackTrace();
                        }

                        runOnUiThread(() -> {
                            if (otrUiContainer != null) otrUiContainer.setVisibility(View.GONE);
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
        menuOverlay = findViewById(R.id.menu_overlay);
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);
        artifactText = findViewById(R.id.otr_current_artifact); // Initialize

        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(new GLRenderer(this));
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        menuController = new MenuController(this);

        View selectBtn = findViewById(R.id.btn_select_rom);
        if (selectBtn != null) {
            selectBtn.setOnClickListener(v -> openFilePicker());
        }

        NativeBridge.nativeInit(this); 
    }

    public void updateOtrProgress(int percent, String fileName) {
        runOnUiThread(() -> {
            if (progressBar != null) progressBar.setProgress(percent);
            
            // Show the file being processed currently
            if (artifactText != null) {
                artifactText.setText(fileName);
            }

            // Show the percentage below
            if (progressText != null) {
                progressText.setText("Generating OTR: " + percent + "%");
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
