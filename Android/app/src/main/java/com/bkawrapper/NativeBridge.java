package com.bkawrapper;

import android.app.Activity;

public class NativeBridge {

    static {
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInit(Activity activity);
    public static native void stopGameLoop();
}