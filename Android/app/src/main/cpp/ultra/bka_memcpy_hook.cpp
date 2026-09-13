#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <android/log.h>

extern "C" {
void* __real_memcpy(void* dst, const void* src, size_t n);
void* __real_memmove(void* dst, const void* src, size_t n);

static const unsigned char kBad[8] = { 0xFC,0x62,0xFE,0x04, 0x3F,0x15,0xF9,0xFF };

static void check_and_log(const char* what, const void* dst, const void* src, size_t n) {
    uintptr_t d = (uintptr_t)dst;
    if (d < 0x7220000000ULL || d >= 0x7230000000ULL) return;
    if (n < 8) return;
    const unsigned char* p = (const unsigned char*)src;
    for (size_t i = 0; i + 8 <= n; i++) {
        if (memcmp(p + i, kBad, 8) == 0) {
            static int s_n = 0;
            if (s_n++ < 20) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "MEMHOOK %s dst=%p src=%p+%zu ra=%p",
                    what, dst, src, i, __builtin_return_address(0));
            }
            return;
        }
    }
}

void* __wrap_memcpy(void* dst, const void* src, size_t n) {
    check_and_log("memcpy", dst, src, n);
    return __real_memcpy(dst, src, n);
}
void* __wrap_memmove(void* dst, const void* src, size_t n) {
    check_and_log("memmove", dst, src, n);
    return __real_memmove(dst, src, n);
}
}
