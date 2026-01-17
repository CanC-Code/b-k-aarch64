// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.view.Surface;

import java.io.InputStream;
import java.io.IOException;

public final class NativeBridge {

    static {
        // MUST match the CMake add_library() name
        System.loadLibrary("wrapper");
    }

    private NativeBridge() {
        // Prevent instantiation
    }

    // -------------------------
    // ROM / OTR
    // -------------------------
    public static native void loadRom(byte[] romData);
    public static native void processRom();

    // -------------------------
    // Game lifecycle
    // -------------------------
    public static native void initGame(Surface surface);
    public static native void cleanupGame();
    public static native void resetGame();

    // -------------------------
    // Game loop
    // -------------------------
    public static native void startGameLoop();
    public static native void stopGameLoop();

    // -------------------------
    // Rendering
    // -------------------------
    public static native int initTexture();            // Returns OpenGL texture ID
    public static native void updateTexture(int texId);

    // -------------------------
    // Audio
    // -------------------------
    public static native short[] getAudioBuffer(int samples);

    // -------------------------
    // Optional debug / export
    // -------------------------
    public static native void saveOTR(String path);

    // -------------------------
    // SAF helper: load ROM from URI directly
    // -------------------------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) {
        try (InputStream is = resolver.openInputStream(uri)) {
            if (is == null) return;

            int size = is.available();
            byte[] buffer = new byte[size];
            int offset = 0;

            while (offset < size) {
                int read = is.read(buffer, offset, size - offset);
                if (read <= 0) break;
                offset += read;
            }

            if (offset > 0) {
                loadRom(buffer);
                processRom();
            }

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // -------------------------
    // Convenience helpers
    // -------------------------
    public static void startGame(Surface surface) {
        initGame(surface);
        startGameLoop();
    }

    public static void stopGame() {
        stopGameLoop();
        cleanupGame();
    }

    public static void reset() {
        resetGame();
    }
}