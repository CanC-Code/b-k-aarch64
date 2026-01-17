// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

import android.opengl.GLSurfaceView;
import android.opengl.GLES20;

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

        loadGameBtn.setOnClickListener(v -> romPickerLauncher.launch(new String[]{"application/octet-stream"}));
    }

    private void handleRomUri(Uri uri) {
        // Load ROM and automatically generate BK.OTR
        NativeBridge.loadRomFromUri(getContentResolver(), uri);

        // Initialize game and start native game loop
        NativeBridge.startGame(glSurfaceView.getHolder().getSurface());

        // Initialize OpenGL texture in native side
        glRenderer.initTexture();
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
        NativeBridge.stopGame(); // Stop loop + cleanup resources
    }

    static {
        System.loadLibrary("bka_wrapper"); // Load JNI wrapper
    }

    // ---- OpenGL Renderer ----
    private class GLRenderer implements GLSurfaceView.Renderer {

        private int texId = 0;

        @Override
        public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 gl, javax.microedition.khronos.egl.EGLConfig config) {
            GLES20.glClearColor(0f, 0f, 0f, 1f);
        }

        @Override
        public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 gl, int width, int height) {
            GLES20.glViewport(0, 0, width, height);
        }

        @Override
        public void onDrawFrame(javax.microedition.khronos.opengles.GL10 gl) {
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

            if (texId != 0) {
                NativeBridge.updateTexture(texId); // Update GPU texture from native framebuffer
            }

            // TODO: render a fullscreen quad using texId
            // (you can use a simple textured quad shader to draw the N64 framebuffer)
        }

        public void initTexture() {
            texId = NativeBridge.initTexture();
        }
    }
}