package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;

public class NativeBridge {

    static {
        System.loadLibrary("wrapper");
    }

    public static native void setAssetManager(android.content.res.AssetManager mgr);
    public static native void loadRomFromUri(ContentResolver resolver, Uri uri);
    public static native void processRom();
    public static native float getOTRProgress();
    public static native byte[] getOTR();
}