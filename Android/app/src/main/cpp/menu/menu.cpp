#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler::MenuHandler(JNIEnv* env, jobject activity)
    : env_(env), activity_(activity) {

    activityClass_ = env_->GetObjectClass(activity_);

    jfieldID menuId = env_->GetFieldID(activityClass_, "menuOverlay", "Landroid/widget/LinearLayout;");
    menuOverlay_ = env_->GetObjectField(activity_, menuId);

    LOGI("MenuHandler initialized");
}

MenuHandler::~MenuHandler() {
    menuOverlay_ = nullptr;
    activityClass_ = nullptr;
}

void MenuHandler::callJavaVisibility(bool visible) {
    if (!menuOverlay_) return;

    jclass cls = env_->GetObjectClass(menuOverlay_);
    jmethodID setVis = env_->GetMethodID(cls, "setVisibility", "(I)V");

    env_->CallVoidMethod(menuOverlay_, setVis, visible ? 0 /*View.VISIBLE*/ : 8 /*View.GONE*/);
}

void MenuHandler::showMenu() {
    LOGI("Showing menu");
    callJavaVisibility(true);
}

void MenuHandler::hideMenu() {
    LOGI("Hiding menu");
    callJavaVisibility(false);
}

bool MenuHandler::isMenuVisible() const {
    return false; // Optional: can implement via JNI if needed
}