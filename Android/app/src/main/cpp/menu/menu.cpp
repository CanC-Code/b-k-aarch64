// File: Android/app/src/main/cpp/menu/menu.cpp
#include "menu.hpp"
#include <android/log.h>
#include <atomic>
#include <unistd.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
static std::atomic<bool> g_paused{false};
static std::atomic<bool> g_menuVisible{false};

// ------------------------------------------------------------
MenuHandler::MenuHandler(JavaVM* vm, jobject activity) : vm_(vm) {
    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);

    activityGlobal_ = env->NewGlobalRef(activity);

    jclass activityCls = env->GetObjectClass(activity);
    jfieldID menuField = env->GetFieldID(activityCls, "menuOverlay", "Landroid/widget/LinearLayout;");
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
    jmethodID setVis = env->GetMethodID(viewCls, "setVisibility", "(I)V");
    env->CallVoidMethod(menuOverlayGlobal_, setVis, visible ? 0 : 8); // VISIBLE / GONE

    visible_ = visible;
    g_menuVisible.store(visible);
    g_paused.store(visible);
}

void MenuHandler::showMenu() { setVisibility(true); }
void MenuHandler::hideMenu() { setVisibility(false); }
void MenuHandler::toggleVisibility() { visible_ ? hideMenu() : showMenu(); }
bool MenuHandler::isVisible() const { return visible_; }
jobject MenuHandler::getOverlay() const { return menuOverlayGlobal_; }

// ------------------------------------------------------------
// JNI
// ------------------------------------------------------------
extern "C" {

static MenuHandler* g_menu = nullptr;
static JavaVM* g_vm = nullptr;

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