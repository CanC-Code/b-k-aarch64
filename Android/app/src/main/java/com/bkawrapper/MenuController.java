package com.bkawrapper;

import android.view.View;
import android.widget.Button;

public class MenuController {
    private final MainActivity activity;
    private final View menuOverlay;

    public MenuController(MainActivity activity) {
        this.activity = activity;
        this.menuOverlay = activity.findViewById(R.id.menu_overlay);
        
        Button selectBtn = activity.findViewById(R.id.btn_select_rom);
        if (selectBtn != null) {
            selectBtn.setOnClickListener(v -> activity.openFilePicker());
        }
    }

    public void show() {
        if (menuOverlay != null) menuOverlay.setVisibility(View.VISIBLE);
    }

    public void hide() {
        if (menuOverlay != null) menuOverlay.setVisibility(View.GONE);
    }

    public void toggle() {
        if (menuOverlay != null) {
            if (menuOverlay.getVisibility() == View.VISIBLE) hide();
            else show();
        }
    }
}
