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
        env->GetFieldID(
            activityCls,
            "menuOverlay",
            "Landroid/widget/LinearLayout;"
        );

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

void MenuHandler::setVisibilityOnUiThread(bool visible) {
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);

    jclass activityCls = env->GetObjectClass(activityGlobal_);
    jmethodID runOnUiThread =
        env->GetMethodID(
            activityCls,
            "runOnUiThread",
            "(Ljava/lang/Runnable;)V"
        );

    jclass runnableCls = env->FindClass("java/lang/Runnable");

    jobject runnable = env->NewObject(
        runnableCls,
        env->GetMethodID(runnableCls, "<init>", "()V")
    );

    jclass viewCls = env->GetObjectClass(menuOverlayGlobal_);
    jmethodID setVis =
        env->GetMethodID(viewCls, "setVisibility", "(I)V");

    jint visibility = visible ? 0 : 8; // VISIBLE / GONE
    env->CallVoidMethod(menuOverlayGlobal_, setVis, visibility);
}

void MenuHandler::showMenu() {
    LOGI("showMenu()");
    setVisibilityOnUiThread(true);
}

void MenuHandler::hideMenu() {
    LOGI("hideMenu()");
    setVisibilityOnUiThread(false);
}