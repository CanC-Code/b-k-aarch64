package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.view.Surface;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper");
    }

    private NativeBridge() {}

    // -------- Native API --------
    public static native void loadRom(byte[] rom);
    public static native void core1_loadOTR(byte[] rom, int size); // <-- new
    public static native byte[] getOTRData();                      // <-- new
    public static native void saveOTRToFile(String path);          // <-- new
    public static native void initGame(Surface surface);
    public static native void cleanupGame();
    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native int initTexture();
    public static native void updateTexture(int texId);

    // -------- SAF Loader --------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws Exception {
        try (InputStream is = resolver.openInputStream(uri);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {

            if (is == null) throw new Exception("InputStream null");

            byte[] buf = new byte[8192];
            int r;
            while ((r = is.read(buf)) > 0) {
                bos.write(buf, 0, r);
            }

            byte[] rom = bos.toByteArray();
            if (rom.length < 0x1000) throw new Exception("ROM too small");

            // Load ROM
            loadRom(rom);

            // Generate dynamic OTR
            core1_loadOTR(rom, rom.length);

            // Optional: save OTR to disk for debugging
            // saveOTRToFile("/sdcard/BK.OTR");
        }
    }
}