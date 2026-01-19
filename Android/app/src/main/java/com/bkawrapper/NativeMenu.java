// File: Android/app/src/main/java/com/bkawrapper/NativeMenu.java

package com.bkawrapper;

import android.app.Activity;
import android.widget.LinearLayout;

public final class NativeMenu {

    static {
        System.loadLibrary("your_native_lib_name");
    }

    public static native void nativeInitMenu(
            Activity activity,
            LinearLayout menuOverlay
    );

    public static native void nativeToggleMenu();

    public static native void nativePauseEmulator();

    public static native void nativeResumeEmulator();
}