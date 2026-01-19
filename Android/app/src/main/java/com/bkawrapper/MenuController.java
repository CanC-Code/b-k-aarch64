package com.bkawrapper.menu;

public class MenuController {

    private final MenuOverlayView menuView;
    private boolean visible = false;

    public MenuController(MenuOverlayView menuView) {
        this.menuView = menuView;
    }

    public void toggle() {
        if (visible) {
            hide();
        } else {
            show();
        }
    }

    public void show() {
        visible = true;
        menuView.show();
    }

    public void hide() {
        visible = false;
        menuView.hide();
    }

    public boolean isVisible() {
        return visible;
    }
}