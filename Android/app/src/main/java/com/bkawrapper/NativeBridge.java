package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper");
    }

    private NativeBridge() {}

    // -----------------------------
    // ROM loading
    // -----------------------------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws IOException {
        try (InputStream in = resolver.openInputStream(uri);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {

            if (in == null) {
                throw new IOException("Failed to open ROM input stream");
            }

            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) > 0) {
                out.write(buffer, 0, read);
            }

            loadRom(out.toByteArray());
        }
    }

    // -----------------------------
    // Native API
    // -----------------------------
    public static native void loadRom(byte[] romData);
    public static native void processRom();
    public static native float getOTRProgress();

    // -----------------------------
    // Rendering / lifecycle
    // -----------------------------
    public static native void initGame(Object surface);
    public static native void initTexture();
    public static native void updateTexture(int textureId);
    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native void cleanupGame();
}