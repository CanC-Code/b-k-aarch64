package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {

    static {
        System.loadLibrary("wrapper"); // Match your CMake/NDK library
    }

    /* ===========================
       ROM / OTR
       =========================== */
    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);
    public static native float getOTRProgress();
    public static native void saveOTRToFile(String path);

    /* ===========================
       Game loop
       =========================== */
    public static native void startGameLoop();
    public static native void cleanupGame();

    /* ===========================
       Menu
       =========================== */
    public static native void nativeInitMenu(Object activity);
    public static native void nativeOnBackPressed();

    /* ===========================
       GL / Texture
       =========================== */
    public static native void initTexture();
    public static native void updateTexture(int textureId);
}