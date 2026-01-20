// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.app.Activity;

public class NativeBridge {
    static {
        System.loadLibrary("wrapper"); // matches your CMake target
    }

    /** Initialize the native menu (passes activity to JNI) */
    public static native void nativeInitMenu(Activity activity);
}