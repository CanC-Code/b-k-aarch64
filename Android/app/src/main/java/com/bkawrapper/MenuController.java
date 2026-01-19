package com.bkawrapper;

import android.view.MotionEvent;
import android.view.View;
import android.widget.LinearLayout;
import androidx.appcompat.app.AppCompatActivity;

public class MenuController {

    private final AppCompatActivity activity;
    private final LinearLayout menuOverlay;

    // Swipe detection
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    public MenuController(AppCompatActivity activity, LinearLayout menuOverlay) {
        this.activity = activity;
        this.menuOverlay = menuOverlay;

        // Initialize native menu overlay
        NativeMenu.nativeInitMenu(menuOverlay);
    }

    /** Call from MainActivity.onBackPressed() */
    public void onBackPressed() {
        NativeMenu.nativeOnBackPressed();
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
                        NativeMenu.nativeOnBackPressed();
                        return true;
                    }
                }
                break;
        }
        return false;
    }

    /** Attach controller: back button + touch forwarding */
    public static void attach(AppCompatActivity activity, MenuController controller) {
        // Override back button
        activity.getOnBackPressedDispatcher().addCallback(activity, new androidx.activity.OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                controller.onBackPressed();
            }
        });

        // Forward touch events
        View root = activity.getWindow().getDecorView();
        root.setOnTouchListener((v, event) -> controller.onTouchEvent(event));
    }
}