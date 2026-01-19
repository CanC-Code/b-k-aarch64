package com.bkawrapper;

import android.content.Context;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.GLUtils;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {

    private final Context context;

    // Vertex coordinates for a full-screen quad
    private final float[] vertexData = {
            -1f,  1f,
            -1f, -1f,
             1f,  1f,
             1f, -1f
    };

    private final float[] texCoordData = {
            0f, 0f,
            0f, 1f,
            1f, 0f,
            1f, 1f
    };

    private FloatBuffer vertexBuffer;
    private FloatBuffer texCoordBuffer;

    private int program;
    private int textureId = -1;
    private byte[] otrData; // latest OTR bytes
    private boolean textureNeedsUpdate = false;

    public GLRenderer(Context ctx) {
        context = ctx;

        vertexBuffer = ByteBuffer.allocateDirect(vertexData.length * 4)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer();
        vertexBuffer.put(vertexData).position(0);

        texCoordBuffer = ByteBuffer.allocateDirect(texCoordData.length * 4)
                .order(ByteOrder.nativeOrder())
                .asFloatBuffer();
        texCoordBuffer.put(texCoordData).position(0);
    }

    // -----------------------------
    // Renderer callbacks
    // -----------------------------
    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0f, 0f, 0f, 1f);
        GLES20.glEnable(GLES20.GL_TEXTURE_2D);

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

        int vertexShader = loadShader(GLES20.GL_VERTEX_SHADER, vertexShaderCode);
        int fragmentShader = loadShader(GLES20.GL_FRAGMENT_SHADER, fragmentShaderCode);

        program = GLES20.glCreateProgram();
        GLES20.glAttachShader(program, vertexShader);
        GLES20.glAttachShader(program, fragmentShader);
        GLES20.glLinkProgram(program);

        GLES20.glUseProgram(program);

        // Create texture
        int[] texIds = new int[1];
        GLES20.glGenTextures(1, texIds, 0);
        textureId = texIds[0];
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, textureId);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

        GLES20.glUseProgram(program);

        int posHandle = GLES20.glGetAttribLocation(program, "aPos");
        int texHandle = GLES20.glGetAttribLocation(program, "aTex");
        int samplerHandle = GLES20.glGetUniformLocation(program, "uTexture");

        GLES20.glEnableVertexAttribArray(posHandle);
        GLES20.glVertexAttribPointer(posHandle, 2, GLES20.GL_FLOAT, false, 0, vertexBuffer);

        GLES20.glEnableVertexAttribArray(texHandle);
        GLES20.glVertexAttribPointer(texHandle, 2, GLES20.GL_FLOAT, false, 0, texCoordBuffer);

        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, textureId);
        GLES20.glUniform1i(samplerHandle, 0);

        if (textureNeedsUpdate && otrData != null) {
            updateTexture();
        }

        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);

        GLES20.glDisableVertexAttribArray(posHandle);
        GLES20.glDisableVertexAttribArray(texHandle);
    }

    // -----------------------------
    // Helpers
    // -----------------------------
    private int loadShader(int type, String code) {
        int shader = GLES20.glCreateShader(type);
        GLES20.glShaderSource(shader, code);
        GLES20.glCompileShader(shader);
        return shader;
    }

    private void updateTexture() {
        // Convert OTR bytes into RGBA bitmap
        // For demonstration: treat bytes as grayscale and expand to RGBA
        int size = (int) Math.sqrt(otrData.length / 4);
        if (size <= 0) return;

        Bitmap bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888);
        int[] pixels = new int[size * size];
        for (int i = 0; i < pixels.length && i * 4 + 3 < otrData.length; i++) {
            int r = otrData[i * 4] & 0xFF;
            int g = otrData[i * 4 + 1] & 0xFF;
            int b = otrData[i * 4 + 2] & 0xFF;
            int a = otrData[i * 4 + 3] & 0xFF;
            pixels[i] = (a << 24) | (r << 16) | (g << 8) | b;
        }
        bmp.setPixels(pixels, 0, size, 0, 0, size, size);

        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, textureId);
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bmp, 0);
        bmp.recycle();

        textureNeedsUpdate = false;
    }

    // Called from MainActivity after OTR bytes are ready
    public void setOTRData(byte[] data) {
        this.otrData = data;
        this.textureNeedsUpdate = true;
    }
}