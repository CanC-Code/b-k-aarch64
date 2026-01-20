// File: Android/app/src/main/java/com/bkawrapper/MenuController.java
package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;
import androidx.activity.OnBackPressedCallback;

public class MenuController {

    private final Activity activity;

    public MenuController(Activity activity) {
        this.activity = activity;
        NativeBridge.nativeInitMenu(activity);
    }

    public void onBackPressed() {
        NativeMenu.nativeToggleMenu();
    }

    public boolean onTouchEvent(MotionEvent event) {
        // optional swipe detection
        return false;
    }

    public static void attach(Activity activity, MenuController menuController) {
        activity.getOnBackPressedDispatcher().addCallback(activity,
                new OnBackPressedCallback(true) {
                    @Override
                    public void handleOnBackPressed() {
                        menuController.onBackPressed();
                    }
                });

        View root = activity.getWindow().getDecorView();
        root.setOnTouchListener((v, event) -> menuController.onTouchEvent(event));
    }
}