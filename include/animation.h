#ifndef ANIMATION_H
#define ANIMATION_H

#include "prop.h"
size_t  anim_getSize(void);
enum asset_e  anim_getIndex(Animation *this);
f32  anim_getTimer(Animation *this);
f32  anim_getDuration(Animation *this);
void anim_new(Animation *this, bool arg1);
void anim_setTimer(Animation *this, f32 arg1);
void anim_80289790(Animation* this, void (*arg1)(s32, s32));
void anim_80289798(Animation *this, s32 arg1);
void anim_setDuration(Animation *this, f32 arg1);

//represents the transformation on a given model bone



#endif
