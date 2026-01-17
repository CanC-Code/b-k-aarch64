#include <jni.h>
#include <thread>
#include <atomic>
#include <android/log.h>
#include <unistd.h>

extern "C" {
    void core1_reset(uint8_t* ram);
    void core1_stepCPU();
    void core2_stepFrame();
    void n_audioInit();
    void n_audioStep();
    void core1_loadOTR(const char* path);
}

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::atomic<bool> g_running{false};
static std::thread g_emulationThread;

static void emulation_loop() {
    LOGI("Emulation thread started");

    n_audioInit();
    core1_loadOTR("/sdcard/bk.otr");

    g_running.store(true);

    while (g_running.load()) {
        core1_stepCPU();
        core2_stepFrame();
        n_audioStep();

        // ~60Hz pacing
        usleep(16 * 1000);
    }

    LOGI("Emulation thread stopped");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeStart(JNIEnv*, jclass) {
    if (g_emulationThread.joinable()) {
        LOGI("Emulation already running");
        return;
    }

    LOGI("Starting emulation");
    g_emulationThread = std::thread(emulation_loop);
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeStop(JNIEnv*, jclass) {
    LOGI("Stopping emulation");
    g_running.store(false);

    if (g_emulationThread.joinable()) {
        g_emulationThread.join();
    }
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM*, void*) {
    LOGI("JNI_OnLoad called");
    return JNI_VERSION_1_6;
}