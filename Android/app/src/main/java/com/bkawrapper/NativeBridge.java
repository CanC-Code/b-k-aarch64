package com.bkawrapper;

import android.content.res.AssetManager;

public class NativeBridge {
    static {
        System.loadLibrary("bkawrapper");
    }

    // Existing methods
    public static native void nativeInit(Object activity);
    public static native void runOtrGeneration(int romFd, AssetManager assetManager, String outputDir);

    // FIX: Added missing method for OtrService.java:21
    public static void notifyFinished() {
        // Implementation for when extraction finishes
    }

    // FIX: Added missing method for GLRenderer.java:30
    public static void updateTexture(int textureId) {
        // Native stub for rendering
    }
}
