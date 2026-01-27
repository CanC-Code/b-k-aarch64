package com.bkawrapper;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import android.net.Uri;

public class OtrService extends Service {
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String uriString = intent.getStringExtra("uri");
        String outDir = intent.getStringExtra("outDir");
        Uri uri = Uri.parse(uriString);

        // Run in a background thread to prevent ANR
        new Thread(() -> {
            try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(uri, "r")) {
                if (pfd != null) {
                    NativeBridge.runOtrGeneration(pfd.getFd(), getAssets(), outDir);
                    NativeBridge.notifyFinished();
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            stopSelf();
        }).start();

        return START_NOT_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
