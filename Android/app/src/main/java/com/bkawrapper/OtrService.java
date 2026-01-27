package com.bkawrapper;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.net.Uri;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import androidx.core.app.NotificationCompat;

public class OtrService extends Service {
    private static final String CHANNEL_ID = "OTR_GEN_CHANNEL";

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        createNotificationChannel();
        Notification notification = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("Generating OTR Files")
                .setContentText("Processing ROM assets...")
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .build();

        startForeground(1, notification);

        String uriString = intent.getStringExtra("uri");
        String outDir = intent.getStringExtra("outDir");

        new Thread(() -> {
            try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(Uri.parse(uriString), "r")) {
                if (pfd != null) {
                    NativeBridge.runOtrGeneration(pfd.getFd(), getAssets(), outDir);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            stopForeground(true);
            stopSelf();
        }).start();

        return START_NOT_STICKY;
    }

    private void createNotificationChannel() {
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "OTR Generation", NotificationManager.IMPORTANCE_LOW);
        getSystemService(NotificationManager.class).createNotificationChannel(channel);
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
