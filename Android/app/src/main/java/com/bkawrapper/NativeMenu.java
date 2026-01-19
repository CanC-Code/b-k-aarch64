package com.bkawrapper;

import android.view.View;

public class NativeMenu {

    static {
        System.loadLibrary("emulator_native");
    }

    public static native void nativeInitMenu(View menuOverlay);
    public static native void nativeOnBackPressed();
    public static native void nativePauseEmulator();
    public static native void nativeResumeEmulator();
}