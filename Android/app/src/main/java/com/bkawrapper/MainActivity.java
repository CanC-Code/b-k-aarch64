package com.bkawrapper;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private static final int PICK_ROM_REQUEST = 1001;
    
    // UI Elements
    private View menuOverlay;
    private View otrContainer;
    private ProgressBar progressBar;
    private TextView progressText;
    private TextView currentArtifactText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize UI References
        menuOverlay = findViewById(R.id.menu_overlay);
        otrContainer = findViewById(R.id.otr_ui_container);
        progressBar = findViewById(R.id.otr_progress_bar);
        progressText = findViewById(R.id.otr_progress_text);
        currentArtifactText = findViewById(R.id.otr_current_artifact);

        // 1. Initialize Native Bridge
        NativeBridge.nativeInit(this);

        // 2. Initialize Menu Controller (This sets up the button listener)
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
            // Show the extraction UI and hide the menu
            menuOverlay.setVisibility(View.GONE);
            otrContainer.setVisibility(View.VISIBLE);
            
            // Logic to handle the ROM URI would go here
            // (e.g., passing the FD to OtrService)
        }
    }

    // This is called from C++ background thread
    public void updateOtrProgress(final int percent, final String fileName) {
        runOnUiThread(() -> {
            if (progressBar != null) progressBar.setProgress(percent);
            if (progressText != null) progressText.setText(percent + "%");
            if (currentArtifactText != null) currentArtifactText.setText(fileName);
        });
    }
}
