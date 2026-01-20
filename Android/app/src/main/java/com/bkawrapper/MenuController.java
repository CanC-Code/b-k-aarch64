// File: Android/app/src/main/java/com/bkawrapper/MenuController.java
package com.bkawrapper;

import android.app.Activity;

public class MenuController {

    private Activity activity;

    public MenuController(Activity activity) {
        this.activity = activity;
        NativeBridge.nativeInitMenu(activity);
    }

    public void toggle() {
        NativeBridge.nativeOnBackPressed();
    }

    // Optional attach helper if needed
    public static void attach(Activity activity, MenuController controller) {
        // Currently unused, could register activity callbacks
    }
}