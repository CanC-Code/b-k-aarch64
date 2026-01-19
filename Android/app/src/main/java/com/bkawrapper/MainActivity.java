package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.View;
import android.widget.LinearLayout;
import androidx.appcompat.app.AppCompatActivity;
import android.opengl.GLSurfaceView;

public class MainActivity extends AppCompatActivity {

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private MenuController menuController;
    private LinearLayout menuOverlay;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // GLSurfaceView setup
        glSurfaceView = findViewById(R.id.gl_surface_view);
        glRenderer = new GLRenderer();
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setRenderer(glRenderer);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        // Menu overlay
        menuOverlay = findViewById(R.id.menu_overlay);
        menuController = new MenuController(this, menuOverlay);

        // Attach menu controller to handle back & swipe
        MenuController.attach(this, menuController);

        // Initialize native bridge
        NativeBridge.initTexture();
        NativeBridge.startGameLoop();
    }

    @Override
    protected void onPause() {
        super.onPause();
        NativeBridge.pauseGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        NativeBridge.resumeGameLoop();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        NativeBridge.cleanupGame();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (menuController != null && menuController.onTouchEvent(event)) {
            return true;
        }
        return super.onTouchEvent(event);
    }

    @Override
    public void onBackPressed() {
        if (menuController != null) {
            menuController.onBackPressed();
            return;
        }
        super.onBackPressed();
    }
}