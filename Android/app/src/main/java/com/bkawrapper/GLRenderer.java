package com.bkawrapper;

import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {

    private final MainActivity activity;

    private int program;
    private int textureId = 0;
    private boolean textureReady = false;

    private FloatBuffer vertexBuffer;
    private FloatBuffer texBuffer;
    private final float[] mvp = new float[16];

    private final float[] verts = {
            -1,  1, 0,
            -1, -1, 0,
             1,  1, 0,
             1, -1, 0
    };

    private final float[] tex = {
            0, 0,
            0, 1,
            1, 0,
            1, 1
    };

    // UI progress overlay references
    private ProgressBar progressBar;
    private TextView progressText;

    public GLRenderer(MainActivity activity) {
        this.activity = activity;
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0, 0, 0, 1);
        Matrix.setIdentityM(mvp, 0);

        vertexBuffer = ByteBuffer.allocateDirect(verts.length * 4)
                .order(ByteOrder.nativeOrder()).asFloatBuffer();
        vertexBuffer.put(verts).position(0);

        texBuffer = ByteBuffer.allocateDirect(tex.length * 4)
                .order(ByteOrder.nativeOrder()).asFloatBuffer();
        texBuffer.put(tex).position(0);

        program = buildProgram();

        // bind progress overlay
        progressBar = activity.findViewById(R.id.otrProgressBar);
        progressText = activity.findViewById(R.id.otrProgressText);

        activity.onSurfaceReady();
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

        // --- update progress overlay ---
        float progress = NativeBridge.getOTRProgress();
        if (progressBar != null && progressText != null) {
            activity.runOnUiThread(() -> {
                progressBar.setProgress((int)(progress * 100));
                progressText.setText((int)(progress * 100) + "%");
            });
        }

        // --- if texture is ready, render ---
        if (textureReady) {
            // Update texture from native
            NativeBridge.updateTexture(textureId);

            GLES20.glUseProgram(program);

            int p = GLES20.glGetAttribLocation(program, "aPos");
            int t = GLES20.glGetAttribLocation(program, "aUV");
            int m = GLES20.glGetUniformLocation(program, "uMVP");
            int s = GLES20.glGetUniformLocation(program, "uTex");

            GLES20.glEnableVertexAttribArray(p);
            GLES20.glVertexAttribPointer(p, 3, GLES20.GL_FLOAT, false, 0, vertexBuffer);

            GLES20.glEnableVertexAttribArray(t);
            GLES20.glVertexAttribPointer(t, 2, GLES20.GL_FLOAT, false, 0, texBuffer);

            GLES20.glUniformMatrix4fv(m, 1, false, mvp, 0);
            GLES20.glUniform1i(s, 0);

            GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);

            GLES20.glDisableVertexAttribArray(p);
            GLES20.glDisableVertexAttribArray(t);
        }
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
    }

    private int buildProgram() {
        String vs =
                "uniform mat4 uMVP;" +
                "attribute vec4 aPos;" +
                "attribute vec2 aUV;" +
                "varying vec2 vUV;" +
                "void main(){gl_Position=uMVP*aPos;vUV=aUV;}";

        String fs =
                "precision mediump float;" +
                "uniform sampler2D uTex;" +
                "varying vec2 vUV;" +
                "void main(){gl_FragColor=texture2D(uTex,vUV);}";

        int v = compile(GLES20.GL_VERTEX_SHADER, vs);
        int f = compile(GLES20.GL_FRAGMENT_SHADER, fs);

        int p = GLES20.glCreateProgram();
        GLES20.glAttachShader(p, v);
        GLES20.glAttachShader(p, f);
        GLES20.glLinkProgram(p);
        return p;
    }

    private int compile(int type, String src) {
        int s = GLES20.glCreateShader(type);
        GLES20.glShaderSource(s, src);
        GLES20.glCompileShader(s);
        return s;
    }

    /** Attach a texture ID from native core */
    public void attachTexture(int texId) {
        this.textureId = texId;
        this.textureReady = texId != 0;
    }

    /**
     * Upload OTR bytes to native core and attach resulting GPU texture.
     * Called after OTR generation is complete.
     */
    public void setOTRData(byte[] otrData) {
        if (otrData == null || otrData.length == 0) return;

        NativeBridge.initTextureWithOTR(otrData);
        int texId = NativeBridge.getTextureId();
        attachTexture(texId);

        // Hide progress overlay
        activity.runOnUiThread(() -> {
            View overlay = activity.findViewById(R.id.progressOverlay);
            if (overlay != null) overlay.setVisibility(View.GONE);
        });
    }
}