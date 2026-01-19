#include <jni.h>
#include <mutex>
#include "menu/menu.hpp"

static std::mutex g_stateMutex;
static MenuHandler g_menuHandler;

extern "C" {

// Example of a properly defined JNI function
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeOnBackPressed(JNIEnv* env, jclass) {
    // Lock menu state
    std::lock_guard<std::mutex> lock(g_stateMutex);

    // Toggle menu
    g_menuHandler.toggle();
}

// Add more JNI exports if needed, e.g., initialization
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitMenu(JNIEnv* env, jclass) {
    std::lock_guard<std::mutex> lock(g_stateMutex);
    g_menuHandler.init();
}

// Optional: notify ROM ready state
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeSetRomReady(JNIEnv* env, jclass, jboolean ready) {
    std::lock_guard<std::mutex> lock(g_stateMutex);
    g_menuHandler.setRomReady(ready);
}

} // extern "C"