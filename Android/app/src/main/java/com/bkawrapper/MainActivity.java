package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.opengl.GLSurfaceView;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;

public class MainActivity extends Activity {

    private static final int PICK_ROM = 1001;

    private GLSurfaceView glView;
    private Button loadButton;
    private LinearLayout progressOverlay;
    private ProgressBar progressBar;
    private TextView progressText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // GLSurfaceView
        glView = findViewById(R.id.gl_surface);

        // Buttons & progress
        loadButton = findViewById(R.id.button_load_game);
        progressOverlay = findViewById(R.id.progress_overlay);
        progressBar = findViewById(R.id.progress_bar);
        progressText = findViewById(R.id.progress_text);

        NativeBridge.nativeInit(getAssets());

        loadButton.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.setType("*/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(intent, PICK_ROM);
        });

        // Update progress periodically
        glView.postDelayed(progressUpdater, 50);
    }

    private final Runnable progressUpdater = new Runnable() {
        @Override
        public void run() {
            float progress = NativeBridge.nativeGetProgress();
            progressBar.setProgress((int)(progress * 100));
            progressText.setText(String.format("%d%%", (int)(progress * 100)));
            glView.postDelayed(this, 50);
        }
    };

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_ROM && resultCode == RESULT_OK) {
            Uri uri = data.getData();
            if (uri != null) {
                try {
                    InputStream is = getContentResolver().openInputStream(uri);
                    ByteArrayOutputStream bos = new ByteArrayOutputStream();
                    byte[] buffer = new byte[8192];
                    int read;
                    while ((read = is.read(buffer)) != -1) {
                        bos.write(buffer, 0, read);
                    }
                    is.close();
                    byte[] romData = bos.toByteArray();

                    progressOverlay.setVisibility(View.VISIBLE);

                    // Generate OTR using embedded YAMLs at runtime
                    NativeBridge.nativeGenerateOTR(romData, "otr_yaml/decompressed.pal.yaml");
                    NativeBridge.nativeGenerateOTR(romData, "otr_yaml/decompressed.us.v10.yaml");

                    // Load generated OTR into renderer
                    NativeBridge.nativeLoadOTR();
                    progressOverlay.setVisibility(View.GONE);

                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }
}