// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.util.Log;

import java.io.FileInputStream;
import java.io.IOException;

public class NativeBridge {

    private static final String TAG = "BK_NATIVE";

    // Load ROM from a URI (from file picker)
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) {
        try (ParcelFileDescriptor pfd = resolver.openFileDescriptor(uri, "r");
             FileInputStream fis = new FileInputStream(pfd.getFileDescriptor())) {

            byte[] buffer = new byte[fis.available()];
            int read = fis.read(buffer);
            if (read != buffer.length) {
                Log.w(TAG, "Read ROM size mismatch: " + read + " != " + buffer.length);
            }

            loadRom(buffer);

        } catch (IOException e) {
            Log.e(TAG, "Failed to load ROM from URI", e);
        }
    }

    // -----------------------------
    // JNI functions
    // -----------------------------

    // Load ROM bytes into native layer
    private static native void loadRom(byte[] romData);

    // Start processing ROM → OTR in background
    public static native void processRom();

    // Get OTR generation progress (0.0 → 1.0)
    public static native float getOTRProgress();

    // Retrieve finished OTR bytes
    public static native byte[] getOTRData();

    // Save OTR to file path
    public static native void saveOTRToFile(String path);

    // -----------------------------
    // Optional: Game loop / Surface / Texture hooks
    // These should already exist in your previous NativeBridge
    // -----------------------------
    public static native void initGame(Object surface);
    public static native void initTexture();
    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native void cleanupGame();

    static {
        System.loadLibrary("wrapper");
    }
}