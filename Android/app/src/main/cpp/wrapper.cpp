#include <jni.h>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <android/log.h>
#include <unistd.h>

#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// Emulator stubs
extern "C" {
    void core1_reset(uint8_t* ram);
    void n_audioStep();
}

// ------------------------------------------------------------
// Global state
static std::vector<uint8_t> g_ram(8 * 1024 * 1024);
static std::atomic<bool> g_running{false};
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// Menu
static MenuHandler* g_menu = nullptr;
static JavaVM* g_vm = nullptr;

// ------------------------------------------------------------
static void emulation_loop() {
    core1_reset(g_ram.data());

    while (g_running.load()) {
        if (g_menu && g_menu->isVisible()) {
            usleep(16 * 1000);
            continue;
        }

        std::lock_guard<std::mutex> lock(g_stateMutex);
        n_audioStep();
        usleep(16 * 1000);
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI
extern "C" {

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass, jobject activity) {
    if (!g_menu) {
        g_menu = new MenuHandler(g_vm, env, activity);
        LOGI("Native menu initialized");
    }
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    if (g_running.load()) return;
    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game loop paused");
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv*, jclass) {
    if (g_running.load()) return;
    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop resumed");
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game cleaned up");
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv*, jclass) {
    if (g_menu) g_menu->toggleVisibility();
}

// JNI_OnLoad
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}

} // extern "C"