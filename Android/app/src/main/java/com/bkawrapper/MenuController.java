package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

public class MenuController {

    private final Activity activity;
    private final LinearLayout menuOverlay;

    private float swipeStartX = -1;
    private float swipeStartY = -1;

    public MenuController(Activity activity, LinearLayout menuOverlay) {
        this.activity = activity;
        this.menuOverlay = menuOverlay;

        // init native
        NativeBridge.nativeInitMenu(activity);

        setupButtons();
    }

    private void setupButtons() {
        menuOverlay.findViewById(R.id.button_resume).setOnClickListener(v -> toggleMenu());
        menuOverlay.findViewById(R.id.button_exit).setOnClickListener(v -> activity.finish());
        menuOverlay.findViewById(R.id.button_settings).setOnClickListener(v -> {});
        menuOverlay.findViewById(R.id.button_controller).setOnClickListener(v -> {});
    }

    public boolean onBackPressed() {
        toggleMenu();
        return true; // menu handled
    }

    public boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;
            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) {
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) {
                        toggleMenu();
                        return true;
                    }
                }
                break;
        }
        return false;
    }

    private void toggleMenu() {
        NativeBridge.nativeOnBackPressed();
    }
}