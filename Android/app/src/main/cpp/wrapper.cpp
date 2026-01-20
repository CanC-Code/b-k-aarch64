#include "menu/menu.hpp"
#include <android/log.h>
#include <atomic>
#include <thread>
#include <vector>
#include <mutex>
#include <unistd.h>

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

extern "C" {
    void core1_reset(uint8_t* ram);
    void n_audioStep();
}

static MenuHandler* g_menu = nullptr;

// ------------------------------------------------------------
// Emulation loop
static void emulation_loop() {
    core1_reset(g_ram.data());

    while (g_running.load()) {
        // pause if menu visible
        if (g_menu && g_menu->isVisible()) {
            usleep(16 * 1000);
            continue;
        }

        std::lock_guard<std::mutex> lock(g_stateMutex);
        n_audioStep();
        usleep(16 * 1000);
    }
}

// ------------------------------------------------------------
// JNI API
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {
    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv*, jclass) {
    if (g_menu) g_menu->showMenu();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv*, jclass) {
    if (g_menu) g_menu->hideMenu();
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    g_running.store(false);
    if (g_emulationThread.joinable()) g_emulationThread.join();
    LOGI("Game cleaned up");
}

} // extern "C"