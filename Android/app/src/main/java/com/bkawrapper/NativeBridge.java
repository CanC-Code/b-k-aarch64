// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.app.Activity;
import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {

    static {
        System.loadLibrary("bkawrapper");
    }

    public static native void nativeInit(Activity activity);
    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();
    public static native void initTexture();
    public static native void updateTexture(int textureId);
    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);
    public static native float getOTRProgress();
}
