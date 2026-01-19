package com.bkawrapper;

import android.content.res.AssetManager;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // name of your .so
    }

    // Initialize native side (renderer, etc.)
    public static native void nativeInit(AssetManager assetManager);

    // Generate OTR from ROM bytes + YAML asset
    public static native boolean nativeGenerateOTR(byte[] romData, String yamlAssetPath);

    // Get generation progress [0.0 – 1.0]
    public static native float nativeGetProgress();

    // Load in-memory OTR into renderer
    public static native void nativeLoadOTR();
}