package com.bkawrapper;

import android.app.Activity;
import android.view.View;
import android.widget.LinearLayout;

public class Menu {

    private final LinearLayout menuOverlay;

    public Menu(Activity activity, LinearLayout menuOverlay) {
        this.menuOverlay = menuOverlay;

        // Initialize native menu system with the overlay view
        NativeMenu.nativeInitMenu(menuOverlay);

        setupButtons();
    }

    private void setupButtons() {
        View resumeButton = menuOverlay.findViewById(R.id.menu_resume);
        View pauseButton  = menuOverlay.findViewById(R.id.menu_pause);

        if (resumeButton != null) {
            resumeButton.setOnClickListener(v -> {
                NativeMenu.nativeResumeEmulator();
                menuOverlay.setVisibility(View.GONE);
            });
        }

        if (pauseButton != null) {
            pauseButton.setOnClickListener(v -> {
                NativeMenu.nativePauseEmulator();
            });
        }
    }

    public void show() {
        menuOverlay.setVisibility(View.VISIBLE);
    }

    public void hide() {
        menuOverlay.setVisibility(View.GONE);
    }
}