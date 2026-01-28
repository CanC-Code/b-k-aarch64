package com.bkawrapper;

import android.view.View;
import android.widget.Button;

public class MenuController {
    private final MainActivity activity;

    public MenuController(MainActivity activity) {
        this.activity = activity;
        setupListeners();
    }

    private void setupListeners() {
        // Find your select button by ID (ensure this exists in your layout)
        View selectBtn = activity.findViewById(R.id.button_select_rom);
        if (selectBtn != null) {
            selectBtn.setOnClickListener(v -> {
                activity.openFilePicker();
            });
        }
    }
}
