package com.bkawrapper;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import android.net.Uri;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

public class OtrService extends Service {
    private static OtrService instance;

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
    }

    // This is the method C++ will call
    public void updateOtrProgress(int percent, String status) {
        Intent intent = new Intent("OTR_PROGRESS");
        intent.putExtra("percent", percent);
        intent.putExtra("status", status);
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String uriString = intent.getStringExtra("uri");
        String outDir = intent.getStringExtra("outDir");
        Uri uri = Uri.parse(uriString);

        new Thread(() -> {
            try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(uri, "r")) {
                if (pfd != null) {
                    // Initialize the bridge to point to THIS service instance
                    NativeBridge.nativeInit(this);
                    NativeBridge.runOtrGeneration(pfd.getFd(), getAssets(), outDir);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            instance = null;
            stopSelf();
        }).start();

        return START_NOT_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
