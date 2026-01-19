package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;
import androidx.activity.OnBackPressedCallback;

public class MenuController {

    private final Activity activity;
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    public MenuController(Activity activity, View menuOverlay) {
        this.activity = activity;

        // Initialize native menu
        NativeMenu.nativeInitMenu(menuOverlay);

        // Attach back button callback
        activity.getOnBackPressedDispatcher().addCallback(activity, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                NativeMenu.nativeOnBackPressed();
            }
        });

        // Forward touch events for swipe
        menuOverlay.setOnTouchListener((v, event) -> onTouchEvent(event));
    }

    private boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) { // top-left corner
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) { // swipe down threshold
                        NativeMenu.nativeOnBackPressed();
                        return true;
                    }
                }
                break;
        }
        return false;
    }
}