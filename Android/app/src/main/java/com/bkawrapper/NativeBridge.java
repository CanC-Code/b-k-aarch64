// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.app.Activity;
import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {

    static {
        System.loadLibrary("bk_wrapper"); // Must match your built lib name
    }

    // -------------------------
    // Menu / UI
    // -------------------------
    public static native void nativeInitMenu(Activity activity);
    public static native void nativeOnBackPressed();

    // -------------------------
    // ROM / Game management
    // -------------------------
    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);
    public static native float getOTRProgress();
    public static native void initTexture();
    public static native void startGameLoop();
    public static native void cleanupGame();
}