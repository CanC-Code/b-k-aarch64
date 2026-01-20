package com.bkawrapper;

import android.os.Bundle;
import androidx.activity.ComponentActivity;

public class MainActivity extends ComponentActivity {

    private boolean gameRunning = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Initialize core/game
        NativeBridge.nativeInitCore();
        gameRunning = true;

        // Initialize menu
        MenuController menu = new MenuController(this);
        menu.initMenu();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (gameRunning) NativeBridge.pauseGameLoop();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (gameRunning) NativeBridge.resumeGameLoop();
    }
}