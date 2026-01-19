package com.bkawrapper;

import android.app.Activity;
import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {

    // ------------------------------------------------------------
    // ROM / OTR
    // ------------------------------------------------------------
    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);
    public static native void initTexture();
    public static native void startGameLoop();
    public static native void stopGameLoop();
    public static native void cleanupGame();
    public static native float getOTRProgress();

    // ------------------------------------------------------------
    // Menu / Emulator control
    // ------------------------------------------------------------
    public static native void nativeInitMenu(Activity activity);
    public static native void nativeOnBackPressed();
    public static native void nativePauseEmulator();
    public static native void nativeResumeEmulator();
}