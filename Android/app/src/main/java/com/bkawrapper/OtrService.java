package com.bkawrapper;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import android.os.PowerManager;
import android.util.Log;
import androidx.core.app.NotificationCompat;

public class OtrService extends Service {
    private static final String CHANNEL_ID = "OTR_GEN_CHANNEL";
    private static final String TAG = "OtrService";
    private PowerManager.WakeLock wakeLock;
    private boolean isRunning = false;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (isRunning) return START_NOT_STICKY;
        isRunning = true;

        createNotificationChannel();
        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Generating Assets")
                .setContentText("Please wait while we process the ROM...")
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setOngoing(true)
                .build();
        startForeground(1, notification);

        PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
        wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "BKA:OTR_Lock");
        wakeLock.acquire(10*60*1000L);

        String uriString = intent.getStringExtra("uri");
        String outDir = intent.getStringExtra("outDir");

        new Thread(() -> {
            try {
                Uri romUri = Uri.parse(uriString);
                try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(romUri, "r")) {
                    if (pfd != null) {
                        NativeBridge.runOtrGeneration(pfd.getFd(), getAssets(), outDir);
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "Extraction failed", e);
            } finally {
                NativeBridge.notifyFinished(); 
                if (wakeLock.isHeld()) wakeLock.release();
                stopForeground(true);
                stopSelf();
            }
        }).start();

        return START_NOT_STICKY;
    }

    private void createNotificationChannel() {
        NotificationChannel serviceChannel = new NotificationChannel(CHANNEL_ID, "OTR Generation", NotificationManager.IMPORTANCE_LOW);
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) manager.createNotificationChannel(serviceChannel);
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
