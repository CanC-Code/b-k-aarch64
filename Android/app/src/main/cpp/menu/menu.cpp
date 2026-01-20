// File: Android/app/src/main/cpp/menu/menu.cpp

#include "menu.hpp"
#include <android/log.h>
#include <unistd.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Global JNI reference from wrapper.cpp
extern JavaVM* g_vm;

// --------------------------
MenuHandler::MenuHandler(JNIEnv* env, jobject activity)
{
    activityGlobal_ = env->NewGlobalRef(activity);
    jclass cls = env->GetObjectClass(activity);
    jfieldID fid = env->GetFieldID(cls, "menuOverlay", "Landroid/widget/LinearLayout;");
    menuOverlayGlobal_ = env->NewGlobalRef(env->GetObjectField(activity, fid));

    visible_ = false;
    LOGI("MenuHandler initialized");
}

MenuHandler::~MenuHandler() {
    if (activityGlobal_) {
        JNIEnv* env = nullptr;
        g_vm->AttachCurrentThread(&env, nullptr);
        env->DeleteGlobalRef(activityGlobal_);
    }
    if (menuOverlayGlobal_) {
        JNIEnv* env = nullptr;
        g_vm->AttachCurrentThread(&env, nullptr);
        env->DeleteGlobalRef(menuOverlayGlobal_);
    }
}

void MenuHandler::setVisibility(bool visible) {
    JNIEnv* env = nullptr;
    g_vm->AttachCurrentThread(&env, nullptr);

    jclass cls = env->GetObjectClass(menuOverlayGlobal_);
    jmethodID setVis = env->GetMethodID(cls, "setVisibility", "(I)V");
    env->CallVoidMethod(menuOverlayGlobal_, setVis, visible ? 0 /*VISIBLE*/ : 8 /*GONE*/);

    visible_ = visible;
}

void MenuHandler::showMenu() { setVisibility(true); }
void MenuHandler::hideMenu() { setVisibility(false); }
void MenuHandler::toggleVisibility() {
    if (isVisible()) hideMenu();
    else showMenu();
}
bool MenuHandler::isVisible() const { return visible_; }

// --------------------------
// JNI exports
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeToggleMenu(JNIEnv*, jclass) {
    if (g_menu) g_menu->toggleVisibility();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativePauseEmulator(JNIEnv*, jclass) {
    // Pause emulator if needed
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeResumeEmulator(JNIEnv*, jclass) {
    // Resume emulator if needed
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (!g_menu) g_menu = new MenuHandler(env, activity);
}

} // extern "C"