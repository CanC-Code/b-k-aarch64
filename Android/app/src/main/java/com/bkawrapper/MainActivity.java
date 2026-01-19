package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.content.res.AssetManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.FrameLayout;

import java.io.InputStream;
import java.io.OutputStream;

public class MainActivity extends Activity {

    private static final int REQUEST_ROM = 1;

    private GLRenderer glSurfaceView;
    private Button loadRomButton;
    private ProgressBar progressBar;
    private TextView progressText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface);
        loadRomButton = findViewById(R.id.button_load_game);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

        loadRomButton.setOnClickListener(v -> selectROM());
    }

    private void selectROM() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(intent, REQUEST_ROM);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQUEST_ROM && resultCode == RESULT_OK && data != null) {
            Uri romUri = data.getData();
            loadROM(romUri);
        }
    }

    private void loadROM(Uri romUri) {
        new Thread(() -> {
            try {
                InputStream romStream = getContentResolver().openInputStream(romUri);
                byte[] romData = new byte[romStream.available()];
                romStream.read(romData);
                romStream.close();

                AssetManager am = getAssets();

                // Choose YAML dynamically; example loads PAL and US YAML
                NativeBridge.nativeGenerateOTR(romData, "otr_yaml/decompressed.pal.yaml", getFilesDir().getAbsolutePath());
                NativeBridge.nativeGenerateOTR(romData, "otr_yaml/decompressed.us.v10.yaml", getFilesDir().getAbsolutePath());

                runOnUiThread(() -> {
                    progressBar.setProgress(100);
                    progressText.setText("OTR Loaded");
                    // Load generated OTR into renderer
                    NativeBridge.nativeLoadOTR(getFilesDir() + "/latest.otr");
                });

            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }
}