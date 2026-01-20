package com.bkawrapper;

public final class NativeBridge {

    static {
        System.loadLibrary("bk_native");
    }

    // Menu control
    public static native void pauseGameLoop();
    public static native void resumeGameLoop();

    // Renderer hooks (required by GLRenderer)
    public static native void updateTexture(int textureId);

    // Optional quit hook (safe stub)
    public static void nativeQuitGame() {
        android.os.Process.killProcess(android.os.Process.myPid());
    }
}