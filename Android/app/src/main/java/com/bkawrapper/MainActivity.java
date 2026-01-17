// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

public class MainActivity extends AppCompatActivity {

    private ActivityResultLauncher<String[]> romPickerLauncher;
    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button loadGameBtn = findViewById(R.id.button_load_game);
        glSurfaceView = findViewById(R.id.surface_gl);

        glSurfaceView.setEGLContextClientVersion(2); // OpenGL ES 2.0
        glRenderer = new GLRenderer();
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // SAF launcher for ROM
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) {
                        handleRomUri(uri);
                    }
                }
        );

        loadGameBtn.setOnClickListener(v -> {
            romPickerLauncher.launch(new String[]{"application/octet-stream"});
        });
    }

    private void handleRomUri(Uri uri) {
        // Pass URI to native layer to dynamically build .otr / decompile
        NativeBridge.loadRom(getContentResolver(), uri);
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();
    }
    
    static {
        System.loadLibrary("bka_wrapper"); // Native code library
    }
}