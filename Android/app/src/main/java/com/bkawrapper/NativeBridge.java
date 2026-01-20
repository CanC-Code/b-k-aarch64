// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.app.Activity;

public class NativeBridge {

    static {
        System.loadLibrary("bk_wrapper");
    }

    // Game loop control
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();

    // Menu
    public static native void nativeInitMenu(Activity activity);
    public static native void nativeOnBackPressed();

    // Texture update (stub)
    public static native void updateTexture(int textureId);
}