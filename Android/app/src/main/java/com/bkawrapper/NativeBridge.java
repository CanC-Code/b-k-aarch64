package com.bkawrapper;

import android.content.ContentResolver;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.FrameLayout;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;

public final class NativeBridge {

    static {
        System.loadLibrary("wrapper");
    }

    private NativeBridge() {}

    // -----------------------------
    // Embedded ROM loader
    // -----------------------------
    public static void loadRomFromUri(ContentResolver resolver, Uri uri) throws IOException {
        if (resolver == null || uri == null) throw new IOException("Invalid resolver or URI");

        try (InputStream in = resolver.openInputStream(uri);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {

            if (in == null) throw new IOException("Failed to open ROM input stream");

            byte[] buffer = new byte[8192];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }

            loadRom(out.toByteArray());
        }
    }

    // -----------------------------
    // Asset manager (for YAMLs)
    // -----------------------------
    public static void setAssetManager(android.content.res.AssetManager manager) {
        if (manager != null) {
            nativeSetAssetManager(manager);
        }
    }

    private static native void nativeSetAssetManager(android.content.res.AssetManager manager);

    // -----------------------------
    // Native ROM/OTR API
    // -----------------------------
    public static native void loadRom(byte[] romData);
    public static native void processRom();
    public static native float getOTRProgress();
    public static native byte[] getOTR();

    // -----------------------------
    // Real-time progress integration
    // -----------------------------
    public static void generateOTRWithProgress(FrameLayout overlay,
                                               ProgressBar progressBar,
                                               TextView progressText,
                                               Runnable onComplete) {
        overlay.setVisibility(android.view.View.VISIBLE);
        progressBar.setProgress(0);
        progressText.setText("0%");

        new Thread(() -> {
            processRom();

            Handler handler = new Handler(Looper.getMainLooper());
            while (true) {
                float progress = getOTRProgress();
                final int p = Math.round(progress * 100f);

                handler.post(() -> {
                    progressBar.setProgress(p);
                    progressText.setText(p + "%");
                });

                if (progress >= 1.0f) break;

                try { Thread.sleep(50); } catch (InterruptedException ignored) {}
            }

            byte[] otrData = getOTR();

            handler.post(() -> {
                overlay.setVisibility(android.view.View.GONE);
                if (onComplete != null) onComplete.run();
            });

        }).start();
    }
}