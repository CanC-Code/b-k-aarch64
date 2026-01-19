#include <vector>
#include <atomic>
#include <thread>
#include <mutex>
#include <cstdio>
#include <unistd.h>
#include <android/log.h>

#include "menu/menu.hpp"

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
static std::thread g_emulationThread;
static std::mutex g_stateMutex;

// In-memory OTR (NOTE: builder currently owns real data)
static std::vector<uint8_t> g_OTR;

// ------------------------------------------------------------
// Menu system (native-owned)
// ------------------------------------------------------------
static JavaVM* g_vm = nullptr;
static MenuHandler* g_menu = nullptr;

// ------------------------------------------------------------
// Emulation loop
// ------------------------------------------------------------
static void emulation_loop() {
    core1_reset(g_ram.data());

    while (g_running.load()) {
        // Pause emulation while menu is visible
        if (g_menu) {
            // Attach thread for JNI check
            JNIEnv* env = nullptr;
            g_vm->AttachCurrentThread(&env, nullptr);

            jclass menuCls = env->GetObjectClass(g_menu);
            jmethodID isVisibleMethod = env->GetMethodID(menuCls, "isVisible", "()Z");
            jboolean menuVisible = env->CallBooleanMethod(reinterpret_cast<jobject>(g_menu), isVisibleMethod);
            if (menuVisible) {
                usleep(16 * 1000);
                continue;
            }
        }

        {
            std::lock_guard<std::mutex> lock(g_stateMutex);
            // Main emulation step
            n_audioStep();
        }

        // ~60Hz pacing
        usleep(16 * 1000);
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI Exports
// ------------------------------------------------------------
extern "C" {

JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTRData(JNIEnv* env, jclass) {
    jbyteArray out = env->NewByteArray(static_cast<jsize>(g_OTR.size()));
    if (!out || g_OTR.empty()) return out;

    env->SetByteArrayRegion(out, 0,
        static_cast<jsize>(g_OTR.size()),
        reinterpret_cast<jbyte*>(g_OTR.data())
    );

    return out;
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(JNIEnv* env, jclass, jstring path) {
    const char* cpath = env->GetStringUTFChars(path, nullptr);
    FILE* f = fopen(cpath, "wb");
    if (!f) {
        env->ReleaseStringUTFChars(path, cpath);
        LOGI("Failed to save BK.OTR: cannot open file");
        return;
    }

    fwrite(g_OTR.data(), 1, g_OTR.size(), f);
    fclose(f);
    env->ReleaseStringUTFChars(path, cpath);

    LOGI("Saved BK.OTR: %zu bytes", g_OTR.size());
}

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

// ------------------------------------------------------------
// Menu JNI hooks
// ------------------------------------------------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass, jobject activity) {
    if (g_menu) return;

    g_menu = new MenuHandler(g_vm, activity);
    LOGI("Native menu initialized");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv*, jclass) {
    if (!g_menu) return;

    // Simply toggle menu visibility
    // Emulation pause/resume is managed in emulation loop based on visibility
    g_menu->showMenu();  // or hideMenu() can be called via Java swipe/back logic
}

} // extern "C"

// ------------------------------------------------------------
// JNI load
// ------------------------------------------------------------
JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM* vm, void*) {
    g_vm = vm;
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}