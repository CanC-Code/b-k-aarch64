package com.bkawrapper;

import android.content.ContentResolver;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.util.Log;

import java.io.ByteArrayOutputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.channels.FileChannel;

public final class NativeBridge {

    private static final String TAG = "BKAWrapper";

    static {
        System.loadLibrary("wrapper");
    }

    private NativeBridge() {}

    // -----------------------------
    // Load ROM bytes from URI
    // -----------------------------
    public static byte[] loadRomFromUri(ContentResolver resolver, Uri uri) throws IOException {
        if (resolver == null || uri == null) {
            throw new IOException("Invalid resolver or URI");
        }

        ParcelFileDescriptor pfd = resolver.openFileDescriptor(uri, "r");
        if (pfd == null) {
            throw new IOException("Failed to open file descriptor");
        }

        FileInputStream fis = new FileInputStream(pfd.getFileDescriptor());
        FileChannel channel = fis.getChannel();
        long size = channel.size();
        if (size > Integer.MAX_VALUE) {
            fis.close();
            pfd.close();
            throw new IOException("ROM file too large");
        }

        byte[] buffer = new byte[(int) size];
        int read = fis.read(buffer);
        fis.close();
        pfd.close();

        if (read != size) {
            throw new IOException("Failed to read full ROM");
        }

        return buffer;
    }

    // -----------------------------
    // Start OTR generation
    // -----------------------------
    public static void processRom(AssetManager assetManager, byte[] romData) {
        if (romData == null || romData.length == 0) {
            Log.e(TAG, "ROM data is empty");
            return;
        }

        nativeProcessRom(assetManager, romData);
    }

    // -----------------------------
    // Query OTR progress (0.0 - 1.0)
    // -----------------------------
    public static native float getOTRProgress();

    // -----------------------------
    // Retrieve generated OTR bytes
    // -----------------------------
    public static native byte[] getOTR();

    // -----------------------------
    // Native function
    // -----------------------------
    private static native void nativeProcessRom(AssetManager assetManager, byte[] romData);
}