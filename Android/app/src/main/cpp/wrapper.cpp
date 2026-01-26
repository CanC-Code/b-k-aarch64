#include <jni.h>
#include <thread>
#include <atomic>
#include <vector>
#include <android/log.h>
#include <unistd.h>
#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static JavaVM* g_vm = nullptr;
static MenuHandler* g_menu = nullptr;
static std::atomic<bool> g_running{false};
static std::thread g_thread;

extern "C" void n_audioStep();
extern "C" void core1_reset(uint8_t*);

static std::vector<uint8_t> g_ram(8 * 1024 * 1024);

static void emuLoop() {
    core1_reset(g_ram.data());

    while (g_running.load()) {
        if (!g_menu || !g_menu->isVisible()) {
            n_audioStep();
        }
        usleep(16000);
    }
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(
        JNIEnv* env, jclass, jobject activity) {
    if (!g_menu) {
        g_menu = new MenuHandler(g_vm, activity);
        LOGI("Menu initialized");
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(
        JNIEnv*, jclass) {
    if (g_menu) g_menu->toggleVisibility();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(
        JNIEnv*, jclass) {
    g_running.store(true);
    g_thread = std::thread(emuLoop);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(
        JNIEnv*, jclass) {
    g_running.store(false);
    if (g_thread.joinable()) g_thread.join();
}

JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad OK");
    return JNI_VERSION_1_6;
}

}