// File: Android/app/src/main/java/com/bkawrapper/Menu.java
package com.bkawrapper;

import android.app.Activity;
import android.widget.LinearLayout;

public final class Menu {

    private final Activity activity;
    private final LinearLayout menuOverlay;

    public Menu(Activity activity, LinearLayout menuOverlay) {
        this.activity = activity;
        this.menuOverlay = menuOverlay;

        NativeMenu.nativeInitMenu(menuOverlay);
    }

    public void toggle() {
        NativeMenu.nativeToggleMenu();
    }

    public void pauseEmulator() {
        NativeMenu.nativePauseEmulator();
    }

    public void resumeEmulator() {
        NativeMenu.nativeResumeEmulator();
    }
}