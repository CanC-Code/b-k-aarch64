package com.bkawrapper;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import android.util.Log;

public class MainActivity extends AppCompatActivity {
    static {
        // This MUST match the project name in CMakeLists.txt
        System.loadLibrary("bkawrapper"); 
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize the bridge so C++ knows about this activity instance
        NativeBridge.nativeInit(this);
        
        Log.i("BKA", "Native library loaded and initialized.");
    }

    // This method is called by the C++ background thread
    public void updateOtrProgress(final int percent, final String fileName) {
        runOnUiThread(() -> {
            // Update your UI ProgressBar and TextView here
            Log.d("OTR_PROGRESS", "Extracting " + fileName + ": " + percent + "%");
        });
    }
}
