package com.bkawrapper;

import android.os.Bundle;
import android.view.View;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private MenuController menuController;
    private View menuOverlay;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        menuOverlay = findViewById(R.id.menu_overlay);

        menuController = new MenuController(this, menuOverlay);

        // Initialize emulator as before
        initEmulator();
    }

    private void initEmulator() {
        // existing GLSurfaceView / game loop setup
    }
}