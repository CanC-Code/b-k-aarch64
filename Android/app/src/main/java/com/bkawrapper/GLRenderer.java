package com.bkawrapper;

import android.content.Context;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.util.Log;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {

    private static final String TAG = "GLRenderer";

    // OTR data buffer in memory
    private ByteBuffer otrBuffer = null;
    private int otrSize = 0;

    private Context context;

    // Simple triangle vertices for demo (replace with your OTR rendering logic)
    private final float[] vertices = {
            0.0f,  0.5f, 0.0f,
           -0.5f, -0.5f, 0.0f,
            0.5f, -0.5f, 0.0f
    };
    private FloatBuffer vertexBuffer;
    private int program;

    public GLRenderer(Context context) {
        this.context = context;
        vertexBuffer = ByteBuffer.allocateDirect(vertices.length * 4)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer();
        vertexBuffer.put(vertices);
        vertexBuffer.position(0);
    }

    // Called when the surface is first created
    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0f, 0f, 0f, 1f);

        // Compile a simple shader program for demo purposes
        String vertexShaderCode =
                "attribute vec4 vPosition;" +
                "void main() {" +
                "  gl_Position = vPosition;" +
                "}";
        String fragmentShaderCode =
                "precision mediump float;" +
                "void main() {" +
                "  gl_FragColor = vec4(1.0, 0.5, 0.0, 1.0);" +
                "}";
        int vertexShader = loadShader(GLES20.GL_VERTEX_SHADER, vertexShaderCode);
        int fragmentShader = loadShader(GLES20.GL_FRAGMENT_SHADER, fragmentShaderCode);

        program = GLES20.glCreateProgram();
        GLES20.glAttachShader(program, vertexShader);
        GLES20.glAttachShader(program, fragmentShader);
        GLES20.glLinkProgram(program);

        Log.i(TAG, "GL program created");
    }

    // Called when the surface changes size
    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
    }

    // Called on every frame
    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

        if (otrBuffer != null && otrSize > 0) {
            // TODO: Pass otrBuffer to your emulator renderer
            // Example: EmulatorRenderer.renderOTR(otrBuffer, otrSize);

            // For demo, draw simple triangle
            GLES20.glUseProgram(program);
            int posHandle = GLES20.glGetAttribLocation(program, "vPosition");
            GLES20.glEnableVertexAttribArray(posHandle);
            GLES20.glVertexAttribPointer(posHandle, 3, GLES20.GL_FLOAT, false, 12, vertexBuffer);
            GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, 3);
            GLES20.glDisableVertexAttribArray(posHandle);
        }
    }

    // Load generated OTR into the renderer
    public void loadOTR(byte[] otrData) {
        if (otrData == null || otrData.length == 0) return;
        otrBuffer = ByteBuffer.allocateDirect(otrData.length)
                .order(ByteOrder.nativeOrder());
        otrBuffer.put(otrData);
        otrBuffer.position(0);
        otrSize = otrData.length;
        Log.i(TAG, "OTR loaded into renderer, size: " + otrSize);
    }

    // Shader helper
    private int loadShader(int type, String code) {
        int shader = GLES20.glCreateShader(type);
        GLES20.glShaderSource(shader, code);
        GLES20.glCompileShader(shader);
        int[] compiled = new int[1];
        GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, compiled, 0);
        if (compiled[0] == 0) {
            Log.e(TAG, "Shader compile failed: " + GLES20.glGetShaderInfoLog(shader));
            GLES20.glDeleteShader(shader);
            shader = 0;
        }
        return shader;
    }
}