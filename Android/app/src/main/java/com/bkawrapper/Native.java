package com.bkawrapper;

public class Native {
    static { System.loadLibrary("bkawrapper"); }
    public static native void startEngine(String dir);
    public static native void fillArgb(int[] out);
}
