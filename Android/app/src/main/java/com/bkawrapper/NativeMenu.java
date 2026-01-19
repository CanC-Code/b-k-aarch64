package com.bkawrapper;

import android.view.View;

public final class NativeMenu {
    static {
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInitMenu(View menuOverlay);
    public static native void nativeToggleMenu();
}