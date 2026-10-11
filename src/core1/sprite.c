#include <ultra64.h>
#include "core1/core1.h"
#include <android/log.h>

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
                "sprite=%p id=%u cnt=%d szofBKSprite=%zu raw=%08X off=%08X base=%p ret=%p",
                (void*)this, frame_id, (int)frame_cnt,
                sizeof(BKSprite), raw, offset, (void*)base, (void*)ret);
    }
    return ret;
}
