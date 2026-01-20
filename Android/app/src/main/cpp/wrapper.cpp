#include <jni.h>
#include <atomic>
#include <unistd.h>

static std::atomic<bool> g_paused{false};

extern "C" {

// Called from Java
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv*, jclass) {
    g_paused.store(true, std::memory_order_release);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv*, jclass) {
    g_paused.store(false, std::memory_order_release);
}

}

// Example emulation loop hook
void emulator_main_loop() {
    while (true) {
        if (g_paused.load(std::memory_order_acquire)) {
            usleep(16 * 1000); // ~60Hz idle
            continue;
        }

        // ---- emulator frame step here ----
    }
}