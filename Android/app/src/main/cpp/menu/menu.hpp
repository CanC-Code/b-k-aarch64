#pragma once
#include <jni.h>

class MenuHandler {
public:
    MenuHandler(JavaVM* vm, JNIEnv* env, jobject activity);
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