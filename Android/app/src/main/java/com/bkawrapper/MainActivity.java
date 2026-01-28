package com.bkawrapper;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.util.Log;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import java.io.File;

public class MainActivity extends AppCompatActivity {
    private static final int PICK_ROM_REQUEST = 1001;
    
    private View menuOverlay;
    private View otrContainer;
    private ProgressBar progressBar;
    private TextView progressText;
    private TextView currentArtifactText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        menuOverlay = findViewById(R.id.menu_overlay);
        otrContainer = findViewById(R.id.otr_ui_container);
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);
        currentArtifactText = findViewById(R.id.otr_current_artifact);

        NativeBridge.nativeInit(this);
        new MenuController(this);
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
            Uri uri = data.getData();
            startExtraction(uri);
        }
    }

    private void startExtraction(Uri romUri) {
        menuOverlay.setVisibility(View.GONE);
        otrContainer.setVisibility(View.VISIBLE);

        new Thread(() -> {
            try (ParcelFileDescriptor pfd = getContentResolver().openFileDescriptor(romUri, "r")) {
                if (pfd != null) {
                    int fd = pfd.getFd();
                    String outputDir = getFilesDir().getAbsolutePath();
                    
                    Log.i("BKA", "Handing FD " + fd + " to Native");
                    // This call will block the background thread until finished
                    NativeBridge.runOtrGeneration(fd, getAssets(), outputDir);
                    
                    Log.i("BKA", "Native OTR Generation Finished");
                }
            } catch (Exception e) {
                Log.e("BKA", "Failed to open ROM FD", e);
            }
        }).start();
    }

    public void updateOtrProgress(final int percent, final String fileName) {
        runOnUiThread(() -> {
            progressBar.setProgress(percent);
            progressText.setText(percent + "%");
            currentArtifactText.setText(fileName);
        });
    }
}
