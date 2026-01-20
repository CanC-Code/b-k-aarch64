package com.bkawrapper;

import android.app.Activity;
import android.net.Uri;

public class NativeBridge {

    static {
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInit(Activity activity);
    public static native void loadRomFromUri(Object resolver, Uri uri);
    public static native float getOTRProgress();
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();
    public static native void initTexture();
    public static native void nativeOnBackPressed();
}