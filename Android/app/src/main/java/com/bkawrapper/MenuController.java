package com.bkawrapper;

import android.os.Bundle;
import android.view.KeyEvent;
import androidx.activity.ComponentActivity;
import androidx.activity.OnBackPressedCallback;

public class MenuController {

    private final ComponentActivity activity;

    public MenuController(ComponentActivity activity) {
        this.activity = activity;
        setupBackHandler();
    }

    private void setupBackHandler() {
        activity.getOnBackPressedDispatcher().addCallback(activity, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                boolean handled = NativeBridge.nativeOnBackPressed();
                if (!handled) {
                    setEnabled(false);
                    activity.onBackPressed();
                    setEnabled(true);
                }
            }
        });
    }

    public void initMenu() {
        NativeBridge.nativeInitMenu();
    }
}