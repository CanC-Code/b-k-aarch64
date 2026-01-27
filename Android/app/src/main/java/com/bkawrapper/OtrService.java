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
                .setContentTitle("Generating OTR Files")
                .setContentText("Processing ROM assets in background...")
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();

        startForeground(1, notification);

        PowerManager powerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
        if (powerManager != null) {
            wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "BKAWrapper:OTRGenLock");
            wakeLock.acquire(30*60*1000L);
        }

        String uriString = intent.getStringExtra("uri");
        String outDir = intent.getStringExtra("outDir");

        new Thread(() -> {
            try {
                Uri romUri = Uri.parse(uriString);
                try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(romUri, "r")) {
                    if (pfd != null) {
                        Log.d(TAG, "Starting NDK OTR Generation...");
                        NativeBridge.runOtrGeneration(pfd.getFd(), getAssets(), outDir);
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "Error during OTR generation", e);
            } finally {
                NativeBridge.notifyFinished(); 
                cleanup();
            }
        }).start();

        return START_NOT_STICKY;
    }

    private void cleanup() {
        if (wakeLock != null && wakeLock.isHeld()) {
            wakeLock.release();
        }
        stopForeground(true);
        stopSelf();
        isRunning = false;
    }

    private void createNotificationChannel() {
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "OTR Generation", NotificationManager.IMPORTANCE_LOW);
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) manager.createNotificationChannel(channel);
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        cleanup();
        super.onDestroy();
    }
}
