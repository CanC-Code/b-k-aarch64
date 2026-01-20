package com.bkawrapper;

import android.view.View;
import android.widget.Button;

public final class MenuController {

    private final View menuView;
    private boolean visible = false;

    public MenuController(View menuView) {
        this.menuView = menuView;
        this.menuView.setVisibility(View.GONE);

        Button resume = menuView.findViewById(R.id.menu_resume);
        Button quit   = menuView.findViewById(R.id.menu_quit);

        resume.setOnClickListener(v -> hide());
        quit.setOnClickListener(v -> android.os.Process.killProcess(android.os.Process.myPid()));
    }

    public boolean onBackPressed() {
        if (visible) {
            hide();
            return true;
        } else {
            show();
            return true;
        }
    }

    private void show() {
        visible = true;
        menuView.setVisibility(View.VISIBLE);
        NativeBridge.pauseGameLoop();
    }

    private void hide() {
        visible = false;
        menuView.setVisibility(View.GONE);
        NativeBridge.resumeGameLoop();
    }
}