// File: Android/app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.IntentFilter;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import android.opengl.GLSurfaceView;
import android.widget.FrameLayout;

import java.io.File;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

public class MainActivity extends AppCompatActivity {

    private static final String TAG              = "BKA-MainActivity";
    private static final int    PICK_ROM_REQUEST = 1001;

    private static final String SENTINEL_FILENAME = "extraction_complete";

    private View        menuOverlay;
    private View        otrContainer;
    private ProgressBar progressBar;
    private TextView    progressText;
    private TextView    currentArtifactText;

    private GLSurfaceView glSurfaceView;

    static {
        System.loadLibrary("bkawrapper");
    }

    private final BroadcastReceiver progressReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (action == null) return;

            switch (action) {
                case OtrService.ACTION_OTR_PROGRESS: {
                    int    percent = intent.getIntExtra("percent", 0);
                    String status  = intent.getStringExtra("status");
                    updateUI(percent, status);
                    break;
                }
                case OtrService.ACTION_OTR_COMPLETE:
                    handleExtractionComplete();
                    break;

                case OtrService.ACTION_OTR_ERROR: {
                    String error = intent.getStringExtra("message");
                    handleExtractionError(error);
                    break;
                }
            }
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Automation: if auto_rom.z64 exists in files dir, load it directly
        File autoRom = new File(getFilesDir(), "auto_rom.z64");

