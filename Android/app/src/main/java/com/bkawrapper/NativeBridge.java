package com.bkawrapper;

import android.content.ContentResolver;
import android.content.res.AssetManager;
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
    // ROM loading (Java → native)
    // -----------------------------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws IOException {
        if (resolver == null || uri == null) {
            throw new IOException("Invalid resolver or URI");
        }

        try (InputStream in = resolver.openInputStream(uri);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {

            if (in == null) {
                throw new IOException("Failed to open ROM input stream");
            }

            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }

            loadRom(out.toByteArray());
        }
    }

    // -----------------------------
    // Asset Manager (for YAML loading)
    // -----------------------------
    public static void setAssetManager(AssetManager manager) {
        if (manager != null) {
            nativeSetAssetManager(manager);
        }
    }

    private static native void nativeSetAssetManager(AssetManager manager);

    // -----------------------------
    // Native OTR API
    // -----------------------------
    public static native void loadRom(byte[] romData);
    public static native void processRom();
    public static native float getOTRProgress();
    public static native byte[] getOTR();

    // -----------------------------
    // Rendering / lifecycle
    // -----------------------------
    public static native void initGame(Object surface);
    public static native void initTexture();
    public static native void updateTexture(int textureId);
    public static native void initTextureWithOTR(byte[] otrData);
    public static native int getTextureId();
    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native void cleanupGame();
}