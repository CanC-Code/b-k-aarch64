package com.bkawrapper;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.FrameLayout;

public class MainActivity extends Activity {

    private MenuController menuController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        FrameLayout root = findViewById(R.id.root_container);
        View menuOverlay = getLayoutInflater()
                .inflate(R.layout.menu_overlay, root, false);

        root.addView(menuOverlay);

        menuController = new MenuController(menuOverlay);
    }
    public void onSurfaceReady() {
    // Renderer callback — no-op for now
    }
    @Override
    public void onBackPressed() {
        if (!menuController.onBackPressed()) {
            super.onBackPressed();
        }
    }
}