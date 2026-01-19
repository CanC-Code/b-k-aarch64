package com.bkawrapper;

import android.content.res.AssetManager;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // matches your CMake add_library(wrapper SHARED ...)
    }

    /**
     * Load and generate OTR from embedded ROM + YAML.
     * The progressCallback is a lambda: float -> void
     */
    public static native boolean loadEmbeddedOTRAssets(
            android.content.Context context,
            AssetManager assetManager,
            ProgressCallback progressCallback
    );

    public interface ProgressCallback {
        void onProgress(float progress); // 0.0 – 1.0
    }
}