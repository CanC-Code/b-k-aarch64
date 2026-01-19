#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler::MenuHandler(JNIEnv* env, jobject menuOverlay) {
    menuOverlayGlobal_ = env->NewGlobalRef(menuOverlay);

    jclass viewCls = env->GetObjectClass(menuOverlayGlobal_);
    setVisibility_ = env->GetMethodID(viewCls, "setVisibility", "(I)V");

    LOGI("MenuHandler initialized");
}

MenuHandler::~MenuHandler() {
    // JVM owns thread here; safe
}

void MenuHandler::show() {
    JNIEnv* env;
    JavaVM* vm;
    env->GetJavaVM(&vm);
    vm->GetEnv((void**)&env, JNI_VERSION_1_6);

    env->CallVoidMethod(menuOverlayGlobal_, setVisibility_, 0); // VISIBLE
}

void MenuHandler::hide() {
    JNIEnv* env;
    JavaVM* vm;
    env->GetJavaVM(&vm);
    vm->GetEnv((void**)&env, JNI_VERSION_1_6);

    env->CallVoidMethod(menuOverlayGlobal_, setVisibility_, 8); // GONE
}