package com.bkawrapper;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;
import androidx.activity.OnBackPressedCallback;

public class MenuController {

    private final Activity activity;
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    public MenuController(Activity activity) {
        this.activity = activity;
        NativeBridge.nativeInitMenu(activity);
    }

    public void onBackPressed() {
        NativeBridge.nativeOnBackPressed();
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
                        NativeBridge.nativeOnBackPressed();
                        return true;
                    }
                }
                break;
        }
        return false;
    }

    public static void attach(Activity activity, MenuController menuController) {
        activity.getOnBackPressedDispatcher().addCallback(activity, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                menuController.onBackPressed();
            }
        });

        View root = activity.getWindow().getDecorView();
        root.setOnTouchListener((v, event) -> menuController.onTouchEvent(event));
    }
}