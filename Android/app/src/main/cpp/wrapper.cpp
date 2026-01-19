#include "menu.hpp"
#include <atomic>
#include <thread>
#include <vector>
#include <android/log.h>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ----------------------------
// Global state
// ----------------------------
static JavaVM* g_vm = nullptr;
static MenuHandler* g_menu = nullptr;
static std::atomic<bool> g_menuVisible{false};
static std::atomic<bool> g_paused{false};

// Emulation state omitted for brevity ...

extern "C" {

// ----------------------------
// Menu JNI hooks
// ----------------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeToggleMenu(JNIEnv*, jclass) {
    if (!g_menu) return;

    if (!g_menuVisible.load()) {
        g_menuVisible.store(true);
        g_paused.store(true);
        g_menu->showMenu();
        LOGI("Menu shown, emulator paused");
    } else {
        g_menuVisible.store(false);
        g_paused.store(false);
        g_menu->hideMenu();
        LOGI("Menu hidden, emulator resumed");
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeMenu_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (g_menu) return;
    g_menu = new MenuHandler(g_vm, activity);
    LOGI("Native menu initialized");
}

// ----------------------------
// JNI load
// ----------------------------
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}

} // extern "C"