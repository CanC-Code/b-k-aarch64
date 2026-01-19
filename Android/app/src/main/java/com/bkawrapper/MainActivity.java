package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import android.opengl.GLSurfaceView;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.File;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_CODE_ROM = 1001;

    private GLSurfaceView glSurfaceView;
    private GLRenderer glRenderer;
    private Button loadButton;
    private LinearLayout progressOverlay;
    private ProgressBar progressBar;
    private TextView progressText;

    private byte[] loadedRom;
    private String palYaml = "otr_yaml/decompressed.pal.yaml";
    private String usYaml = "otr_yaml/decompressed.us.v10.yaml";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        glSurfaceView = findViewById(R.id.gl_surface);
        loadButton = findViewById(R.id.button_load_game);
        progressOverlay = findViewById(R.id.progress_overlay);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

        glRenderer = new GLRenderer();
        glRenderer.init();
        glSurfaceView.setRenderer(glRenderer);

        NativeBridge.nativeInit(getAssets());

        loadButton.setOnClickListener(v -> openRomPicker());
    }

    private void openRomPicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(intent, REQUEST_CODE_ROM);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_CODE_ROM && resultCode == Activity.RESULT_OK && data != null) {
            Uri romUri = data.getData();
            try {
                InputStream is = getContentResolver().openInputStream(romUri);
                loadedRom = new byte[is.available()];
                is.read(loadedRom);
                is.close();

                generateOTR(loadedRom, usYaml); // or palYaml as needed
            } catch (Exception e) {
                Toast.makeText(this, "Failed to read ROM", Toast.LENGTH_LONG).show();
            }
        }
    }

    private void generateOTR(byte[] rom, String yamlAsset) {
        progressOverlay.setVisibility(View.VISIBLE);
        progressBar.setProgress(0);
        progressText.setText("0%");

        new Thread(() -> {
            try {
                // Output directory in app files
                File outDir = getFilesDir();
                File outFile = new File(outDir, "generated.otr");

                boolean success = NativeBridge.nativeGenerateOTR(rom, yamlAsset, outFile.getAbsolutePath());
                if (!success) {
                    runOnUiThread(() -> {
                        Toast.makeText(this, "OTR generation failed", Toast.LENGTH_LONG).show();
                        progressOverlay.setVisibility(View.GONE);
                    });
                    return;
                }

                // Update progress to 100%
                runOnUiThread(() -> {
                    progressBar.setProgress(100);
                    progressText.setText("100%");
                });

                // Load generated OTR into renderer
                long ptr = NativeBridge.nativeGetOTRPointer();
                int size = NativeBridge.nativeGetOTRSize();
                glRenderer.setOTRMemory(ptr, size);

                runOnUiThread(() -> progressOverlay.setVisibility(View.GONE));

            } catch (Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> {
                    Toast.makeText(this, "OTR generation error", Toast.LENGTH_LONG).show();
                    progressOverlay.setVisibility(View.GONE);
                });
            }
        }).start();

        // Optional: UI thread progress updater
        new Thread(() -> {
            while (progressOverlay.getVisibility() == View.VISIBLE) {
                final float progress = NativeBridge.nativeGetProgress() * 100f;
                runOnUiThread(() -> {
                    progressBar.setProgress((int) progress);
                    progressText.setText((int) progress + "%");
                });
                try { Thread.sleep(50); } catch (InterruptedException ignored) {}
            }
        }).start();
    }
}