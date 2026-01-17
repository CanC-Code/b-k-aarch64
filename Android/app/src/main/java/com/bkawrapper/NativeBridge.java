// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.view.Surface;

public class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // Loads wrapper.cpp
    }

    // ---- ROM / OTR ----
    public static native void loadRom(byte[] romData);
    public static native void processRom();

    // ---- Game init / cleanup ----
    public static native void initGame(Surface surface);
    public static native void cleanupGame();

    // ---- Frame stepping ----
    public static native void stepFrame();
    public static native int[] getFrameBuffer();

    // ---- Audio ----
    public static native short[] getAudioBuffer(int samples);

    // ---- Optional: save OTR to file ----
    public static native void saveOTR(String path);
}