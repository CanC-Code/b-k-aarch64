package com.bkawrapper;

import android.content.ContentResolver;
import android.content.res.AssetManager;
import android.net.Uri;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // Load native wrapper
    }

    private NativeBridge() {}

    // -----------------------------
    // ROM loading (Java → native)
    // -----------------------------
    /**
     * Load a ROM file from a URI and pass it to the native layer.
     */
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

            // Pass ROM bytes to native
            loadRom(out.toByteArray());
        }
    }

    // -----------------------------
    // Asset Manager (for YAML/asset access)
    // -----------------------------
    /**
     * Set the Android AssetManager for native access to assets.
     */
    public static void setAssetManager(AssetManager manager) {
        if (manager != null) {
            nativeSetAssetManager(manager);
        }
    }

    private static native void nativeSetAssetManager(AssetManager manager);

    // -----------------------------
    // Native OTR API
    // -----------------------------
    /**
     * Load raw ROM bytes into native core.
     */
    public static native void loadRom(byte[] romData);

    /**
     * Process the loaded ROM to generate OTR bytes.
     */
    public static native void processRom();

    /**
     * Return progress of OTR generation (0.0 → 1.0).
     */
    public static native float getOTRProgress();

    /**
     * Retrieve generated OTR bytes from native core.
     */
    public static native byte[] getOTR();

    // -----------------------------
    // Rendering / lifecycle
    // -----------------------------
    /**
     * Initialize the game with a GLSurfaceView surface object.
     */
    public static native void initGame(Object surface);

    /** Standard texture initialization (without OTR) */
    public static native void initTexture();

    /** Update an existing texture each frame */
    public static native void updateTexture(int textureId);

    /**
     * Initialize texture directly from OTR bytes.
     * Called after OTR generation is complete.
     */
    public static native void initTextureWithOTR(byte[] otrData);

    /** Get the OpenGL texture ID created by native core */
    public static native int getTextureId();

    /** Start the native game loop */
    public static native void startGameLoop();

    /** Stop the native game loop */
    public static native void stopGameLoop();

    /** Cleanup native resources */
    public static native void cleanupGame();
}