#include <ultra64.h>
#include "core1/core1.h"
#include <android/log.h>
#include <malloc.h>

u32 sprite_getUnk8(BKSprite *this) {
    return this->unk8;
}

u32 sprite_getUnkA(BKSprite *this) {
    return this->unkA;
}

u32 sprite_getUnk6(BKSprite *this) {
    return this->unk6;
}

u32 sprite_getUnk4(BKSprite *this) {
    return this->unk4;
}

s32 sprite_getFrameCount(BKSprite *this) {
    /* ARM64 port 2026-10-15: host-range guard on sprite_getFrameCount.
       particleEmitter_update passes this->sprite_1C after only a NULL
       check. On the N64-logo map that field holds a non-NULL truncated
       32-bit pointer (sign-extended), crashing at +8 on the frameCnt
       load. Return 0 for pointers outside the port's host mmap range
       0x7000000000-0x8000000000. Same class of fix as sMapSavestates[],
       D_8036E570, D_80371E70[] and the func_80342038 guard. */
    uintptr_t v = (uintptr_t)this;
    if (this == NULL || v < 0x7000000000ULL || v >= 0x8000000000ULL) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA-SPRITE",
            "sprite_getFrameCount: bad ptr %p", (void*)this);
        return 0;
    }
    return (s16)__builtin_bswap16((u16)this->frameCnt);
}

BKSpriteFrame *sprite_getFramePtr(BKSprite *this, u32 frame_id) {
    u32 raw = (u32)this->offsets[frame_id];
    u32 offset = __builtin_bswap32(raw);
    s16 frame_cnt = (s16)__builtin_bswap16((u16)this->frameCnt);
    u8 *base = (u8 *)this + sizeof(BKSprite) + frame_cnt * sizeof(s32);
    BKSpriteFrame *ret = (BKSpriteFrame *)(base + offset);
    {
        static int s_fp = 0;
        if (s_fp++ < 500)
            __android_log_print(ANDROID_LOG_ERROR, "BKA-FRPTR",
                "sprite=%p usable=%zu id=%u cnt=%d raw=%08X off=%08X ret=%p",
                (void*)this, malloc_usable_size((void*)this),
                frame_id, (int)frame_cnt,
                raw, offset, (void*)ret);
    }
    return ret;
}
