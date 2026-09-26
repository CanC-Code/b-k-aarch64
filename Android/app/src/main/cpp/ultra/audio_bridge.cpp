#include <android/log.h>

#define LOG_TAG "BKA_AUDIO"
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

extern "C" {

/* =========================
   Music
========================= */

// coMusicPlayer_playMusic, comusic_8025AB44, func_8025A9D4, etc.
// Real defs in src/core2/. Stubs disabled to eliminate duplicate symbols.

/* =========================
   Audio Engine
========================= */

// n_alSynAddPlayer, n_alSynStartVoice, n_alSynStopVoice
// Real defs in src/core1/ultra/audio/. Stubs disabled.

void n_alSynRemovePlayer(void) {
    LOGW("n_alSynRemovePlayer stub");
}

/* =========================
   SFX
========================= */

// sfx_play: real def in src/core2/code_85800.c

void func_8025F4F0(void) {
    LOGW("audio func_8025F4F0 stub");
}

} // extern "C"
