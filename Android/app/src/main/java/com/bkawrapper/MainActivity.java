package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;

/**
 * Bootstrap. Uses Theme.NoDisplay so it never creates a surface; starts
 * the foreground service and finishes immediately. All the real work
 * runs in BkaService.
 *
 * This is required because Motorola's libgui has a UAF on the buffer
 * transaction callback. Any visible window in our process — even one
 * with no rendering — triggers it. Only a NoDisplay activity that
 * finishes in onCreate avoids the surface entirely.
 */
public class MainActivity extends Activity {
    private static final String TAG = "BKA-Main";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.i(TAG, "bootstrap -> startForegroundService");

        // Seed ROM if bundled (see previous MainActivity logic — ROM
        // is already in files/auto_rom.z64 on this device).
        Intent svc = new Intent(this, BkaService.class);
        if (Build.VERSION.SDK_INT >= 26) {
            startForegroundService(svc);
        } else {
            startService(svc);
        }
        finish();
    }
}
