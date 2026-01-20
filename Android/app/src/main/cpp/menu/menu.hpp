// File: Android/app/src/main/cpp/menu/menu.hpp

#pragma once
#include <jni.h>
#include <atomic>

class MenuHandler {
public:
    MenuHandler(JavaVM* vm, jobject activity);
    ~MenuHandler();

    void showMenu();
    void hideMenu();
    void toggleVisibility();
    bool isVisible() const;

private:
    JavaVM* vm_;
    jobject activityGlobal_;
    jobject menuOverlayGlobal_;
    bool visible_ = false;

    void setVisibility(bool visible);
};