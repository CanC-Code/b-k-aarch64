package com.bkawrapper;

import android.app.Activity;

public class Menu {

    public Menu(Activity activity) {
        MenuNative.nativeInitMenu(activity);
    }

    public void toggleMenu() {
        MenuNative.nativeToggleMenu();
    }

    public void pauseEmulator() {
        MenuNative.nativePauseEmulator();
    }

    public void resumeEmulator() {
        MenuNative.nativeResumeEmulator();
    }
}