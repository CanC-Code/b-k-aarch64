package com.bkawrapper;

import android.app.Activity;

public class MenuNative {

    static {
        System.loadLibrary("bkawrapper");
    }

    // Called once to pass Activity if needed
    public static native void nativeInitMenu(Activity activity);

    // Toggle menu visibility (back button / gesture)
    public static native void nativeToggleMenu();

    // Explicit controls
    public static native void nativePauseEmulator();
    public static native void nativeResumeEmulator();
}