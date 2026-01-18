package com.bkawrapper;

import android.content.ContentResolver;
import android.content.res.AssetManager;
import android.net.Uri;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

/**
 * Bridge between Java (Android) and native emulator/game core.
 * Handles ROM loading, OTR generation, and GPU texture management.
 */
public final class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // wrapper.cpp
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
    // Asset Manager (for YAML or other assets)
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
    /** Load ROM bytes into native core */
    public static native void loadRom(byte[] romData);

    /** Process ROM → generate OTR bytes (blocking) */
    public static native void processRom();

    /** Return OTR progress (0.0 → 1.0) */
    public static native float getOTRProgress();

    /** Retrieve generated OTR bytes */
    public static native byte[] getOTR();

    // -----------------------------
    // Rendering / lifecycle
    // -----------------------------
    /** Initialize game surface (GLSurfaceView / Surface) */
    public static native void initGame(Object surface);

    /** Initialize GPU texture placeholder (optional) */
    public static native void initTexture();

    /** Upload OTR bytes to GPU */
    public static native void initTextureWithOTR(byte[] otrData);

    /** Update GPU texture (per-frame) */
    public static native void updateTexture(int textureId);

    /** Return OpenGL texture ID */
    public static native int getTextureId();

    /** Start game loop (native thread) */
    public static native void startGameLoop();

    /** Stop game loop */
    public static native void stopGameLoop();

    /** Cleanup native resources */
    public static native void cleanupGame();
}