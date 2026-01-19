package com.bkawrapper;

import android.content.res.AssetManager;

public final class NativeBridge {

    static {
        System.loadLibrary("bka"); // your native .so name
    }

    // Initialize native side (renderer, etc.)
    public static native void nativeInit(AssetManager assetManager);

    // Generate OTR from ROM bytes + YAML asset
    public static native boolean nativeGenerateOTR(
            byte[] romData,
            String yamlAssetPath,
            String outputDir
    );

    // Progress [0.0 – 1.0]
    public static native float nativeGetProgress();

    // Notify native renderer to load generated OTR
    public static native void nativeLoadOTR(String otrPath);
}