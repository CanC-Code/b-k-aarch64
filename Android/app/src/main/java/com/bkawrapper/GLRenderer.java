package com.bkawrapper;

import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import javax.microedition.khronos.opengles.GL10;

public class GLRenderer implements GLSurfaceView.Renderer {

    private int textureId;

    @Override
    public void onSurfaceCreated(GL10 gl, javax.microedition.khronos.egl.EGLConfig config) {
        // setup texture
        textureId = createTexture();
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        NativeBridge.updateTexture(textureId);
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
    }

    private int createTexture() {
        int[] textures = new int[1];
        GLES20.glGenTextures(1, textures, 0);
        return textures[0];
    }
}