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
import androidx.core.app.NotificationCompat;

public class OtrService extends Service {
    private static final String CHANNEL_ID = "OTR_GEN_CHANNEL";
    private PowerManager.WakeLock wakeLock;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        createNotificationChannel();
        
        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Generating OTR Files")
                .setContentText("Processing ROM assets in background...")
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setOngoing(true) // Prevents user from swiping it away
                .build();

        startForeground(1, notification);

        // Acquire WakeLock to keep CPU running even if screen turns off
        PowerManager powerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "BKAWrapper:OTRGenLock");
        wakeLock.acquire(30*60*1000L /*30 minutes max*/);

        String uriString = intent.getStringExtra("uri");
        String outDir = intent.getStringExtra("outDir");

        new Thread(() -> {
            try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(Uri.parse(uriString), "r")) {
                if (pfd != null) {
                    // This calls the multithreaded C++ loop
                    NativeBridge.runOtrGeneration(pfd.getFd(), getAssets(), outDir);
                }
            } catch (Exception e) {
                e.printStackTrace();
            } finally {
                // NOTIFY THE ACTIVITY: Important for auto-launching game
                NativeBridge.notifyFinished(); 
                
                if (wakeLock != null && wakeLock.isHeld()) {
                    wakeLock.release();
                }
                stopForeground(true);
                stopSelf();
            }
        }).start();

        return START_NOT_STICKY;
    }

    private void createNotificationChannel() {
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, 
                "OTR Generation", 
                NotificationManager.IMPORTANCE_LOW
        );
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) {
            manager.createNotificationChannel(channel);
        }
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
