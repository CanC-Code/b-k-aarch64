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

    private final ActivityResultLauncher<Intent> filePickerLauncher =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            if (result.getResultCode() == Activity.RESULT_OK && result.getData() != null) {
                Uri uri = result.getData().getData();
                if (uri != null) {
                    getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    NativeBridge.loadRomFromUri(getContentResolver(), uri);
                }
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Load the XML layout FIRST
        setContentView(R.layout.activity_main);

        // Retrieve the GL view from the inflated layout
        glSurfaceView = findViewById(R.id.gl_surface_view);
        glSurfaceView.setEGLContextClientVersion(2);
        GLRenderer glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // Initialize MenuController WITHOUT calling setContentView again
        menuController = new MenuController(this);
        
        NativeBridge.nativeInit(this);
        NativeBridge.startGameLoop();
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
        NativeBridge.pauseGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (glSurfaceView != null) glSurfaceView.onResume();
        NativeBridge.resumeGameLoop();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        NativeBridge.cleanupGame();
    }
}
