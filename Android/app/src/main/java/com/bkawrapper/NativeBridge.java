package com.bkawrapper;

public final class NativeBridge {

    static {
        System.loadLibrary("bk_native");
    }

    public static native void pauseGameLoop();
    public static native void resumeGameLoop();
}