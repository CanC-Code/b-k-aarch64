#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler::MenuHandler(JavaVM* vm, jobject activity)
    : vm_(vm) {

    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);

    activityGlobal_ = env->NewGlobalRef(activity);

    jclass activityCls = env->GetObjectClass(activity);
    jfieldID menuField =
        env->GetFieldID(activityCls, "menuOverlay", "Landroid/widget/LinearLayout;");

    jobject menuLocal = env->GetObjectField(activity, menuField);
    menuOverlayGlobal_ = env->NewGlobalRef(menuLocal);

    LOGI("MenuHandler initialized");
}

MenuHandler::~MenuHandler() {
    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);

    env->DeleteGlobalRef(menuOverlayGlobal_);
    env->DeleteGlobalRef(activityGlobal_);
}

void MenuHandler::setVisibility(bool visible) {
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);

    jclass viewCls = env->GetObjectClass(menuOverlayGlobal_);
    jmethodID setVis =
        env->GetMethodID(viewCls, "setVisibility", "(I)V");

    env->CallVoidMethod(
        menuOverlayGlobal_,
        setVis,
        visible ? 0 /* View.VISIBLE */ : 8 /* View.GONE */
    );
}

void MenuHandler::showMenu() {
    LOGI("showMenu()");
    setVisibility(true);
}

void MenuHandler::hideMenu() {
    LOGI("hideMenu()");
    setVisibility(false);
}