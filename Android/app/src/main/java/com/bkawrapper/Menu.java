package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.util.Log;

public class Menu {
    private static final String TAG = "MENU";

    private final Activity activity;
    private final LinearLayout menuOverlay;

    private float swipeStartX = -1;
    private float swipeStartY = -1;

    private boolean menuVisible = false;

    public Menu(Activity activity) {
        this.activity = activity;
        menuOverlay = activity.findViewById(R.id.menu_overlay);

        setupButtons();
    }

    /** Wire up the menu buttons to actions */
    private void setupButtons() {
        Button resumeButton = activity.findViewById(R.id.button_resume);
        Button exitButton = activity.findViewById(R.id.button_exit);
        Button settingsButton = activity.findViewById(R.id.button_settings);
        Button controllerButton = activity.findViewById(R.id.button_controller);

        resumeButton.setOnClickListener(v -> hideMenu());
        exitButton.setOnClickListener(v -> activity.finish());
        settingsButton.setOnClickListener(v ->
                Log.i(TAG, "Settings clicked (stub)")
        );
        controllerButton.setOnClickListener(v ->
                Log.i(TAG, "Controller layout clicked (stub)")
        );
    }

    /** Show the menu overlay and pause the emulator */
    public void showMenu() {
        menuOverlay.setVisibility(View.VISIBLE);
        NativeBridge.nativeOnBackPressed(); // ensures native pause logic sync
        menuVisible = true;
        Log.i(TAG, "Menu shown");
    }

    /** Hide the menu overlay and resume the emulator */
    public void hideMenu() {
        menuOverlay.setVisibility(View.GONE);
        NativeBridge.nativeOnBackPressed(); // ensures native resume logic sync
        menuVisible = false;
        Log.i(TAG, "Menu hidden");
    }

    /** Called from Activity onBackPressed() */
    public void handleBackPressed() {
        if (!menuVisible) {
            showMenu();
        } else {
            hideMenu();
        }
    }

    /** Detect swipe-down gesture to open the menu */
    public boolean handleTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) { // top-left corner
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) { // swipe-down threshold
                        handleBackPressed(); // toggle menu
                        return true;
                    }
                }
                break;
        }
        return false;
    }
}