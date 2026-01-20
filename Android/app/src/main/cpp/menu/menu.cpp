// File: Android/app/src/main/cpp/menu/menu.cpp
#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MenuHandler"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler* g_menu = nullptr;

MenuHandler::MenuHandler(JavaVM* vm, jobject activity)
    : m_vm(vm)
{
    JNIEnv* env = nullptr;
    vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6);
    m_activity = env->NewGlobalRef(activity);

    LOGI("MenuHandler created");
}

MenuHandler::~MenuHandler() {
    JNIEnv* env = nullptr;
    m_vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6);
    env->DeleteGlobalRef(m_activity);
}

void MenuHandler::toggleVisibility() {
    LOGI("Menu toggle requested (UI side handles actual visibility)");
}

// JNI entry points

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeToggleMenu(JNIEnv*, jclass) {
    if (g_menu) {
        g_menu->toggleVisibility();
    }
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    JavaVM* vm = nullptr;
    env->GetJavaVM(&vm);

    if (!g_menu) {
        g_menu = new MenuHandler(vm, activity);
    }
}