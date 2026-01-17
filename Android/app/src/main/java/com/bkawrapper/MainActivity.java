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

        loadGameBtn.setOnClickListener(v -> {
            romPickerLauncher.launch(new String[]{"application/octet-stream"});
        });
    }

    private void handleRomUri(Uri uri) {
        // Load ROM and automatically generate in-memory BK.OTR
        NativeBridge.loadRomFromUri(getContentResolver(), uri);

        // Initialize game with OpenGL surface
        NativeBridge.initGame(glSurfaceView.getHolder().getSurface());

        // Initialize GL texture in renderer
        glRenderer.initTexture();

        // Start the native game loop automatically
        NativeBridge.startGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();

        // Resume game loop if a ROM was already loaded
        NativeBridge.startGameLoop();
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();

        // Stop game loop and cleanup resources
        NativeBridge.stopGameLoop();
        NativeBridge.cleanupGame();
    }

    // ---- OpenGL Renderer ----
    private class GLRenderer implements GLSurfaceView.Renderer {

        private int texId = 0;
        private int program = 0;
        private int positionHandle = 0;
        private int texCoordHandle = 0;
        private int texUniformHandle = 0;

        // Fullscreen quad (X,Y) and texture coords (U,V)
        private final float[] quadVertices = {
                -1f,  1f,  0f, 0f, // top-left
                -1f, -1f,  0f, 1f, // bottom-left
                 1f, -1f,  1f, 1f, // bottom-right
                 1f,  1f,  1f, 0f  // top-right
        };

        private java.nio.FloatBuffer vertexBuffer;

        @Override
        public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 gl,
                                     javax.microedition.khronos.egl.EGLConfig config) {
            GLES20.glClearColor(0f, 0f, 0f, 1f);

            // Upload vertex data
            java.nio.ByteBuffer bb = java.nio.ByteBuffer.allocateDirect(quadVertices.length * 4);
            bb.order(java.nio.ByteOrder.nativeOrder());
            vertexBuffer = bb.asFloatBuffer();
            vertexBuffer.put(quadVertices);
            vertexBuffer.position(0);

            // Compile shader program
            String vertexShaderCode =
                    "attribute vec2 aPos;" +
                    "attribute vec2 aTex;" +
                    "varying vec2 vTex;" +
                    "void main() {" +
                    "  gl_Position = vec4(aPos, 0.0, 1.0);" +
                    "  vTex = aTex;" +
                    "}";

            String fragmentShaderCode =
                    "precision mediump float;" +
                    "varying vec2 vTex;" +
                    "uniform sampler2D uTexture;" +
                    "void main() {" +
                    "  gl_FragColor = texture2D(uTexture, vTex);" +
                    "}";

            int vs = loadShader(GLES20.GL_VERTEX_SHADER, vertexShaderCode);
            int fs = loadShader(GLES20.GL_FRAGMENT_SHADER, fragmentShaderCode);
            program = GLES20.glCreateProgram();
            GLES20.glAttachShader(program, vs);
            GLES20.glAttachShader(program, fs);
            GLES20.glLinkProgram(program);

            // Get attribute/uniform locations
            positionHandle = GLES20.glGetAttribLocation(program, "aPos");
            texCoordHandle = GLES20.glGetAttribLocation(program, "aTex");
            texUniformHandle = GLES20.glGetUniformLocation(program, "uTexture");
        }

        @Override
        public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 gl, int width, int height) {
            GLES20.glViewport(0, 0, width, height);
        }

        @Override
        public void onDrawFrame(javax.microedition.khronos.opengles.GL10 gl) {
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

            if (texId == 0) return;

            NativeBridge.updateTexture(texId);

            GLES20.glUseProgram(program);

            vertexBuffer.position(0);
            GLES20.glVertexAttribPointer(positionHandle, 2, GLES20.GL_FLOAT, false, 4 * 4, vertexBuffer);
            GLES20.glEnableVertexAttribArray(positionHandle);

            vertexBuffer.position(2);
            GLES20.glVertexAttribPointer(texCoordHandle, 2, GLES20.GL_FLOAT, false, 4 * 4, vertexBuffer);
            GLES20.glEnableVertexAttribArray(texCoordHandle);

            GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, texId);
            GLES20.glUniform1i(texUniformHandle, 0);

            GLES20.glDrawArrays(GLES20.GL_TRIANGLE_FAN, 0, 4);
        }

        public void initTexture() {
            texId = NativeBridge.initTexture();
        }

        private int loadShader(int type, String shaderCode) {
            int shader = GLES20.glCreateShader(type);
            GLES20.glShaderSource(shader, shaderCode);
            GLES20.glCompileShader(shader);
            int[] compiled = new int[1];
            GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, compiled, 0);
            if (compiled[0] == 0) {
                String log = GLES20.glGetShaderInfoLog(shader);
                GLES20.glDeleteShader(shader);
                throw new RuntimeException("Shader compile failed: " + log);
            }
            return shader;
        }
    }

    static {
        System.loadLibrary("bka_wrapper"); // Load JNI wrapper with OTR and GPU framebuffer
    }
}