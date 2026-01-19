package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {

    static {
        System.loadLibrary("emulator_native");
    }

    public static native void loadRomFromUri(ContentResolver cr, Uri uri);
    public static native float getOTRProgress();
    public static native void initTexture();
    public static native void startGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();
}