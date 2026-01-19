package com.bkawrapper;

import android.content.Context;
import android.content.res.AssetManager;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // matches your native library name
    }

    /**
     * Load and generate OTR from embedded ROM + YAML.
     * The progressCallback will be called with 0.0f → 1.0f
     */
    public static native boolean loadEmbeddedOTRAssets(
            Context context,
            AssetManager assetManager,
            ProgressCallback progressCallback
    );

    /**
     * Simple interface for reporting progress to Java
     */
    public interface ProgressCallback {
        void onProgress(float progress);
    }
}