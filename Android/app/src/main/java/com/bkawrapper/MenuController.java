package com.bkawrapper;

import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

public class MenuController {
    private final MainActivity activity;
    private final LinearLayout menuOverlay;

    public MenuController(MainActivity activity) {
        this.activity = activity;
        this.menuOverlay = activity.findViewById(R.id.menu_overlay);
        setupUI();
    }

    private void setupUI() {
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

    public void hide() {
        if (menuOverlay != null) menuOverlay.setVisibility(View.GONE);
    }
}
