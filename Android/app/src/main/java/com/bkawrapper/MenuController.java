package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;

public final class MenuController {

    private static final int CORNER_SIZE = 200;
    private static final int SWIPE_THRESHOLD = 150;

    private final Activity activity;
    private float startX = -1;
    private float startY = -1;

    public MenuController(Activity activity, View menuOverlay) {
        this.activity = activity;
        NativeMenu.nativeInitMenu(menuOverlay);
    }

    /** Back button entry point */
    public boolean onBackPressed() {
        NativeMenu.nativeToggleMenu();
        return true; // consume
    }

    /** Gesture detector */
    public boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                startX = event.getX();
                startY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                if (startX >= 0 && startY >= 0 &&
                    startX < CORNER_SIZE &&
                    startY < CORNER_SIZE) {

                    float dy = event.getY() - startY;
                    if (dy > SWIPE_THRESHOLD) {
                        NativeMenu.nativeToggleMenu();
                        reset();
                        return true;
                    }
                }
                reset();
                break;
        }
        return false;
    }

    private void reset() {
        startX = -1;
        startY = -1;
    }
}