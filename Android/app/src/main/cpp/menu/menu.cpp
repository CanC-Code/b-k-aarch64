#include "menu.hpp"
#include <android/log.h>
#include <unistd.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
static MenuHandler* g_menu = nullptr;
static JavaVM* g_vm = nullptr;

MenuHandler::MenuHandler(JavaVM* vm, jobject activity) : vm_(vm) {
    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);
    activityGlobal_ = env->NewGlobalRef(activity);

    jclass activityCls = env->GetObjectClass(activityGlobal_);
    jfieldID menuField = env->GetFieldID(activityCls, "menu_overlay", "Landroid/widget/LinearLayout;");
    menuOverlayGlobal_ = env->NewGlobalRef(env->GetObjectField(activityGlobal_, menuField));
}

MenuHandler::~MenuHandler() {
    if (!vm_) return;
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);
    env->DeleteGlobalRef(activityGlobal_);
    env->DeleteGlobalRef(menuOverlayGlobal_);
}

void MenuHandler::setVisibility(bool visible) {
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);

    jclass viewCls = env->GetObjectClass(menuOverlayGlobal_);
    jmethodID setVis = env->GetMethodID(viewCls, "setVisibility", "(I)V");
    env->CallVoidMethod(menuOverlayGlobal_, setVis, visible ? 0 /* VISIBLE */ : 8 /* GONE */);

    visible_ = visible;
}

void MenuHandler::showMenu() { setVisibility(true); }
void MenuHandler::hideMenu() { setVisibility(false); }
void MenuHandler::toggleVisibility() { isVisible() ? hideMenu() : showMenu(); }
bool MenuHandler::isVisible() const { return visible_; }

// ------------------------------------------------------------
// JNI hooks
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (!g_menu)
        g_menu = new MenuHandler(g_vm, activity);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv*, jclass) {
    if (!g_menu) return;
    g_menu->toggleVisibility();
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}

} // extern "C"