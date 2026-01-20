// File: Android/app/src/main/cpp/wrapper.cpp
#include <vector>
#include <mutex>
#include <thread>
#include <atomic>
#include <unistd.h>
#include <android/log.h>
#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// Emulation state
// ------------------------------------------------------------
static std::atomic<bool> g_running{false};
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

static std::vector<uint8_t> g_ram(8 * 1024 * 1024);
static std::vector<uint32_t> g_framebuffer;
static int g_fbWidth = 320;
static int g_fbHeight = 240;

static MenuHandler* g_menu = nullptr;
static JavaVM* g_vm = nullptr;

// ------------------------------------------------------------
// Emulation loop
// ------------------------------------------------------------
static void emulation_loop() {
    LOGI("Emulation thread started");

    while (g_running.load()) {
        // Pause automatically if menu visible
        if (g_menu && g_menu->isVisible()) {
            usleep(16 * 1000);
            continue;
        }

        std::lock_guard<std::mutex> lock(g_stateMutex);

        // Audio / core step stubs
        // n_audioStep();
        // core_step...

        usleep(16 * 1000);
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI
// ------------------------------------------------------------
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game cleaned up");
}

// Menu hooks
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