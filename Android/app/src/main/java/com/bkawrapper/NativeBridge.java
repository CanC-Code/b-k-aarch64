package com.bkawrapper;

import android.content.Context;
import android.content.res.AssetManager;
import android.os.ParcelFileDescriptor;
import java.io.File;

public class NativeBridge {
    static {
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInit(Context activity);
    public static native void runOtrGeneration(int romFd, AssetManager assetManager, String outputDir);
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();
    public static native int initTexture();
    public static native void updateTexture(int tid);

    // This helper method replaces the failing logic in your Activity/Fragment
    public static void executeOtr(Context context, ParcelFileDescriptor pfd, String outDir) {
        if (pfd != null) {
            // FIX: Use context.getAssets() instead of resolver.getAssets()
            runOtrGeneration(pfd.getFd(), context.getAssets(), outDir);
        }
    }
}
