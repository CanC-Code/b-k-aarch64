package com.bkawrapper;

import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;

public class MenuController {
    private final MainActivity activity;
    private final LinearLayout menuOverlay;

    public MenuController(MainActivity activity) {
        this.activity = activity;
        // Reference the overlay already in the layout
        this.menuOverlay = activity.findViewById(R.id.menu_overlay);
        
        Button selectBtn = activity.findViewById(R.id.btn_select_rom);
        if (selectBtn != null) {
            selectBtn.setOnClickListener(v -> activity.openFilePicker());
        }
    }

    public void toggle() {
        if (menuOverlay != null) {
            int vis = (menuOverlay.getVisibility() == View.VISIBLE) ? View.GONE : View.VISIBLE;
            menuOverlay.setVisibility(vis);
        }
    }

    public void hide() {
        if (menuOverlay != null) menuOverlay.setVisibility(View.GONE);
    }
}
