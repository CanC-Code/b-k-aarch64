// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;

import java.io.InputStream;

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

        // Setup OpenGL ES 2.0
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer();
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // SAF launcher for ROM selection
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
        // Convert ROM from URI into byte[] and pass to native layer
        try {
            ContentResolver resolver = getContentResolver();
            InputStream input = resolver.openInputStream(uri);
            if (input != null) {
                byte[] romBytes = new byte[input.available()];
                int read = input.read(romBytes);
                input.close();
                if (read > 0) {
                    NativeBridge.loadRom(romBytes); // JNI call to load ROM into RAM
                    NativeBridge.processRom();      // Build in-memory BK.OTR
                    NativeBridge.initGame(glSurfaceView.getHolder().getSurface());
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
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
        NativeBridge.cleanupGame(); // Cleanup native resources when paused
    }

    static {
        System.loadLibrary("wrapper"); // Load your JNI wrapper.cpp
    }
}