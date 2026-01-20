package com.bkawrapper;

import android.app.Activity;

public class NativeBridge {

    static {
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInitMenu(Activity activity);
    public static native void nativeOnBackPressed();

    public static native void startGameLoop();
    public static native void cleanupGame();
}