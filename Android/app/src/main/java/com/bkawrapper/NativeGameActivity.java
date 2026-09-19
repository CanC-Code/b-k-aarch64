package com.bkawrapper;

import android.app.NativeActivity;

public class NativeGameActivity extends NativeActivity {
    static {
        System.loadLibrary("bkawrapper");
    }
}
