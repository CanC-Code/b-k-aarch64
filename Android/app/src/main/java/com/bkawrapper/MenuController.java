// File: Android/app/src/main/java/com/bkawrapper/MenuController.java
package com.bkawrapper;

import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

public class MenuController {
    private final MainActivity activity;
    public LinearLayout menuOverlay;

    public MenuController(MainActivity activity) {
        this.activity = activity;
        setupUI();
    }

    private void setupUI() {
        // Find your existing layout components
        activity.setContentView(R.layout.activity_main);
        menuOverlay = activity.findViewById(R.id.menu_overlay);
        
        Button selectRomBtn = activity.findViewById(R.id.btn_select_rom);
        selectRomBtn.setOnClickListener(v -> activity.openFilePicker());
    }

    public static void attach(MainActivity activity, MenuController controller) {
        // Logic to link with NativeBridge if necessary
    }

    public void toggle() {
        if (menuOverlay.getVisibility() == View.VISIBLE) {
            menuOverlay.setVisibility(View.GONE);
        } else {
            menuOverlay.setVisibility(View.VISIBLE);
        }
    }
}
