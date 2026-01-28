package com.bkawrapper;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.util.Log;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {
    private static final int PICK_ROM_REQUEST = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Ensure JNI is linked
        NativeBridge.nativeInit(this);
    }

    // This is what MenuController calls
    public void openFilePicker() {
        Log.d("BKA", "Opening SAF File Picker");
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*"); // You can change this to "application/octet-stream" if needed
        
        // Some devices require this to show internal storage
        intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, false);
        
        startActivityForResult(intent, PICK_ROM_REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        
        if (requestCode == PICK_ROM_REQUEST && resultCode == Activity.RESULT_OK) {
            if (data != null && data.getData() != null) {
                Uri uri = data.getData();
                Log.d("BKA", "Selected ROM Uri: " + uri.toString());
                
                // Now pass this URI to your OtrService or NativeBridge to start extraction
                // startExtraction(uri);
            }
        }
    }

    public void updateOtrProgress(final int percent, final String fileName) {
        runOnUiThread(() -> {
            Log.d("BKA", "Extraction Progress: " + percent + "% (" + fileName + ")");
        });
    }
}
