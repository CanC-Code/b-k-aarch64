#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler::MenuHandler(JavaVM* vm, jobject activity) : vm_(vm) {
    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);

    activityGlobal_ = env->NewGlobalRef(activity);
    jclass cls = env->GetObjectClass(activity);
    jfieldID fid = env->GetFieldID(cls, "menuOverlay", "Landroid/widget/LinearLayout;");
    jobject menuObj = env->GetObjectField(activity, fid);
    menuOverlayGlobal_ = env->NewGlobalRef(menuObj);

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

    jclass cls = env->GetObjectClass(menuOverlayGlobal_);
    jmethodID mid = env->GetMethodID(cls, "setVisibility", "(I)V");
    env->CallVoidMethod(menuOverlayGlobal_, mid, visible ? 0 : 8); // VISIBLE / GONE

    visible_ = visible;
    vm_->DetachCurrentThread();
}

void MenuHandler::showMenu() { setVisibility(true); }
void MenuHandler::hideMenu() { setVisibility(false); }
void MenuHandler::toggleVisibility() { isVisible() ? hideMenu() : showMenu(); }
bool MenuHandler::isVisible() const { return visible_; }