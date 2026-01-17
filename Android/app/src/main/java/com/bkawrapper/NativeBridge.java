package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.view.Surface;

import java.io.InputStream;
import java.io.IOException;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // MUST match add_library(wrapper ...)
    }

    private NativeBridge() {
        // no instances
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
    public static native int initTexture();
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
    // SAF helper
    // -------------------------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) {
        try (InputStream is = resolver.openInputStream(uri)) {
            if (is == null) return;

            byte[] buffer = new byte[is.available()];
            int offset = 0;

            while (offset < buffer.length) {
                int read = is.read(buffer, offset, buffer.length - offset);
                if (read <= 0) break;
                offset += read;
            }

            loadRom(buffer);
            processRom();

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}