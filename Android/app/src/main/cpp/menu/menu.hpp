#pragma once
#include <jni.h>
#include <atomic>

class MenuHandler {
public:
    MenuHandler(JavaVM* vm, jobject activity);
    ~MenuHandler();

    void showMenu();   // show menu and pause emulator
    void hideMenu();   // hide menu and resume emulator
    void toggleVisibility();
    bool isVisible() const;

private:
    JavaVM* vm_;
    jobject activityGlobal_;
    jobject menuOverlayGlobal_;
    std::atomic<bool> visible_{false};

    void setVisibility(bool visible);
};