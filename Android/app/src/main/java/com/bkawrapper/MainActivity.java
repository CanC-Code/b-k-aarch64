package com.bkawrapper;

import android.os.Bundle;
import android.view.MotionEvent;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private boolean romReady = false; // should be set from native code
    private float swipeStartX = -1;
    private float swipeStartY = -1;

    static {
        System.loadLibrary("wrapper"); // Load your native library
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main); // adjust layout if needed
    }

    @Override
    public void onBackPressed() {
        if (!romReady) {
            super.onBackPressed();
            return;
        }

        NativeBridge.nativeOnBackPressed();
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                swipeStartX = event.getX();
                swipeStartY = event.getY();
                break;

            case MotionEvent.ACTION_UP:
                if (swipeStartX < 200 && swipeStartY < 200) { // top-left corner
                    float dy = event.getY() - swipeStartY;
                    if (dy > 150) { // swipe down threshold
                        NativeBridge.nativeOnBackPressed();
                        return true;
                    }
                }
                break;
        }
        return super.onTouchEvent(event);
    }
}