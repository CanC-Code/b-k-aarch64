// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.app.Activity;
import android.os.Bundle;
import android.opengl.GLSurfaceView;

public class MainActivity extends Activity {

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private MenuController menuController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Setup GLSurfaceView
        glSurfaceView = new GLSurfaceView(this);
        glSurfaceView.setEGLContextClientVersion(2);
        glRenderer = new GLRenderer(this);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        setContentView(glSurfaceView);

        // Menu
        menuController = new MenuController(this);
        MenuController.attach(this, menuController);

        // Start emulator loop
        NativeBridge.startGameLoop();
    }

    @Override
    public void onBackPressed() {
        if (menuController != null) {
            menuController.toggle();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        glSurfaceView.onPause();
        NativeBridge.pauseGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        glSurfaceView.onResume();
        NativeBridge.resumeGameLoop();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        NativeBridge.cleanupGame();
    }
}