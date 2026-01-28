package com.bkawrapper;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import android.net.Uri;
import androidx.core.app.NotificationCompat;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

public class OtrService extends Service {
    private static final String CHANNEL_ID = "OtrServiceChannel";
    private static final int NOTIFICATION_ID = 1;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel serviceChannel = new NotificationChannel(
                    CHANNEL_ID, "OTR Generation Service",
                    NotificationManager.IMPORTANCE_LOW);
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) manager.createNotificationChannel(serviceChannel);
        }
    }

    public void updateOtrProgress(int percent, String status) {
        Intent intent = new Intent("OTR_PROGRESS");
        intent.putExtra("percent", percent);
        intent.putExtra("status", status);
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent);

        // Update the notification so the user sees progress in the tray
        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Extracting Assets...")
                .setContentText(percent + "% - " + status)
                .setSmallIcon(android.R.drawable.stat_sys_download)
                .setProgress(100, percent, false)
                .build();
        
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) manager.notify(NOTIFICATION_ID, notification);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String uriString = intent.getStringExtra("uri");
        String outDir = intent.getStringExtra("outDir");

        // Start as foreground immediately to satisfy Android requirements
        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Starting Extraction")
                .setSmallIcon(android.R.drawable.stat_sys_download)
                .build();
        startForeground(NOTIFICATION_ID, notification);

        new Thread(() -> {
            try {
                Uri uri = Uri.parse(uriString);
                try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(uri, "r")) {
                    if (pfd != null) {
                        NativeBridge.nativeInit(this);
                        NativeBridge.runOtrGeneration(pfd.getFd(), getAssets(), outDir);
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            stopForeground(true);
            stopSelf();
        }).start();

        return START_NOT_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
