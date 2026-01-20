// File: Android/app/src/main/java/com/bkawrapper/NativeMenu.java
package com.bkawrapper;

import android.view.View;

public final class NativeMenu {

    static {
        System.loadLibrary("bk_wrapper");
    }

    private static View menuOverlay;

    public static void nativeInitMenu(View overlay) {
        menuOverlay = overlay;
    }

    public static native void nativeToggleMenu();
    public static native void nativePauseEmulator();
    public static native void nativeResumeEmulator();

    public static void showMenu() {
        if (menuOverlay != null) menuOverlay.setVisibility(View.VISIBLE);
    }

    public static void hideMenu() {
        if (menuOverlay != null) menuOverlay.setVisibility(View.GONE);
    }
}