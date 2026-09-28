package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.Gravity;
import android.view.Window;
import android.view.WindowManager;
import android.widget.TextView;

public class StreamActivity extends Activity {
    private static final String TAG = "BKA-StreamAct";
    private StreamServer server;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        TextView tv = new TextView(this);
        tv.setText("Starting Banjo-Kazooie...\nBrowser will open shortly.");
        tv.setTextColor(0xFF00FF00);
        tv.setGravity(Gravity.CENTER);
        tv.setBackgroundColor(0xFF000000);
        setContentView(tv);

        try {
            server = new StreamServer();
            Thread t = new Thread(() -> server.serve(), "BKA-Stream-Accept");
            t.setDaemon(true);
            t.start();
        } catch (Exception e) {
            Log.e(TAG, "server start failed", e);
            tv.setText("Server failed: " + e.getMessage());
            return;
        }

        Log.i(TAG, "starting engine");
        Native.startEngine(getFilesDir().getAbsolutePath());

        tv.postDelayed(() -> {
            Log.i(TAG, "launching Chrome");
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse("http://127.0.0.1:8080/"));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            try {
                startActivity(i);
            } catch (Exception e) {
                Log.e(TAG, "chrome launch failed", e);
                tv.setText("Chrome launch failed.\nOpen http://127.0.0.1:8080/ manually.");
            }
        }, 1500);
    }

    @Override
    protected void onDestroy() {
        if (server != null) server.stop();
        super.onDestroy();
    }
}
