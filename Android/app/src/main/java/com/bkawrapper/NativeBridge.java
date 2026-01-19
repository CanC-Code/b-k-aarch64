package com.bkawrapper;

import android.content.res.AssetManager;

public final class NativeBridge {

    static {
        System.loadLibrary("bka"); // your native .so
    }

    // Initialize native side with AssetManager
    public static native void nativeInit(AssetManager assetManager);

    // Generate OTR from ROM bytes + YAML path in assets
    public static native boolean nativeGenerateOTR(
            byte[] romData,
            String yamlAssetPath
    );

    // Get progress [0.0 – 1.0]
    public static native float nativeGetProgress();

    // Load generated OTR into renderer
    public static native void nativeLoadOTR();
}