#pragma once
#include <jni.h>

class MenuHandler {
public:
    MenuHandler(JavaVM* vm, jobject activity);
    ~MenuHandler();

    void showMenu();
    void hideMenu();

private:
    JavaVM* vm_;
    jobject activityGlobal_;

    void callJava(const char* methodName);
};