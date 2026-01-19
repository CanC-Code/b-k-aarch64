package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;

/**
 * Handles menu toggle via back button or top-left swipe-down gesture.
 */
public class MenuController {

    private final Activity activity;
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    public MenuController(Activity activity) {
        this.activity = activity;

        // Initialize native menu
        NativeBridge.nativeInitMenu(activity);
    }

    /** Call this from Activity.onBackPressed() */
    public void onBackPressed() {
        NativeBridge.nativeOnBackPressed();
    }

    /** Call this from Activity.onTouchEvent() */
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
                        NativeBridge.nativeOnBackPressed(); // toggle menu
                        return true;
                    }
                }
                break;
        }
        return false;
    }
}