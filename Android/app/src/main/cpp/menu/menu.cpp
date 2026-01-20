#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler::MenuHandler(JavaVM* vm, jobject activity)
    : vm_(vm) {

    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);

    jclass cls = env->GetObjectClass(activity);
    jfieldID fid = env->GetFieldID(
        cls, "menuOverlay", "Landroid/widget/LinearLayout;");

    jobject overlay = env->GetObjectField(activity, fid);
    menuOverlayGlobal_ = env->NewGlobalRef(overlay);

    LOGI("MenuHandler created");
}

MenuHandler::~MenuHandler() {
    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);
    env->DeleteGlobalRef(menuOverlayGlobal_);
}

void MenuHandler::setVisibility(bool visible) {
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);

    jclass viewCls = env->GetObjectClass(menuOverlayGlobal_);
    jmethodID setVis = env->GetMethodID(viewCls, "setVisibility", "(I)V");

    env->CallVoidMethod(menuOverlayGlobal_, setVis, visible ? 0 : 8);
    visible_ = visible;
}

void MenuHandler::toggleVisibility() {
    setVisibility(!visible_);
}

bool MenuHandler::isVisible() const {
    return visible_;
}