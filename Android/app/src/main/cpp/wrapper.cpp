// File: Android/app/src/main/cpp/wrapper.cpp

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
// Global emulator state
// ------------------------------------------------------------
static constexpr size_t RAM_SIZE = 8 * 1024 * 1024;
static std::vector<uint8_t> g_ram(RAM_SIZE);
static std::vector<uint32_t> g_framebuffer;
static int g_fbWidth  = 320;
static int g_fbHeight = 240;

static std::atomic<bool> g_running{false};
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// ------------------------------------------------------------
// Menu
// ------------------------------------------------------------
JavaVM* g_vm = nullptr;
MenuHandler* g_menu = nullptr;

// ------------------------------------------------------------
// Emulation loop (stub for now)
// ------------------------------------------------------------
static void emulation_loop() {
    core1_reset(g_ram.data());

    while (g_running.load()) {
        // Pause automatically if menu is visible
        if (g_menu && g_menu->isVisible()) {
            usleep(16 * 1000);
            continue;
        }

        {
            std::lock_guard<std::mutex> lock(g_stateMutex);

            // TODO: actual CPU/frame/audio steps
            n_audioStep();
        }

        usleep(16 * 1000); // ~60fps sleep for stub
    }
}

// ------------------------------------------------------------
// JNI functions
// ------------------------------------------------------------
extern "C" {

// ----------------------
// ROM / Game control stubs
// ----------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    if (g_running.load()) return;
    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game loop paused");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv*, jclass) {
    if (g_running.load()) return;
    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop resumed");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game cleaned up");
}

// ----------------------
// Menu initialization
// ----------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (!g_menu) {
        g_menu = new MenuHandler(env, activity);
        LOGI("Menu initialized from NativeBridge");
    }
}

// ----------------------
// Toggle menu visibility
// ----------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv*, jclass) {
    if (g_menu) g_menu->toggleVisibility();
}

// ----------------------
// JNI_OnLoad
// ----------------------
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad bk_wrapper");
    return JNI_VERSION_1_6;
}

} // extern "C"