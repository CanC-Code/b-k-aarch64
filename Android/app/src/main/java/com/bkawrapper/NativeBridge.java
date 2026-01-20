// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.app.Activity;

public class NativeBridge {

    static {
        System.loadLibrary("wrapper");
    }

    // Menu init (used by MainActivity / MenuController)
    public static native void nativeInitMenu(Activity activity);

    // Renderer hook (used by GLRenderer)
    public static native void updateTexture(int textureId);
}