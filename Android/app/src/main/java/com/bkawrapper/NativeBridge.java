package com.bkawrapper;

public class NativeBridge {

    static {
        System.loadLibrary("bk_wrapper"); // matches your CMake target
    }

    // Core/game methods
    public static native void nativeInitCore();
    public static native void nativeOnCoreStep();

    // Menu methods
    public static native void nativeInitMenu();
    public static native boolean nativeOnBackPressed();

    // New JNI hooks for MainActivity
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();

    // Called from GLRenderer
    public static native void updateTexture(int textureId);
}