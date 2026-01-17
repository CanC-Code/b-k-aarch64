// File: app/src/main/java/com/bkawrapper/MainActivity.java
package com.bkawrapper;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import java.io.InputStream;

public class MainActivity extends AppCompatActivity {

    private ActivityResultLauncher<String[]> romPickerLauncher;
    private Button loadGameBtn;
    private Button startGameBtn;

    static {
        // Load your native library (name must match build.gradle CMake target)
        System.loadLibrary("bkrecomp");
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        loadGameBtn = findViewById(R.id.button_load_game);
        startGameBtn = findViewById(R.id.button_start_game);
        startGameBtn.setEnabled(false); // disabled until ROM loaded

        // SAF launcher for picking ROM
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

        startGameBtn.setOnClickListener(v -> {
            // Start game loop in a background thread
            new Thread(() -> runGameLoop()).start();
        });
    }

    private void handleRomUri(Uri uri) {
        try (InputStream is = getContentResolver().openInputStream(uri)) {
            if (is == null) return;

            byte[] romBytes = new byte[is.available()];
            int readBytes = is.read(romBytes);
            if (readBytes <= 0) return;

            System.out.println("ROM selected: " + uri.toString());
            System.out.println("ROM loaded into memory, size: " + readBytes + " bytes");

            // Load ROM into native layer
            if (loadRom(romBytes)) {
                System.out.println("ROM loaded successfully, generating BK.otr...");
                if (processRom() && initGame()) {
                    System.out.println("BK.otr generated and game initialized!");
                    runOnUiThread(() -> startGameBtn.setEnabled(true));
                } else {
                    System.out.println("Error: failed to generate BK.otr or initialize game");
                }
            } else {
                System.out.println("Error: failed to load ROM into native layer");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void runGameLoop() {
        // Simplified example loop
        while (true) {
            stepFrame();
            renderFrame();

            try {
                Thread.sleep(16); // ~60 FPS
            } catch (InterruptedException e) {
                break;
            }
        }
    }

    // === Native layer bindings ===

    // Load raw ROM bytes into memory
    private native boolean loadRom(byte[] romData);

    // Generate BK.otr dynamically from ROM
    private native boolean processRom();

    // Initialize ultra cores, interrupts, etc.
    private native boolean initGame();

    // Step one frame of game logic
    private native void stepFrame();

    // Render current frame to surface / texture
    private native void renderFrame();
}
