#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler::MenuHandler(JavaVM* vm, jobject activity)
    : vm_(vm) {

    JNIEnv* env = nullptr;
    vm_->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6);

    activityGlobal_ = env->NewGlobalRef(activity);
    LOGI("MenuHandler initialized");
}

MenuHandler::~MenuHandler() {
    JNIEnv* env = nullptr;
    vm_->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6);

    if (activityGlobal_) {
        env->DeleteGlobalRef(activityGlobal_);
        activityGlobal_ = nullptr;
    }
}

void MenuHandler::callJava(const char* methodName) {
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);

    jclass cls = env->GetObjectClass(activityGlobal_);
    jmethodID mid = env->GetMethodID(cls, methodName, "()V");

    if (mid) {
        env->CallVoidMethod(activityGlobal_, mid);
    } else {
        LOGI("Method not found: %s", methodName);
    }

    env->DeleteLocalRef(cls);
}

void MenuHandler::showMenu() {
    LOGI("Request show menu");
    callJava("showMenuFromNative");
}

void MenuHandler::hideMenu() {
    LOGI("Request hide menu");
    callJava("hideMenuFromNative");
}