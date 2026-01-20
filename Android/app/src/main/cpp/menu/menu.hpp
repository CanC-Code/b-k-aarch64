// File: Android/app/src/main/cpp/menu/menu.hpp
#pragma once

#include <jni.h>

class MenuHandler {
public:
    MenuHandler(JavaVM* vm, jobject activity);
    ~MenuHandler();

    void toggleVisibility();

private:
    JavaVM* m_vm;
    jobject m_activity;
};

// Global menu instance
extern MenuHandler* g_menu;