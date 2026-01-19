#pragma once
#include <jni.h>

class MenuHandler {
public:
    MenuHandler(JNIEnv* env, jobject menuOverlay);
    ~MenuHandler();

    void show();
    void hide();

private:
    jobject menuOverlayGlobal_;
    jmethodID setVisibility_;
};