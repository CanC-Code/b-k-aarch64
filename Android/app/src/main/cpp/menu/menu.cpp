#include "menu.hpp"
#include <android/log.h>

#define LOG_TAG "MENU_HANDLER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

MenuHandler::MenuHandler(JavaVM* vm, jobject activity)
    : vm_(vm)
{
    JNIEnv* env = nullptr;
    vm_->GetEnv((void**)&env, JNI_VERSION_1_6);

    // Store global references
    activityGlobal_ = env->NewGlobalRef(activity);

    jclass activityCls = env->GetObjectClass(activity);
    jfieldID overlayField = env->GetFieldID(activityCls, "menuOverlay", "Landroid/widget/LinearLayout;");
    menuOverlayGlobal_ = env->NewGlobalRef(env->GetObjectField(activity, overlayField));

    visible_ = false;
}

MenuHandler::~MenuHandler() {
    if (!vm_ || !activityGlobal_) return;

    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);
    if (menuOverlayGlobal_) env->DeleteGlobalRef(menuOverlayGlobal_);
    if (activityGlobal_) env->DeleteGlobalRef(activityGlobal_);
}

void MenuHandler::setVisibility(bool visible) {
    JNIEnv* env = nullptr;
    vm_->AttachCurrentThread(&env, nullptr);

    jclass overlayCls = env->GetObjectClass(menuOverlayGlobal_);
    jmethodID setVis = env->GetMethodID(overlayCls, "setVisibility", "(I)V");
    env->CallVoidMethod(menuOverlayGlobal_, setVis, visible ? 0 : 8); // VISIBLE : GONE

    visible_.store(visible);
}

void MenuHandler::showMenu() {
    setVisibility(true);
}

void MenuHandler::hideMenu() {
    setVisibility(false);
}

void MenuHandler::toggleVisibility() {
    if (isVisible()) hideMenu();
    else showMenu();
}

bool MenuHandler::isVisible() const {
    return visible_.load();
}

// ------------------------------------------------------------
// JNI Hooks
extern "C" {

static MenuHandler* g_menu = nullptr;
static JavaVM* g_vm = nullptr;

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (!g_menu) g_menu = new MenuHandler(g_vm, activity);
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