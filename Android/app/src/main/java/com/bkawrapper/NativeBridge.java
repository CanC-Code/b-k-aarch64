package com.bkawrapper;

import android.content.Context;
import android.content.res.AssetManager;

public class NativeBridge {
    // Matches: Java_com_bkawrapper_NativeBridge_nativeInit
    public static native void nativeInit(Object activity);

    // Matches: Java_com_bkawrapper_NativeBridge_runOtrGeneration
    public static native void runOtrGeneration(int romFd, AssetManager assetManager, String outputDir);
}
