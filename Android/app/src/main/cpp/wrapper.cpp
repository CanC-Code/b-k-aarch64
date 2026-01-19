#include "menu/menu.hpp"
#include <android/log.h>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <cstdio>
#include <unistd.h>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// External core symbols
// ------------------------------------------------------------
extern "C" {
    void core1_reset(uint8_t* ram);
    void n_audioStep();
}

// ------------------------------------------------------------
// Global emulator state
// ------------------------------------------------------------
static constexpr size_t RAM_SIZE = 8 * 1024 * 1024;
static std::vector<uint8_t> g_ram(RAM_SIZE);
static std::vector<uint32_t> g_framebuffer;
static int g_fbWidth  = 320;
static int g_fbHeight = 240;

static std::atomic<bool> g_running{false};
static std::atomic<bool> g_paused{false};

static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// In-memory OTR
static std::vector<uint8_t> g_OTR;

// ------------------------------------------------------------
// Menu system (native-owned)
// ------------------------------------------------------------
static JavaVM* g_vm = nullptr;
static MenuHandler* g_menu = nullptr;
static std::atomic<bool> g_menuVisible{false};

// ------------------------------------------------------------
// Emulation loop
// ------------------------------------------------------------
static void emulation_loop() {
    core1_reset(g_ram.data());

    while (g_running.load()) {
        if (g_paused.load()) {
            usleep(16 * 1000);
            continue;
        }

        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            n_audioStep();
        }

        usleep(16 * 1000); // ~60Hz
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// Menu JNI hooks
// ------------------------------------------------------------
extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(
        JNIEnv* env, jclass, jobject activity) {

    if (g_menu) return;

    g_menu = new MenuHandler(g_vm, activity);
    LOGI("Native menu initialized");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(
        JNIEnv*, jclass) {

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

} // extern "C"

// ------------------------------------------------------------
// JNI load
// ------------------------------------------------------------
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}