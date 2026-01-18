// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.content.res.AssetManager;
import android.util.Log;

public class NativeBridge {

    private static final String TAG = "NativeBridge";

    // ROM processing & OTR
    public static boolean processRom(byte[] romData) {
        if (romData == null || romData.length == 0) return false;
        return nativeProcessRom(romData, romData.length);
    }

    public static float getOTRProgress() {
        return nativeGetOTRProgress();
    }

    // Game initialization & rendering
    public static void initGame(Object surface) {
        nativeInitGame(surface);
    }

    public static void initTexture() {
        nativeInitTexture();
    }

    public static void startGameLoop() {
        nativeStartGameLoop();
    }

    public static void stopGameLoop() {
        nativeStopGameLoop();
    }

    public static void cleanupGame() {
        nativeCleanupGame();
    }

    // -------------------
    // Native JNI methods
    // -------------------
    private static native boolean nativeProcessRom(byte[] romData, int romSize);
    private static native float nativeGetOTRProgress();

    private static native void nativeInitGame(Object surface);
    private static native void nativeInitTexture();
    private static native void nativeStartGameLoop();
    private static native void nativeStopGameLoop();
    private static native void nativeCleanupGame();

    // Load native library
    static {
        System.loadLibrary("wrapper");
        Log.i(TAG, "Native library 'wrapper' loaded");
    }
}