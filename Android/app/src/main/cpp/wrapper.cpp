#include <jni.h>
#include <cstdint>
#include <thread>
#include <atomic>
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <mutex>
#include <cstdio>

#include "menu/menu.hpp"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {
    void core1_reset(uint8_t* ram);
    void core1_stepCPU(uint8_t* ram);
    void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int w, int h);

    void n_audioInit();
    void n_audioStep();

    void core1_loadOTR(uint8_t* romData, size_t romSize);
}

static constexpr size_t RAM_SIZE = 8 * 1024 * 1024;

static std::vector<uint8_t>  g_ram(RAM_SIZE);
static std::vector<uint32_t> g_framebuffer;

static std::atomic<bool> g_running{false};
static std::atomic<bool> g_paused{false};

static std::thread g_emulationThread;
static std::mutex g_stateMutex;

static JavaVM* g_vm = nullptr;
static MenuHandler* g_menu = nullptr;
static std::atomic<bool> g_menuVisible{false};

static void emulation_loop() {
    LOGI("Emulation thread started");

    n_audioInit();
    core1_reset(g_ram.data());

    while (g_running.load()) {
        if (g_paused.load()) {
            usleep(16 * 1000);
            continue;
        }

        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            core1_stepCPU(g_ram.data());

            if (!g_framebuffer.empty()) {
                core2_stepFrame(
                    g_ram.data(),
                    g_framebuffer.data(),
                    320,
                    240
                );
            }

            n_audioStep();
        }

        usleep(16 * 1000);
    }

    LOGI("Emulation thread exiting");
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(
        JNIEnv*, jclass, jobject activity) {

    if (g_menu) return;
    g_menu = new MenuHandler(g_vm, activity);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(
        JNIEnv*, jclass) {

    if (!g_menu) return;

    bool showing = g_menuVisible.load();
    g_menuVisible.store(!showing);
    g_paused.store(!showing);

    if (!showing) {
        g_menu->showMenu();
        LOGI("Menu shown, emulator paused");
    } else {
        g_menu->hideMenu();
        LOGI("Menu hidden, emulator resumed");
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(
        JNIEnv*, jclass) {

    if (g_running.load()) return;

    g_running.store(true);
    g_paused.store(false);
    g_emulationThread = std::thread(emulation_loop);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stopGameLoop(
        JNIEnv*, jclass) {

    g_running.store(false);
    if (g_emulationThread.joinable())
        g_emulationThread.join();
}

} // extern "C"

JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    return JNI_VERSION_1_6;
}