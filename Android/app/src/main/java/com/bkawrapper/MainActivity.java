package com.bkawrapper;

import android.os.Bundle;
import android.opengl.GLSurfaceView;

import androidx.appcompat.app.AppCompatActivity;

import com.bkawrapper.menu.MenuController;
import com.bkawrapper.menu.MenuOverlayView;

public class MainActivity extends AppCompatActivity {

    private MenuController menuController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        GLSurfaceView glView = findViewById(R.id.surface_gl);
        glView.setEGLContextClientVersion(2);
        glView.setRenderer(new GLRenderer(this));

        MenuOverlayView menuOverlay =
                findViewById(R.id.menu_overlay);

        menuController = new MenuController(menuOverlay);
        NativeBridge.setMenuController(menuController);
    }

    @Override
    public void onBackPressed() {
        menuController.toggle();
    }
}