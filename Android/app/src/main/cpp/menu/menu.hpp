#pragma once
#include <jni.h>

class MenuHandler {
public:
    MenuHandler(JavaVM* vm, jobject activity);
    ~MenuHandler();

    void showMenu();
    void hideMenu();
    void toggleMenu();      // NEW

private:
    JavaVM* vm_;
    jobject activityGlobal_;
    jobject menuOverlayGlobal_;
    bool visible_ = false; // track menu state

    void setVisibility(bool visible);
};