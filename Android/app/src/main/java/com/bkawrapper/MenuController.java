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
        // UI is already inflated by MainActivity.onCreate
        menuOverlay = activity.findViewById(R.id.menu_overlay);
        
        Button selectRomBtn = activity.findViewById(R.id.btn_select_rom);
        if (selectRomBtn != null) {
            selectRomBtn.setOnClickListener(v -> activity.openFilePicker());
        }
    }

    public void toggle() {
        if (menuOverlay != null) {
            int visibility = (menuOverlay.getVisibility() == View.VISIBLE) ? View.GONE : View.VISIBLE;
            menuOverlay.setVisibility(visibility);
        }
    }
}
