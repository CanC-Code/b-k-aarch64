package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.InputStream;

public final class NativeBridge {

    static { System.loadLibrary("wrapper"); }
    private NativeBridge(){}

    // JNI
    public static native void loadRom(byte[] rom);
    public static native void processRom();
    public static native float getOTRProgress();      // <- progress
    public static native byte[] getOTRData();
    public static native void saveOTRToFile(String path);

    // Helper: load ROM from URI
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws Exception {
        try(InputStream is = resolver.openInputStream(uri);
            ByteArrayOutputStream bos = new ByteArrayOutputStream()){
            if(is==null) throw new Exception("InputStream null");
            byte[] buf = new byte[8192]; int r;
            while((r=is.read(buf))>0) bos.write(buf,0,r);
            byte[] rom = bos.toByteArray();
            if(rom.length<0x1000) throw new Exception("ROM too small");
            loadRom(rom);
            processRom();
        }
    }

    public static void saveOTRToPath(String path) throws Exception {
        byte[] otr = getOTRData();
        if(otr==null || otr.length==0) throw new Exception("OTR empty");
        try(FileOutputStream fos = new FileOutputStream(path)){
            fos.write(otr);
            fos.flush();
        }
    }
}