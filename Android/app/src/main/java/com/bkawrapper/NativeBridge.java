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

    // -------- Native API --------

    public static native void loadRom(byte[] rom);
    public static native void processRom();

    public static native void initGame(Surface surface);
    public static native void cleanupGame();

    public static native void startGameLoop();
    public static native void stopGameLoop();

    public static native int initTexture();
    public static native void updateTexture(int texId);

    // -------- OTR access --------
    public static native byte[] getOTRData();
    public static native void saveOTRToFile(String path);

    // -------- SAF Loader --------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws Exception {
        try (InputStream is = resolver.openInputStream(uri);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {

            if (is == null) throw new Exception("InputStream null");

            byte[] buf = new byte[8192];
            int r;
            while ((r = is.read(buf)) > 0) bos.write(buf, 0, r);

            byte[] rom = bos.toByteArray();
            if (rom.length < 0x1000) throw new Exception("ROM too small");

            loadRom(rom);
            processRom();
        }
    }

    // -------- Helper: Save OTR to file path (Java side convenience) --------
    public static void saveOTRToPath(String path) throws Exception {
        byte[] otr = getOTRData();
        if (otr == null || otr.length == 0) throw new Exception("OTR empty");

        try (FileOutputStream fos = new FileOutputStream(path)) {
            fos.write(otr);
            fos.flush();
        }
    }
}