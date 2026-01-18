// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.view.Surface;

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.InputStream;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper");
    }

    private NativeBridge() {}

    // --------------------
    // ROM / OTR pipeline
    // --------------------
    public static native void loadRom(byte[] rom);
    public static native void processRom();

    public static native float getOTRProgress();
    public static native byte[] getOTRData();
    public static native void saveOTRToFile(String path);

    // --------------------
    // Game lifecycle
    // --------------------
    public static native void initGame(Surface surface);
    public static native void cleanupGame();

    public static native void startGameLoop();
    public static native void stopGameLoop();

    // --------------------
    // Rendering / textures
    // --------------------
    public static native int initTexture();
    public static native void updateTexture(int textureId);

    // --------------------
    // SAF ROM loader
    // --------------------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws Exception {
        try (InputStream is = resolver.openInputStream(uri);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {

            if (is == null) {
                throw new Exception("InputStream null");
            }

            byte[] buffer = new byte[8192];
            int read;
            while ((read = is.read(buffer)) > 0) {
                bos.write(buffer, 0, read);
            }

            byte[] rom = bos.toByteArray();
            if (rom.length < 0x1000) {
                throw new Exception("ROM too small");
            }

            loadRom(rom);
            processRom();
        }
    }

    // --------------------
    // Java-side OTR save helper
    // --------------------
    public static void saveOTRToPath(String path) throws Exception {
        byte[] otr = getOTRData();
        if (otr == null || otr.length == 0) {
            throw new Exception("OTR buffer empty");
        }

        try (FileOutputStream fos = new FileOutputStream(path)) {
            fos.write(otr);
            fos.flush();
        }
    }
}