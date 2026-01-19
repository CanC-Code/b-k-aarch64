package com.bkawrapper;

import android.view.View;

public final class NativeMenu {

    static {
        System.loadLibrary("bkawrapper");
    }

    private NativeMenu() {}

    /**
     * Initialize menu system with the menu overlay view.
     * Called once from MainActivity after layout inflation.
     */
    public static native void nativeInitMenu(View menuOverlay);

    /**
     * Toggle menu visibility (used for back press & gestures).
     */
    public static native void nativeOnBackPressed();

    /**
     * Explicit pause/resume hooks used by menu buttons.
     */
    public static native void nativePauseEmulator();
    public static native void nativeResumeEmulator();
}