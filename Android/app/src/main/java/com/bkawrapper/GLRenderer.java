// File: Android/app/src/main/java/com/bkawrapper/GLRenderer.java
package com.bkawrapper;

import android.opengl.GLSurfaceView;
import android.content.Context;

import javax.microedition.khronos.opengles.GL10;
import javax.microedition.khronos.egl.EGLConfig;

public class GLRenderer implements GLSurfaceView.Renderer {

    private final MainActivity activity;

    public GLRenderer(MainActivity activity) {
        this.activity = activity;
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        // Initialize OpenGL state
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        // Update viewport
        gl.glViewport(0, 0, width, height);
    }

    @Override
    public void onDrawFrame(GL10 gl) {
        // Render frame
        gl.glClear(GL10.GL_COLOR_BUFFER_BIT | GL10.GL_DEPTH_BUFFER_BIT);
    }
}