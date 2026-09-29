package com.bkawrapper;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

public class BkaService extends Service {
    private static final String TAG = "BKA-Service";
    private static final String CHANNEL = "bka_stream";
    private static final int NOTIF_ID = 0xB14;

    private StreamServer server;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.i(TAG, "onStartCommand");

        // Foreground service so Android doesn't kill us
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationManager nm = getSystemService(NotificationManager.class);
            NotificationChannel ch = new NotificationChannel(CHANNEL,
                "Banjo-Kazooie stream", NotificationManager.IMPORTANCE_LOW);
            ch.setShowBadge(false);
            nm.createNotificationChannel(ch);
        }
        Notification n = new Notification.Builder(this, CHANNEL)
                .setContentTitle("Banjo-Kazooie")
                .setContentText("Streaming on http://127.0.0.1:8080/")
                .setSmallIcon(android.R.drawable.ic_media_play)
                .setOngoing(true)
                .build();
        startForeground(NOTIF_ID, n);

        // Start HTTP server
        try {
            server = new StreamServer();
            Thread t = new Thread(() -> server.serve(), "BKA-Stream-Accept");
            t.setDaemon(true);
            t.start();
        } catch (Exception e) {
            Log.e(TAG, "server start failed", e);
            return START_NOT_STICKY;
        }

        // Launch Chrome to the stream page
        Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse("http://127.0.0.1:8080/"));
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(i);
        } catch (Exception e) {
            Log.e(TAG, "chrome launch failed", e);
        }

        // Start the engine after a short delay so Chrome is up first
        new Thread(() -> {
            try { Thread.sleep(1500); } catch (InterruptedException ignored) {}
            Log.i(TAG, "starting engine");
            Native.startEngine(getFilesDir().getAbsolutePath());
        }, "BKA-Engine-Launcher").start();

        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        if (server != null) server.stop();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
