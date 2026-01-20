// File: Android/app/src/main/java/com/bkawrapper/MenuController.java
package com.bkawrapper;

import android.app.Activity;

public class MenuController {

    private boolean menuVisible = false;

    public MenuController() {
    }

    /** Initialize native menu with activity reference */
    public void initMenu(Activity activity) {
        NativeBridge.nativeInitMenu(activity);
    }

    /** Toggle menu visibility from Java side */
    public void toggleMenu() {
        NativeMenu.nativeToggleMenu();
        menuVisible = !menuVisible;
    }

    /** Called by MainActivity on back press */
    public boolean onBackPressed() {
        if (menuVisible) {
            toggleMenu();
            return true; // handled
        }
        return false; // not handled
    }
}