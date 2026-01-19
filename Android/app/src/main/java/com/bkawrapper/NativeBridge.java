package com.bkawrapper;

import android.content.ContentResolver;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper");
    }

    private NativeBridge() {}

    // -----------------------------
    // AssetManager for YAMLs
    // -----------------------------
    public static void setAssetManager(AssetManager manager) {
        if (manager != null) {
            nativeSetAssetManager(manager);
        }
    }

    private static native void nativeSetAssetManager(AssetManager manager);

    // -----------------------------
    // ROM loading
    // -----------------------------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws IOException {
        if (resolver == null || uri == null) throw new IOException("Invalid resolver or URI");

        try (InputStream in = resolver.openInputStream(uri);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {

            if (in == null) throw new IOException("Failed to open ROM input stream");

            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }

            loadRom(out.toByteArray());
        }
    }

    private static native void loadRom(byte[] romData);

    // -----------------------------
    // OTR generation
    // -----------------------------
    public static native void processRom();

    public static native float getOTRProgress();

    public static native byte[] getOTR();

    // -----------------------------
    // Game rendering integration
    // -----------------------------
    public static native void initGame(Object surface);

    public static native void initTexture();

    public static native void updateTexture(int textureId);

    public static native void initTextureWithOTR(byte[] otrData);

    public static native int getTextureId();

    public static native void startGameLoop();

    public static native void stopGameLoop();

    public static native void cleanupGame();

    // -----------------------------
    // Helper: poll native progress and push to renderer
    // -----------------------------
    public static void generateOTRWithCallback(GLRenderer renderer, long pollIntervalMs) {
        Handler handler = new Handler(Looper.getMainLooper());

        // Start generation
        processRom();

        Runnable poller = new Runnable() {
            @Override
            public void run() {
                float progress = getOTRProgress();
                // Optional: update UI via renderer if needed
                // e.g., update progress bar
                if (progress < 1.0f) {
                    handler.postDelayed(this, pollIntervalMs);
                } else {
                    // Finished, push OTR bytes to GLRenderer
                    byte[] otrData = getOTR();
                    renderer.setOTRData(otrData);
                }
            }
        };

        handler.post(poller);
    }
}