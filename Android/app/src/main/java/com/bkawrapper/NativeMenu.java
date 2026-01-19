package com.bkawrapper;

import android.view.View;

public class NativeMenu {

    static {
        System.loadLibrary("wrapper"); // your JNI library
    }

    /** Initialize menu (called from MenuController) */
    public static native void nativeInitMenu(View menuOverlay);

    /** Called on back button or swipe gesture */
    public static native void nativeOnBackPressed();

    /** Pause emulator loop */
    public static native void nativePauseEmulator();

    /** Resume emulator loop */
    public static native void nativeResumeEmulator();
}