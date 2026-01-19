package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;

public class MenuController {

    private final Activity activity;

    // Swipe detection
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    public MenuController(Activity activity) {
        this.activity = activity;

        // Initialize native menu
        NativeBridge.nativeInitMenu(activity);
    }

    /** Call from MainActivity.onBackPressed() */
    public void onBackPressed() {
        NativeBridge.nativeOnBackPressed();
    }

    /** Call from MainActivity.onTouchEvent() */
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
                        NativeBridge.nativeOnBackPressed();
                        return true;
                    }
                }
                break;
        }
        return false;
    }

    /** Helper to attach gesture + back override to an Activity */
    public static void attach(Activity activity, MenuController menuController) {
        // Override back button
        activity.getOnBackPressedDispatcher().addCallback(activity, new androidx.activity.OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                menuController.onBackPressed();
            }
        });

        // Forward touch events automatically
        View root = activity.getWindow().getDecorView();
        root.setOnTouchListener((v, event) -> menuController.onTouchEvent(event));
    }
}