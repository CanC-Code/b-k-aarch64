package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.LinearLayout;
import android.util.Log;

public class MenuController {

    private static final String TAG = "MENU_CONTROLLER";

    private final Activity activity;
    private final LinearLayout menuOverlay;

    // swipe tracking
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    private boolean menuVisible = false;

    public MenuController(Activity activity, LinearLayout menuOverlay) {
        this.activity = activity;
        this.menuOverlay = menuOverlay;

        // Initialize native menu
        NativeBridge.nativeInitMenu(activity);
        Log.i(TAG, "MenuController initialized");

        // Setup menu buttons (resume/exit/settings/controller)
        setupMenuButtons();
    }

    private void setupMenuButtons() {
        menuOverlay.findViewById(R.id.button_resume).setOnClickListener(v -> hideMenu());
        menuOverlay.findViewById(R.id.button_exit).setOnClickListener(v -> activity.finish());
        menuOverlay.findViewById(R.id.button_settings).setOnClickListener(v ->
                Log.i(TAG, "Settings clicked (stub)")
        );
        menuOverlay.findViewById(R.id.button_controller).setOnClickListener(v ->
                Log.i(TAG, "Controller layout clicked (stub)")
        );
    }

    // Back button override
    public boolean onBackPressed() {
        toggleMenu();
        return true; // handled
    }

    // Touch event forwarding (swipe top-left down)
    public boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) { // top-left corner
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) { // swipe down threshold
                        toggleMenu();
                        return true;
                    }
                }
                break;
        }
        return false;
    }

    private void toggleMenu() {
        if (!menuVisible) {
            menuVisible = true;
            NativeBridge.nativeOnBackPressed();
            Log.i(TAG, "Menu shown");
        } else {
            menuVisible = false;
            NativeBridge.nativeOnBackPressed();
            Log.i(TAG, "Menu hidden");
        }
    }
}