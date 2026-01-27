package com.bkawrapper;

import android.content.Context;
import android.content.res.AssetManager;

public class NativeBridge {
    static {
        // This MUST match the name in CMakeLists.txt: add_library(bkawrapper ...)
        System.loadLibrary("bkawrapper");
    }

    public interface OtrCompletionListener {
        void onOtrComplete();
    }

    private static OtrCompletionListener completionListener;

    public static void setOtrCompletionListener(OtrCompletionListener listener) {
        completionListener = listener;
    }

    // --- Native Methods ---
    public static native void nativeInit(Context activity);
    public static native void runOtrGeneration(int romFd, AssetManager assetManager, String outputDir);
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();
    public static native int initTexture();
    public static native void updateTexture(int tid);

    // --- Callback for C++ ---
    public static void notifyFinished() {
        if (completionListener != null) {
            completionListener.onOtrComplete();
        }
    }
}
