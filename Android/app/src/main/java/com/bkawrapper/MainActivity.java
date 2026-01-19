package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import java.io.InputStream;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_ROM_FILE = 1001;

    private ProgressBar progressBar;
    private TextView progressText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

        Button loadButton = findViewById(R.id.button_load_game);
        loadButton.setOnClickListener(v -> openRomPicker());
    }

    private void openRomPicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*"); // ROM files
        startActivityForResult(intent, REQUEST_ROM_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_ROM_FILE && resultCode == Activity.RESULT_OK) {
            if (data != null && data.getData() != null) {
                Uri romUri = data.getData();
                loadRomAndGenerateOTR(romUri);
            }
        }
    }

    private void loadRomAndGenerateOTR(Uri romUri) {
        try (InputStream is = getContentResolver().openInputStream(romUri)) {
            byte[] romData = new byte[is.available()];
            is.read(romData);

            new Thread(() -> {
                // Initialize native with AssetManager
                NativeBridge.nativeInit(getAssets());

                // Generate OTR from ROM + YAML asset (user selects US/PAL)
                boolean success = NativeBridge.nativeGenerateOTR(
                        romData,
                        "otr_yaml/decompressed.us.v10.yaml"
                );

                runOnUiThread(() -> {
                    if (success) {
                        progressBar.setProgress(100);
                        progressText.setText("100%");
                        // Load into renderer
                        NativeBridge.nativeLoadOTR();
                    } else {
                        progressText.setText("OTR generation failed");
                    }
                });
            }).start();

        } catch (Exception e) {
            e.printStackTrace();
            progressText.setText("Failed to read ROM");
        }
    }
}