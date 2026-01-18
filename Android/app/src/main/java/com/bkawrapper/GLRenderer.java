package com.bkawrapper;

import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.FrameLayout;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {

    private final GLSurfaceView glSurfaceView;
    private final ProgressBar progressBar;
    private final TextView progressText;
    private final FrameLayout overlay;

    private byte[] otrData = null;
    private boolean otrInitialized = false;

    public GLRenderer(GLSurfaceView glSurfaceView,
                      ProgressBar progressBar,
                      TextView progressText,
                      FrameLayout overlay) {
        this.glSurfaceView = glSurfaceView;
        this.progressBar = progressBar;
        this.progressText = progressText;
        this.overlay = overlay;
    }

    public void setOTRData(byte[] data) {
        this.otrData = data;
        this.otrInitialized = false;

        if (otrData != null) {
            // Queue texture init on GL thread
            glSurfaceView.queueEvent(() -> {
                NativeBridge.initTextureWithOTR(otrData);
                otrInitialized = true;
            });

            // Hide overlay on UI thread
            overlay.post(() -> overlay.setVisibility(FrameLayout.GONE));
        }
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0f, 0f, 0f, 1f);
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

        if (otrData != null && otrInitialized) {
            NativeBridge.updateTexture(NativeBridge.getTextureId());
        }
    }
}