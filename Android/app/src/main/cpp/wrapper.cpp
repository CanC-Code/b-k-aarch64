#include <jni.h>
#include <cstdint>
#include <thread>
#include <atomic>
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <mutex>
#include <cstdio>

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// External core symbols (real or stubbed elsewhere)
// ------------------------------------------------------------
extern "C" {

void core1_reset(uint8_t* ram);
void core1_stepCPU(uint8_t* ram);
void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int w, int h);

void n_audioInit();
void n_audioStep();

void core1_loadOTR(uint8_t* romData, size_t romSize);

}

// ------------------------------------------------------------
// Global state
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
// In-memory OTR
// ------------------------------------------------------------
static std::vector<uint8_t> g_OTR;

// ------------------------------------------------------------
// Emulation loop
// ------------------------------------------------------------
static void emulation_loop() {
    LOGI("Emulation thread started");

    n_audioInit();
    core1_reset(g_ram.data());

    while (g_running.load()) {
        {
            std::lock_guard<std::mutex> lock(g_stateMutex);

            core1_stepCPU(g_ram.data());

            if (!g_framebuffer.empty()) {
                core2_stepFrame(
                    g_ram.data(),
                    g_framebuffer.data(),
                    g_fbWidth,
                    g_fbHeight
                );
            }

            n_audioStep();
        }

        // ~60Hz pacing
        usleep(16 * 1000);
    }

    LOGI("Emulation thread exiting");
}

// ------------------------------------------------------------
// JNI API (matches NativeBridge.java)
// ------------------------------------------------------------
extern "C" {

// Load ROM bytes into RAM
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(
        JNIEnv* env, jclass, jbyteArray romData) {

    if (!romData) return;

    jsize len = env->GetArrayLength(romData);
    if (len > RAM_SIZE) len = RAM_SIZE;

    env->GetByteArrayRegion(
        romData, 0, len,
        reinterpret_cast<jbyte*>(g_ram.data())
    );

    LOGI("ROM loaded: %d bytes", len);
}

// Process ROM → OTR
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv*, jclass) {

    core1_loadOTR(g_ram.data(), g_ram.size());
    LOGI("OTR processing complete");
}

// Access in-memory OTR
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTRData(
        JNIEnv* env, jclass) {

    jbyteArray out = env->NewByteArray(static_cast<jsize>(g_OTR.size()));
    if (!out || g_OTR.empty()) return out;

    env->SetByteArrayRegion(out, 0, static_cast<jsize>(g_OTR.size()),
                            reinterpret_cast<jbyte*>(g_OTR.data()));
    return out;
}

// Save OTR to file path
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(
        JNIEnv*, jclass, jstring path) {

    if (!path) return;

    const char* cpath = nullptr;
    cpath = env->GetStringUTFChars(path, nullptr);
    if (!cpath) return;

    FILE* f = fopen(cpath, "wb");
    if (!f) {
        env->ReleaseStringUTFChars(path, cpath);
        LOGI("Failed to open file: %s", cpath);
        return;
    }

    fwrite(g_OTR.data(), 1, g_OTR.size(), f);
    fclose(f);
    env->ReleaseStringUTFChars(path, cpath);

    LOGI("Saved BK.OTR: %zu bytes to %s", g_OTR.size(), cpath);
}

// Init game
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initGame(
        JNIEnv*, jclass, jobject /* surface */) {

    std::lock_guard<std::mutex> lock(g_stateMutex);

    g_framebuffer.resize(g_fbWidth * g_fbHeight);
    std::fill(g_framebuffer.begin(), g_framebuffer.end(), 0);

    core1_reset(g_ram.data());
    LOGI("Game initialized");
}

// Start/stop game loop
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(
        JNIEnv*, jclass) {

    if (g_running.load()) {
        LOGI("Game loop already running");
        return;
    }

    g_running.store(true);
    g_emulationThread = std::thread(emulation_loop);
    LOGI("Game loop started");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stopGameLoop(
        JNIEnv*, jclass) {

    if (!g_running.load()) return;

    g_running.store(false);

    if (g_emulationThread.joinable()) {
        g_emulationThread.join();
    }

    LOGI("Game loop stopped");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(
        JNIEnv*, jclass) {

    Java_com_bkawrapper_NativeBridge_stopGameLoop(nullptr, nullptr);

    std::lock_guard<std::mutex> lock(g_stateMutex);
    g_framebuffer.clear();

    LOGI("Game cleaned up");
}

} // extern "C"

// ------------------------------------------------------------
// JNI load
// ------------------------------------------------------------
JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM*, void*) {
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}