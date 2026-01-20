// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.os.Bundle;
import androidx.activity.ComponentActivity;

public class MainActivity extends ComponentActivity {

    private MenuController menuController;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize menu controller and native menu
        menuController = new MenuController();
        menuController.initMenu(this);
    }

    @Override
    public void onBackPressed() {
        if (!menuController.onBackPressed()) {
            super.onBackPressed();
        }
    }

    // Optional callback from renderer if needed
    public void onSurfaceReady() {
        // no-op for now
    }
}