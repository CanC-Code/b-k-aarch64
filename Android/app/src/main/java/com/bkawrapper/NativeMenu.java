package com.bkawrapper;

import android.view.View;

public final class NativeMenu {

    static {
        System.loadLibrary("bk_wrapper"); // your native lib
    }

    private static View menuOverlay;

    /** Initialize with overlay from activity */
    public static void nativeInitMenu(View overlay) {
        menuOverlay = overlay;
    }

    /** Toggle menu visibility and pause/resume emulator */
    public static native void nativeToggleMenu();

    /** Called by native to show menu */
    public static void showMenu() {
        if (menuOverlay != null) {
            menuOverlay.setVisibility(View.VISIBLE);
        }
    }

    /** Called by native to hide menu */
    public static void hideMenu() {
        if (menuOverlay != null) {
            menuOverlay.setVisibility(View.GONE);
        }
    }
}