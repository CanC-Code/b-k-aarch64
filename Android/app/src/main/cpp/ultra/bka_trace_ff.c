#include <android/log.h>

void bka_trace_ff_val(unsigned long long v) {
    static int n = 0;
    if (n++ > 60) return;
    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
        "WEIRDW1 v=0x%llx ra0=%p ra1=%p",
        v,
        __builtin_return_address(0),
        __builtin_return_address(1));
}
