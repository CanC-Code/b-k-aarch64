package com.bkawrapper;

import android.app.Activity;
import android.view.View;

public class Menu {

    private final Activity activity;

    public Menu(Activity activity) {
        this.activity = activity;
        NativeBridge.nativeInitMenu(activity);
    }

    public void toggleMenu() {
        NativeBridge.nativeOnBackPressed();
    }

    public void pauseEmulator() {
        NativeBridge.nativePauseEmulator();
    }

    public void resumeEmulator() {
        NativeBridge.nativeResumeEmulator();
    }

    public void showMenu() {
        NativeBridge.nativeOnBackPressed(); // ensures menu is visible
    }

    public void hideMenu() {
        NativeBridge.nativeOnBackPressed(); // toggles menu hidden
    }
}