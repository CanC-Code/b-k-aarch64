package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.widget.ProgressBar;
import android.widget.Toast;

import java.io.IOException;

public class MainActivity extends Activity {

    private static final String TAG = "BKAWrapper";
    private static final int REQUEST_ROM_FILE = 1;

    private SurfaceView glSurfaceView;
    private ProgressBar progressBar;
    private Handler mainHandler;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface);
        progressBar = findViewById(R.id.progress_bar);

        mainHandler = new Handler(Looper.getMainLooper());

        // Launch file picker on start (or you can trigger with a button)
        pickRomFile();
    }

    private void pickRomFile() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*"); // optionally filter by extension
        startActivityForResult(intent, REQUEST_ROM_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_ROM_FILE && resultCode == RESULT_OK && data != null) {
            Uri romUri = data.getData();
            if (romUri != null) {
                loadAndProcessRom(romUri);
            }
        }
    }

    private void loadAndProcessRom(Uri romUri) {
        new Thread(() -> {
            try {
                byte[] romData = NativeBridge.loadRomFromUri(getContentResolver(), romUri);

                mainHandler.post(() -> {
                    Toast.makeText(this, "ROM loaded, generating OTR...", Toast.LENGTH_SHORT).show();
                    progressBar.setProgress(0);
                });

                // Start OTR generation in native
                NativeBridge.processRom(getAssets(), romData);

                // Poll progress
                pollProgress();

            } catch (IOException e) {
                Log.e(TAG, "Failed to load ROM", e);
                mainHandler.post(() -> Toast.makeText(this, "Failed to load ROM: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }
        }).start();
    }

    private void pollProgress() {
        mainHandler.postDelayed(new Runnable() {
            @Override
            public void run() {
                float progress = NativeBridge.getOTRProgress();
                progressBar.setProgress((int)(progress * 100));

                if (progress < 1.0f) {
                    mainHandler.postDelayed(this, 100);
                } else {
                    byte[] otrData = NativeBridge.getOTR();
                    Toast.makeText(MainActivity.this, "OTR generation complete, size: " + otrData.length + " bytes", Toast.LENGTH_LONG).show();

                    // TODO: Initialize GLRenderer with OTR data
                    initGLRenderer(otrData);
                }
            }
        }, 100);
    }

    private void initGLRenderer(byte[] otrData) {
        // Example: set up OpenGL rendering using your existing GLRenderer
        glSurfaceView.getHolder().addCallback(new SurfaceHolder.Callback() {
            @Override
            public void surfaceCreated(SurfaceHolder holder) {
                // Pass otrData to native renderer if needed
                Log.i(TAG, "GL surface created, ready to render OTR");
            }

            @Override
            public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
            }

            @Override
            public void surfaceDestroyed(SurfaceHolder holder) {
            }
        });
    }
}