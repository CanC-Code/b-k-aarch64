#pragma once
#include <jni.h>

class MenuHandler {
public:
    MenuHandler(JNIEnv* env, jobject activity);
    ~MenuHandler();

    void showMenu();
    void hideMenu();
    bool isMenuVisible() const;

private:
    JNIEnv* env_;
    jobject activity_;
    jclass activityClass_;
    jobject menuOverlay_;

    void callJavaVisibility(bool visible);
};