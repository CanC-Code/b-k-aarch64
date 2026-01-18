// File: NativeBridge.java
package com.bkawrapper;

import android.content.res.AssetManager;

public class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // matches your wrapper.cpp library name
    }

    // ----------------------------
    // ROM / OTR Pipeline
    // ----------------------------

    /** Load a ROM into native memory */
    public static native boolean loadRom(byte[] romData);

    /** Process loaded ROM using embedded YAML and generate OTR */
    public static native boolean processRom(AssetManager assetManager);

    /** Get current OTR generation progress (0.0 → 1.0) */
    public static native float getOTRProgress();

    /** Get the generated OTR as a byte array */
    public static native byte[] getOTRData();

    /** Save generated OTR to a file path */
    public static native void saveOTRToFile(String path);

    // ----------------------------
    // Convenience helpers
    // ----------------------------

    /** Synchronously generate OTR from ROM with progress updates */
    public static boolean generateOTR(byte[] romData, AssetManager mgr) {
        if (!loadRom(romData)) return false;
        return processRom(mgr);
    }
}