package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.opengl.GLSurfaceView;
import androidx.activity.ComponentActivity;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

public class MainActivity extends ComponentActivity {

    private GLSurfaceView glSurfaceView;
    private MenuController menuController;
    private boolean isGameRunning = false;

    private final ActivityResultLauncher<Intent> filePickerLauncher =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri uri = result.getData().getData();
                if (uri != null) {
                    // 1. Grant persistent access
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    // 2. Load the ROM into the native side
                    NativeBridge.loadRomFromUri(getContentResolver(), uri);
                    // 3. Start the game loop ONLY after ROM is selected
                    if (!isGameRunning) {
                        NativeBridge.startGameLoop();
                        isGameRunning = true;
                        if (menuController != null) menuController.hide();
                    }
                }
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Standard layout inflation
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface_view);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(new GLRenderer(this));
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        menuController = new MenuController(this);
        
        // Initialize native context but DO NOT start the game loop yet
        NativeBridge.nativeInit(this); 
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

    @Override
    protected void onPause() {
        super.onPause();
        if (glSurfaceView != null) glSurfaceView.onPause();
        if (isGameRunning) NativeBridge.pauseGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (glSurfaceView != null) glSurfaceView.onResume();
        if (isGameRunning) NativeBridge.resumeGameLoop();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        NativeBridge.cleanupGame();
    }
}
