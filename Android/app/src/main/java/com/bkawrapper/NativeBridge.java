package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.view.Surface;

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // make sure otr_generator + JNI compiled here
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

    // -------- OTR Progress --------
    public static native float getOTRProgress(); // 0.0 to 1.0

    // -------- SAF Loader --------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws IOException {
        try (InputStream is = resolver.openInputStream(uri);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {

            if (is == null) throw new IOException("InputStream null");

            byte[] buf = new byte[8192];
            int r;
            while ((r = is.read(buf)) != -1) bos.write(buf, 0, r);

            byte[] rom = bos.toByteArray();
            if (rom.length < 0x1000) throw new IOException("ROM too small");

            loadRom(rom);
            processRom(); // generates in-memory OTR
        }
    }

    // -------- Helper: Save OTR to file path (Java side convenience) --------
    public static void saveOTRToPath(String path) throws IOException {
        byte[] otr = getOTRData();
        if (otr == null || otr.length == 0) throw new IOException("OTR empty");

        try (FileOutputStream fos = new FileOutputStream(path)) {
            fos.write(otr);
            fos.flush();
        }
    }
}