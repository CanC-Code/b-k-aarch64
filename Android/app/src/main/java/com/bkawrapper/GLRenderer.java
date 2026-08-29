// File: Android/app/src/main/java/com/bkawrapper/GLRenderer.java
package com.bkawrapper;

import android.content.Context;
import android.content.res.AssetManager;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/**
 * GLRenderer
 *
 * Drives the N64 framebuffer → Android display pipeline.
 */
public class GLRenderer implements GLSurfaceView.Renderer {

    private static final String TAG = "BKA-GLRenderer";

    private final Context context;
    private final String assetDir;
    private final AssetManager mgr;

    private static boolean engineBooted = false;
    private boolean isSurfaceReady = false;

    // GL resources
    private int mTextureId = 0;
    private int mProgram = 0;
    private FloatBuffer mQuadVertices;
    private FloatBuffer mQuadTexCoords;

    // Simple vertex shader
    private static final String VERTEX_SHADER =
        "attribute vec4 aPosition;\n" +
        "attribute vec2 aTexCoord;\n" +
        "varying vec2 vTexCoord;\n" +
        "void main() {\n" +
        "  gl_Position = aPosition;\n" +
        "  vTexCoord = aTexCoord;\n" +
        "}";

    // Simple fragment shader that samples the texture
    private static final String FRAGMENT_SHADER =
        "precision mediump float;\n" +
        "varying vec2 vTexCoord;\n" +
        "uniform sampler2D uTexture;\n" +
        "void main() {\n" +
        "  gl_FragColor = texture2D(uTexture, vTexCoord);\n" +
        "}";

    // Full-screen quad vertices (two triangles)
    private static final float[] QUAD_VERTICES = {
        -1.0f, -1.0f, 0.0f,
         1.0f, -1.0f, 0.0f,
        -1.0f,  1.0f, 0.0f,
         1.0f,  1.0f, 0.0f
    };

    // Texture coordinates matching the vertices
    private static final float[] QUAD_TEXCOORDS = {
        0.0f, 1.0f,
        1.0f, 1.0f,
        0.0f, 0.0f,
        1.0f, 0.0f
    };

    public GLRenderer(Context context, String assetDir, AssetManager mgr) {
        this.context = context;
        this.assetDir = assetDir;
        this.mgr = mgr;

        // Prepare vertex buffers
        ByteBuffer vbb = ByteBuffer.allocateDirect(QUAD_VERTICES.length * 4);
        vbb.order(ByteOrder.nativeOrder());
        mQuadVertices = vbb.asFloatBuffer();
        mQuadVertices.put(QUAD_VERTICES);
        mQuadVertices.position(0);

        ByteBuffer tbb = ByteBuffer.allocateDirect(QUAD_TEXCOORDS.length * 4);
        tbb.order(ByteOrder.nativeOrder());
        mQuadTexCoords = tbb.asFloatBuffer();
        mQuadTexCoords.put(QUAD_TEXCOORDS);
        mQuadTexCoords.position(0);
    }

    private int loadShader(int type, String shaderCode) {
        int shader = GLES20.glCreateShader(type);
        GLES20.glShaderSource(shader, shaderCode);
        GLES20.glCompileShader(shader);
        int[] compiled = new int[1];
        GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, compiled, 0);
        if (compiled[0] == 0) {
            Log.e(TAG, "Shader compile error: " + GLES20.glGetShaderInfoLog(shader));
            GLES20.glDeleteShader(shader);
            return 0;
        }
        return shader;
    }

    private void setupGraphics() {
        // Create shader program
        int vertexShader = loadShader(GLES20.GL_VERTEX_SHADER, VERTEX_SHADER);
        int fragmentShader = loadShader(GLES20.GL_FRAGMENT_SHADER, FRAGMENT_SHADER);
        if (vertexShader == 0 || fragmentShader == 0) return;

        mProgram = GLES20.glCreateProgram();
        GLES20.glAttachShader(mProgram, vertexShader);
        GLES20.glAttachShader(mProgram, fragmentShader);
        GLES20.glLinkProgram(mProgram);

        // Create texture
        int[] textures = new int[1];
        GLES20.glGenTextures(1, textures, 0);
        mTextureId = textures[0];
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, mTextureId);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);
        // Initialize with a magenta placeholder so we can see if texture upload works
        ByteBuffer placeholder = ByteBuffer.allocateDirect(4 * 4 * 4); // 4x4 RGBA
        placeholder.order(ByteOrder.nativeOrder());
        for (int i = 0; i < 16; i++) {
            placeholder.put((byte)0xFF); // R
            placeholder.put((byte)0x00); // G
            placeholder.put((byte)0xFF); // B
            placeholder.put((byte)0xFF); // A
        }
        placeholder.position(0);
        GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_RGBA, 4, 4, 0,
                GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, placeholder);
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        Log.i(TAG, "onSurfaceCreated: GL context ready");
        GLES20.glClearColor(0f, 0f, 0f, 1f);
        setupGraphics();
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        Log.i(TAG, "onSurfaceChanged: " + width + "×" + height);
        GLES20.glViewport(0, 0, width, height);

        // Tell the native side the GL context is alive and provide ACTUAL dimensions
        NativeBridge.surfaceReady(width, height);
        isSurfaceReady = true;

        // Protected by the static flag so it only runs once per app process.
        if (!engineBooted) {
            engineBooted = true;
            Log.i(TAG, "Game thread starting — assetDir=" + assetDir);

            // CRITICAL FIX: Removed the unnecessary Java Thread wrapper.
            // nativeGameBoot safely spawns its own detached C++ pthread, so calling
            // it here is perfectly non-blocking and prevents transient thread GC crashes.
            NativeBridge.nativeGameBoot(assetDir, mgr);
        }
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        // TEMP: no-op to isolate RSP worker and avoid libgui crashes
        return;
    }
}