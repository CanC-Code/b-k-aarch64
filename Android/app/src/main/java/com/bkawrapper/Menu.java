package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;

public class Menu {

    private final Activity activity;
    private final View menuOverlay;
    private boolean visible = false;

    private float swipeStartX = -1;
    private float swipeStartY = -1;

    public Menu(Activity activity) {
        this.activity = activity;
        this.menuOverlay = activity.findViewById(R.id.menu_overlay);
        hideMenu(); // start hidden
    }

    public void handleBackPressed() {
        if (!visible) {
            showMenu();
            NativeBridge.nativePauseEmulator();
        } else {
            hideMenu();
            NativeBridge.nativeResumeEmulator();
        }
    }

    public boolean handleTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;
            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) { // top-left corner
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) { // swipe down threshold
                        handleBackPressed();
                        return true;
                    }
                }
                break;
        }
        return false;
    }

    private void showMenu() {
        activity.runOnUiThread(() -> menuOverlay.setVisibility(View.VISIBLE));
        visible = true;
    }

    private void hideMenu() {
        activity.runOnUiThread(() -> menuOverlay.setVisibility(View.GONE));
        visible = false;
    }
}