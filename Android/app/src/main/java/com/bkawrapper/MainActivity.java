package com.bkawrapper;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import android.content.Intent;
import android.util.Log;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Initialize the JNI bridge
        NativeBridge.nativeInit(this);
    }

    // FIX: Added missing method for MenuController.java:16
    public void openFilePicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, 1001);
    }

    // Callback used by C++ background thread
    public void updateOtrProgress(final int percent, final String fileName) {
        runOnUiThread(() -> {
            Log.d("BKA", "Progress: " + percent + "% - " + fileName);
        });
    }
}
