package com.bkawrapper;

import android.content.Context;
import android.content.res.AssetManager;
import android.os.ParcelFileDescriptor;

public class NativeBridge {
    static {
        System.loadLibrary("bkawrapper");
    }

    // Interface to notify the UI when the Service is done
    public interface OtrCompletionListener {
        void onOtrComplete();
    }

    private static OtrCompletionListener completionListener;

    public static void setOtrCompletionListener(OtrCompletionListener listener) {
        completionListener = listener;
    }

    public static native void nativeInit(Context activity);
    public static native void runOtrGeneration(int romFd, AssetManager assetManager, String outputDir);
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();
    
    // Called by the Service when the C++ loop finishes
    public static void notifyFinished() {
        if (completionListener != null) {
            completionListener.onOtrComplete();
        }
    }
}
