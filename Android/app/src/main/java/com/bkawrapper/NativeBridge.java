package com.bkawrapper;

import android.content.ContentResolver;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.util.Log;
import java.io.IOException;

public class NativeBridge {
    static {
        System.loadLibrary("bkawrapper");
    }

    // Lifecycle and Initialization
    public static native void nativeInit(Object activity);
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();

    // Texture handling for GLRenderer
    public static native int initTexture();
    public static native void updateTexture(int textureId);

    // OTR Orchestration
    private static native void runOtrGeneration(int romFd, AssetManager assetManager, String outputDir);

    public static void loadRomFromUri(ContentResolver resolver, Uri uri) {
        try (ParcelFileDescriptor pfd = resolver.openFileDescriptor(uri, "r")) {
            if (pfd != null) {
                // Internal app storage for extracted assets
                String outDir = "/data/data/com.bkawrapper/files/otr_data";
                
                // Pass the raw FD and the AssetManager to C++
                runOtrGeneration(pfd.getFd(), resolver.getAssets(), outDir);
            }
        } catch (IOException e) {
            Log.e("NativeBridge", "Failed to open ROM FileDescriptor", e);
        }
    }
}
