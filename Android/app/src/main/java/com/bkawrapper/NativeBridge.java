package com.bkawrapper;

import com.bkawrapper.menu.MenuController;

public class NativeBridge {

    static {
        System.loadLibrary("bk_native");
    }

    private static MenuController menuController;

    public static void setMenuController(MenuController controller) {
        menuController = controller;
    }

    // Called from native
    public static void showMenu() {
        if (menuController != null) {
            menuController.show();
        }
    }

    public static void hideMenu() {
        if (menuController != null) {
            menuController.hide();
        }
    }

    public static native void nativeResumeGame();
    public static native void nativeQuitGame();
}