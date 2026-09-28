package com.bkawrapper;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;

public class NativeGameActivity extends Activity {
    static { System.loadLibrary("bkawrapper"); }

    public static native void bkaStartEngine(String dir);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        // Content view MUST be set before touching window insets —
        // the decor view doesn't exist until this call.
        GameView gv = new GameView(this);
        setContentView(gv);

        final View decor = getWindow().getDecorView();
        decor.setSystemUiVisibility(
              View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);

        decor.post(new Runnable() {
            @Override public void run() {
                if (Build.VERSION.SDK_INT >= 30) {
                    WindowInsetsController c = decor.getWindowInsetsController();
                    if (c != null) {
                        c.hide(WindowInsets.Type.systemBars());
                        c.setSystemBarsBehavior(
                            WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                    }
                }
            }
        });

        bkaStartEngine(getFilesDir().getAbsolutePath());
    }
}
