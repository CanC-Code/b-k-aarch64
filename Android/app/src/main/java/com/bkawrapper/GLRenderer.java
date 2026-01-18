package com.bkawrapper;

import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.content.Context;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {

    private byte[] otrData;
    private final Object lock = new Object();
    private final Context context;

    public GLRenderer(Context ctx) {
        context = ctx;
    }

    public void setOTRData(byte[] data) {
        synchronized (lock) {
            otrData = data;
        }
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0f,0f,0f,1f);
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0,0,width,height);
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

        synchronized (lock) {
            if (otrData != null) {
                // TODO: decode OTR to texture and render
                // Safe: always on GL thread
            }
        }
    }
}