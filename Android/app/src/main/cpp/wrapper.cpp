extern "C" {

// ------------------------------------------------------------
// Menu toggle
// ------------------------------------------------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_MenuNative_nativeToggleMenu(
        JNIEnv*, jclass) {

    bool newState = !g_menuVisible.load();
    g_menuVisible.store(newState);
    g_emulatorPaused.store(newState);

    __android_log_print(
        ANDROID_LOG_INFO,
        "BKAWrapper",
        "Menu %s",
        newState ? "opened" : "closed"
    );
}

// ------------------------------------------------------------
// Pause
// ------------------------------------------------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_MenuNative_nativePauseEmulator(
        JNIEnv*, jclass) {

    g_emulatorPaused.store(true);
}

// ------------------------------------------------------------
// Resume
// ------------------------------------------------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_MenuNative_nativeResumeEmulator(
        JNIEnv*, jclass) {

    g_emulatorPaused.store(false);
}

}