        // If extraction already finished (sentinel + valid rom_base.bin),
        // skip it entirely and boot the engine directly.  This prevents
        // the 15-second re-extraction on every launch that causes
        // "Activity top resumed state loss timeout" from the OS.
        if (hasExtractionCompleted()) {
            Log.i(TAG, "Extraction sentinel and base ROM verified — skipping ROM selection");
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
                getSplashScreen().setOnExitAnimationListener(splash -> {
                    Log.i(TAG, "Splash exited; starting GL engine");
                    splash.remove();
                    bootGameEngine();
                });
            } else {
                bootGameEngine();
            }
            return;
        }

        if (autoRom.exists()) {
            Log.i(TAG, "Auto-load ROM detected: " + autoRom.getAbsolutePath());
            // Run OTR extraction first - creates rom_base.bin required by engine
            startExtraction(Uri.fromFile(autoRom));
            return;
        }

        if (false) {   // original hasExtractionCompleted branch — dead now
            Log.i(TAG, "Extraction sentinel and base ROM verified — skipping ROM selection");
            // Wait for the splash screen to fully exit before creating the GL
            // surface. On Android 12+ / Motorola libgui, the splash surface
            // teardown races with GLSurfaceView creation and can leave a
            // stale TransactionCompletedListener in the framework, causing
            // a UAF on the app's binder thread.
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
                getSplashScreen().setOnExitAnimationListener(splash -> {
                    Log.i(TAG, "Splash exited; starting GL engine");
                    splash.remove();
                    bootGameEngine();
                });
            } else {
                bootGameEngine();
            }
        } else {
            setContentView(R.layout.activity_main);
            neutralizeXmlGLSurfaceView((ViewGroup) findViewById(android.R.id.content));

            menuOverlay         = findViewById(R.id.menu_overlay);
            otrContainer        = findViewById(R.id.otr_ui_container);
            progressBar         = findViewById(R.id.otr_progress_bar);
            progressText        = findViewById(R.id.otr_progress_text);
            currentArtifactText = findViewById(R.id.otr_current_artifact);

            new MenuController(this);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        maybeRetryGameLaunch();
        IntentFilter filter = new IntentFilter();
        filter.addAction(OtrService.ACTION_OTR_PROGRESS);
        filter.addAction(OtrService.ACTION_OTR_COMPLETE);
        filter.addAction(OtrService.ACTION_OTR_ERROR);
        LocalBroadcastManager.getInstance(this).registerReceiver(progressReceiver, filter);

        if (glSurfaceView != null) glSurfaceView.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        LocalBroadcastManager.getInstance(this).unregisterReceiver(progressReceiver);
        if (glSurfaceView != null) glSurfaceView.onPause();
    }

    // CRITICAL CORRECTION: Do not trust the sentinel file alone. Verify the C++ 
    // engine actually dropped the required physical payload.
    private boolean hasExtractionCompleted() {
        File sentinel = new File(getFilesDir(), SENTINEL_FILENAME);
        File romBase  = new File(getFilesDir(), "rom_base.bin");

        if (sentinel.exists() && (!romBase.exists() || romBase.length() < 4096)) {
            Log.w(TAG, "False sentinel detected (Silent Abort). Wiping corrupt state.");
            sentinel.delete();
            romBase.delete();
            return false;
        }
        return sentinel.exists() && romBase.exists();
    }

    private void neutralizeXmlGLSurfaceView(ViewGroup group) {
        if (group == null) return;
        for (int i = 0; i < group.getChildCount(); i++) {
            View child = group.getChildAt(i);
            if (child instanceof GLSurfaceView) {
                GLSurfaceView dummy = (GLSurfaceView) child;
                dummy.setEGLContextClientVersion(3);
                dummy.setRenderer(new GLSurfaceView.Renderer() {
                    @Override public void onSurfaceCreated(GL10 gl, EGLConfig config) {}
                    @Override public void onSurfaceChanged(GL10 gl, int width, int height) {}
                    @Override public void onDrawFrame(GL10 gl) {}
                });
                dummy.setRenderMode(GLSurfaceView.RENDERMODE_WHEN_DIRTY);
            } else if (child instanceof ViewGroup) {
                neutralizeXmlGLSurfaceView((ViewGroup) child);
            }
        }
    }

    public void openFilePicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, PICK_ROM_REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_ROM_REQUEST && resultCode == RESULT_OK && data != null) {
            Uri romUri = data.getData();
            if (romUri != null) {
                final int takeFlags = data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                try {
                    getContentResolver().takePersistableUriPermission(romUri, takeFlags);
                } catch (SecurityException e) {
                    Log.w(TAG, "Could not take persistable permissions, proceeding with temporary", e);
                }
                startExtraction(romUri);
            }
        }
    }

    private void startExtraction(Uri romUri) {
        // Don't block main thread - just start the service
        Intent serviceIntent = new Intent(this, OtrService.class);
        serviceIntent.putExtra("uri",    romUri.toString());
        serviceIntent.putExtra("outDir", getFilesDir().getAbsolutePath());

        // Upgraded to startForegroundService for Target SDK 34 compliance
        ContextCompat.startForegroundService(this, serviceIntent);
        
        // Keep UI responsive while extraction runs
        new Thread(() -> {
            try { Thread.sleep(500); } catch (InterruptedException e) {}
        }).start();
    }

    private void updateUI(int percent, String fileName) {
        if (progressBar         != null) progressBar.setProgress(percent);
        if (progressText        != null) progressText.setText(percent + "%");
        if (currentArtifactText != null) currentArtifactText.setText(fileName);
    }

    private void handleExtractionComplete() {
        if (currentArtifactText != null) currentArtifactText.setText("Booting Banjo-Kazooie...");
        if (otrContainer != null) {
            otrContainer.postDelayed(() -> {
                otrContainer.setVisibility(View.GONE);
                bootGameEngine();
            }, 800);
        } else {
            bootGameEngine();
        }
    }

    private void handleExtractionError(String message) {
        if (otrContainer  != null) otrContainer.setVisibility(View.GONE);
        if (menuOverlay   != null) menuOverlay.setVisibility(View.VISIBLE);
        Toast.makeText(this, "Extraction failed: " + message, Toast.LENGTH_LONG).show();
    }

    private static final int  RETRY_LIMIT = 0;   // disabled for diagnostic
    private static long s_lastGameStart = 0;
    private static int  s_retries = 0;

    private void bootGameEngine() {
        s_lastGameStart = System.currentTimeMillis();
        Intent intent = new Intent(this, NativeGameActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION);
        startActivity(intent);
        // Do NOT finish() — MainActivity stays in the backstack so
        // onResume() fires when NativeGameActivity dies early, letting
        // maybeRetryGameLaunch() reattempt.

        // External safety net: schedule an AlarmManager check 20s out.
        // AlarmManager runs in the system process and fires even if our
        // process is killed by the SurfaceFlinger UAF.  When it fires,
        // MainActivity.onNewIntent checks whether the game reached
        // running state; if not, it relaunches.
        // DISABLED 2026-09-24: the 20s AlarmManager watchdog was firing on
        // every boot and tearing down NativeGameActivity's surface.  Nothing
        // writes last_frame.txt, so onNewIntent saw age=MAX and re-launched,
        // which paused the running NativeActivity and killed its window.
        // Net effect: the process stayed alive but the GL surface was
        // destroyed 13-20s after boot and never recreated.
        // Re-enable only after a real heartbeat is written on each rendered
        // frame -- otherwise this watchdog is a guaranteed kill switch.
        if (false) {
            try {
                AlarmManager am = (AlarmManager) getSystemService(ALARM_SERVICE);
                Intent retry = new Intent(this, MainActivity.class);
                retry.setAction("com.bkawrapper.RETRY_LAUNCH");
                retry.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
                PendingIntent pi = PendingIntent.getActivity(
                        this, 0xC0DE, retry,
                        PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
                am.set(AlarmManager.RTC_WAKEUP,
                        System.currentTimeMillis() + 20_000L, pi);
            } catch (Throwable t) {
                Log.w(TAG, "AlarmManager schedule failed: " + t);
            }
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (false && intent != null && "com.bkawrapper.RETRY_LAUNCH".equals(intent.getAction())) {
            // AlarmManager fired. Did the game make it?
            long age = Long.MAX_VALUE;
            try {
                java.io.File f = new java.io.File(getFilesDir(), "last_frame.txt");
                if (f.exists()) {
                    String txt = new String(java.nio.file.Files.readAllBytes(f.toPath())).trim();
                    long lastOk = Long.parseLong(txt);
                    age = System.currentTimeMillis() - lastOk;
                }
            } catch (Exception ignored) {}
            if (age > 10_000L) {    // no successful frame in last 10s — relaunch
                Log.i(TAG, "AlarmManager watchdog fired (age=" + age + "ms) — relaunching");
                bootGameEngine();
            } else {
                Log.i(TAG, "AlarmManager watchdog fired; game healthy (age=" + age + "ms)");
            }
        }
    }

    // If NativeGameActivity dies within 6s of being started, retry up to
    // RETRY_LIMIT times.  The intermittency is a Motorola/Android-14
    // SurfaceFlinger UAF that fires during early startup, so a clean
    // second or third launch usually succeeds.
    private void maybeRetryGameLaunch() {
        if (s_lastGameStart == 0) return;
        long elapsed = System.currentTimeMillis() - s_lastGameStart;
        if (elapsed > 8000) return;                 // prior launch had time to succeed
        if (s_retries >= RETRY_LIMIT) {
            Log.w(TAG, "Retry limit reached; not restarting");
            return;
        }
        s_retries++;
        Log.i(TAG, "Early return (" + elapsed + "ms), retry " + s_retries);
        bootGameEngine();
    }
}
