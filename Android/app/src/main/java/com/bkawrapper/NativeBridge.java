// File: Android/app/src/main/java/com/bkawrapper/NativeBridge.java
package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.view.Surface;

import java.io.InputStream;
import java.io.IOException;

public class NativeBridge {

    static {
        System.loadLibrary("bka_wrapper"); // Matches wrapper.cpp
    }

    // ---- ROM / OTR ----
    public static native void loadRom(byte[] romData);
    public static native void processRom();

    // ---- Game init / cleanup ----
    public static native void initGame(Surface surface);
    public static native void cleanupGame();
    public static native void resetGame();

    // ---- Frame / Loop control ----
    public static native void startGameLoop();
    public static native void stopGameLoop();

    // ---- Framebuffer access ----
    public static native int[] getFrameBuffer();

    // ---- Audio ----
    public static native short[] getAudioBuffer(int samples);

    // ---- Optional: save OTR to file ----
    public static native void saveOTR(String path);

    // ---- Helper: load ROM from SAF URI directly ----
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) {
        try (InputStream is = resolver.openInputStream(uri)) {
            if (is == null) return;

            byte[] romData = new byte[is.available()];
            int read = 0;
            while (read < romData.length) {
                int n = is.read(romData, read, romData.length - read);
                if (n < 0) break;
                read += n;
            }

            loadRom(romData);
            processRom(); // Automatically build BK_OTR
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // ---- Convenience helpers for threaded game loop ----
    public static void startGame(Surface surface) {
        initGame(surface);
        startGameLoop();
    }

    public static void stopGame() {
        stopGameLoop();
        cleanupGame();
    }

    public static void reset() {
        resetGame();
    }
}