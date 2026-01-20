package com.bkawrapper;

import android.app.Activity;
import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {

    static {
        System.loadLibrary("bkawrapper");
    }

    /* =======================
       CORE / LIFECYCLE
       ======================= */

    public static native void nativeInit(Activity activity);

    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
    public static native void cleanupGame();

    /* =======================
       GL / TEXTURE
       ======================= */

    /** Called every frame by GLRenderer */
    public static native void updateTexture(int textureId);

    /** Called once when surface is ready */
    public static native void initTexture();

    /* =======================
       ROM / OTR
       ======================= */

    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);

    /** @return progress from 0.0f → 1.0f */
    public static native float getOTRProgress();
}