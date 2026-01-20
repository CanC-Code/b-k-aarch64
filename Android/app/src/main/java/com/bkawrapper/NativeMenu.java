// File: Android/app/src/main/java/com/bkawrapper/NativeMenu.java
package com.bkawrapper;

public class NativeMenu {
    /** Toggles the menu via JNI */
    public static native void nativeToggleMenu();

    public static native void nativePauseEmulator();
    public static native void nativeResumeEmulator();
}