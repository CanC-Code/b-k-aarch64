package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {
    static {
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInit(Object activity);
    public static native void startGameLoop();
    public static native void cleanupGame();
    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);
    
    // Texture stubs for GLRenderer
    public static native int initTexture();
    public static native void updateTexture(int textureId);

    // Required by MainActivity even if empty
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
}
