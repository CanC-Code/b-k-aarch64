package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {
    static {
        // This MUST match the name in CMakeLists.txt (add_library)
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInit(Object activity);
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();
    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);
}
