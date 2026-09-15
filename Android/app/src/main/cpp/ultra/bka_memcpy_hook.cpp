#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <android/log.h>

extern "C" {
void* __real_memcpy(void* dst, const void* src, size_t n);
void* __real_memmove(void* dst, const void* src, size_t n);
void* __real_memset(void* dst, int c, size_t n);

// Any DL entry whose words.w1 has top byte 0xFF (LE: byte[7]==0xFF or byte[3]==0xFF).
// The bad G_VTXs look like: [FC 62 FE 04  3F 15 F9 FF]  (w1 low32 = 0xFFF9153F)
// or                      [FC 26 98 04  1F 14 FF FF]  (w1 low32 = 0xFFFF141F)
// Detection: byte[3] (first w0 byte) == 0x04 and byte[7] == 0xFF.
static void check_and_log(const char* what, const void* dst, const void* src, size_t n) {
    uintptr_t d = (uintptr_t)dst;
    // Only DL-region destinations (any 0x72-prefixed heap).
    if (d < 0x7200000000ULL || d >= 0x7300000000ULL) return;
    if (n < 8) return;

    const unsigned char* p = (const unsigned char*)src;
    for (size_t i = 0; i + 8 <= n; i += 4) {
        // Match "opcode 0x04" at byte[3] or byte[7] and 0xFF in the other half's top byte.
        const unsigned char* q = p + i;
        int hit = 0;
        if (q[3] == 0x04 && (q[7] == 0xFF || q[7] == 0x01)) hit = 1;  // w0 LE, w1 LE high-byte 0xFF
        if (q[0] == 0x04 && (q[4] == 0xFF || q[4] == 0x01)) hit = 1;  // w0 BE, w1 BE high-byte 0xFF
        if (hit) {
            static int s_n = 0;
            if (s_n++ < 30) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "MEMHOOK %s dst=%p src=%p+%zu bytes=%02X%02X%02X%02X %02X%02X%02X%02X ra=%p",
                    what, dst, src, i,
                    q[0],q[1],q[2],q[3], q[4],q[5],q[6],q[7],
                    __builtin_return_address(0));
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
void* __wrap_memset(void* dst, int c, size_t n) {
    // memset can't inject a pattern, but log big fills into DL region for completeness.
    uintptr_t d = (uintptr_t)dst;
    if (d >= 0x7200000000ULL && d < 0x7300000000ULL && n >= 8 && c == 0) {
        static int s_m = 0;
        if (s_m++ < 5) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MEMHOOK memset dst=%p n=%zu ra=%p", dst, n, __builtin_return_address(0));
        }
    }
    return __real_memset(dst, c, n);
}
}
