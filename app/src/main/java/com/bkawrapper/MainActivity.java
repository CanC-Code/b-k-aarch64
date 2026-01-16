// File: app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private ActivityResultLauncher<String[]> romPickerLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Button loadGameBtn = findViewById(R.id.button_load_game);

        // SAF launcher
        romPickerLauncher = registerForActivityResult(
                new ActivityResultContracts.OpenDocument(),
                uri -> {
                    if (uri != null) {
                        handleRomUri(uri);
                    }
                }
        );

        loadGameBtn.setOnClickListener(v -> {
            romPickerLauncher.launch(new String[]{"application/octet-stream"});
        });
    }

    private void handleRomUri(Uri uri) {
        // TODO: pass URI to native layer for processing/decompilation
        // For now, just print URI
        System.out.println("ROM selected: " + uri.toString());
    }
}