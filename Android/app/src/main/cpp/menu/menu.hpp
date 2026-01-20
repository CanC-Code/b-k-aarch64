// File: Android/app/src/main/cpp/menu/menu.hpp
#pragma once
#include <jni.h>

class MenuHandler {
public:
    MenuHandler(JavaVM* vm, jobject activity);
    ~MenuHandler();

    void showMenu();
    void hideMenu();
    void toggleVisibility();
    bool isVisible() const;
    jobject getOverlay() const; // for wrapper loop pause check

private:
    JavaVM* vm_;
    jobject activityGlobal_;
    jobject menuOverlayGlobal_;
    bool visible_ = false;

    void setVisibility(bool visible);
};