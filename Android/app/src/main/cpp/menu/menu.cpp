// File: Android/app/src/main/cpp/menu/menu.cpp

#include "menu.hpp"
#include <android/log.h>
#include <unistd.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Global JNI references
static MenuHandler* g_menu = nullptr;
static JavaVM* g_vm = nullptr;

// --------------------------
MenuHandler::MenuHandler(JavaVM* vm, jobject activity)
    : vm_(vm)
{
    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);

    activityGlobal_ = env->NewGlobalRef(activity);
    jclass cls = env->GetObjectClass(activity);
    jfieldID fid = env->GetFieldID(cls, "menuOverlay", "Landroid/widget/LinearLayout;");
    menuOverlayGlobal_ = env->NewGlobalRef(env->GetObjectField(activity, fid));

    visible_ = false;
    LOGI("MenuHandler initialized");
}

MenuHandler::~MenuHandler() {}

void MenuHandler::setVisibility(bool visible) {
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);

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
    if (!g_menu) g_menu = new MenuHandler(g_vm, activity);
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad bk_wrapper");
    return JNI_VERSION_1_6;
}

} // extern "C"