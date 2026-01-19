package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;

public class MenuController implements View.OnTouchListener {

    private static final int SWIPE_THRESHOLD = 120;

    private float startX;
    private float startY;

    private final Activity activity;

    public MenuController(Activity activity) {
        this.activity = activity;
    }

    public static void attach(Activity activity, MenuController controller) {
        View decorView = activity.getWindow().getDecorView();
        decorView.setOnTouchListener(controller);
    }

    /**
     * Called from MainActivity.onBackPressed()
     */
    public void onBackPressed() {
        NativeMenu.nativeOnBackPressed();
    }

    @Override
    public boolean onTouch(View v, MotionEvent event) {
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                startX = event.getX();
                startY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                float dx = event.getX() - startX;
                float dy = event.getY() - startY;

                // Swipe down from top-left corner
                if (startX < 200 && startY < 200 && dy > SWIPE_THRESHOLD) {
                    NativeMenu.nativeOnBackPressed();
                    return true;
                }
                break;
        }
        return false;
    }
}