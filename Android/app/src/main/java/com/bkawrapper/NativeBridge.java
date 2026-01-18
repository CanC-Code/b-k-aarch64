package com.bkawrapper;

import android.content.res.AssetManager;
import android.util.Log;

public class NativeBridge {

    private static final String TAG = "BK_NativeBridge";

    // --------------------
    // JNI methods
    // --------------------
    public static native boolean processRom(AssetManager assetManager, byte[] romData);
    public static native float getOTRProgress();
    public static native byte[] getOTR();

    // --------------------
    // Java helpers
    // --------------------

    /**
     * Start processing a ROM with OTR generation
     * @param assetManager AssetManager from context
     * @param romData ROM bytes
     * @return true if processing started successfully
     */
    public static boolean loadRomFromBytes(AssetManager assetManager, byte[] romData) {
        if (romData == null || romData.length == 0) {
            Log.e(TAG, "ROM data is null or empty");
            return false;
        }

        boolean started = processRom(assetManager, romData);
        if (!started) {
            Log.e(TAG, "Failed to start ROM processing");
        } else {
            Log.i(TAG, "ROM processing started");
        }
        return started;
    }

    /**
     * Poll the OTR progress (0.0f → 1.0f)
     */
    public static float pollOTRProgress() {
        return getOTRProgress();
    }

    /**
     * Retrieve the generated OTR bytes after processing finishes
     */
    public static byte[] retrieveOTR() {
        byte[] otrData = getOTR();
        if (otrData == null || otrData.length == 0) {
            Log.e(TAG, "OTR data not ready");
            return null;
        }
        Log.i(TAG, "OTR data retrieved: " + otrData.length + " bytes");
        return otrData;
    }

    // --------------------
    // Game initialization stubs
    // --------------------
    public static native void initGame(Object surface);
    public static native void initTexture();
    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native void cleanupGame();

    // --------------------
    // Load native library
    // --------------------
    static {
        System.loadLibrary("wrapper");
    }
}