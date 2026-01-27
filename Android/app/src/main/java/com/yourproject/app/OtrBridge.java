// Android/app/src/main/java/com/yourproject/app/OtrBridge.java
package com.yourproject.app;

import android.content.res.AssetManager;

public class OtrBridge {
    static {
        System.loadLibrary("bkawrapper");
    }

    /**
     * @param romFd The file descriptor of the user's ROM
     * @param assetManager The Android AssetManager to load manifest.bin
     * @param manifestPath Filename in assets (e.g., "manifest_us.bin")
     * @param outputDir Where to save the generated OTR files
     */
    public native boolean runExtraction(int romFd, AssetManager assetManager, 
                                       String manifestPath, String outputDir);
}
