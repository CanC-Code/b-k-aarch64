#include <ultra64.h>
#include "functions.h"
#include "variables.h"
#include "core2/bonetransform.h"

typedef struct {
    BoneTransformList *bone_xform;
    s16 life;
    u8 alive;
    // u8 pad7[1];
}struct10E0s;

/* .bss */
#define ANIM_CACHE_SIZE 1024
struct10E0s D_80379E20[ANIM_CACHE_SIZE];

/* .code */
void animCache_init(void){
    int i;

    for(i = 0; i<ANIM_CACHE_SIZE; i++){
        D_80379E20[i].alive = FALSE;
        D_80379E20[i].bone_xform = NULL;
        D_80379E20[i].life = 0;
    }
}

void animCache_free(void){
    int i;

    for(i = 0; i<ANIM_CACHE_SIZE; i++){
        if(D_80379E20[i].alive){
            if(D_80379E20[i].bone_xform){
                boneTransformList_free(D_80379E20[i].bone_xform);
            }
        }
    }
}

void animCache_flushStale(void){
    int i;

    for(i = 0; i<ANIM_CACHE_SIZE; i++){
        if(D_80379E20[i].alive == TRUE && D_80379E20[i].bone_xform != NULL){
            if(D_80379E20[i].life < 0x3b){
                boneTransformList_free(D_80379E20[i].bone_xform);
                D_80379E20[i].bone_xform = 0;
                if(func_80254BC4(1)){
                    break;
                }
            }
        }
    }
}

void animCache_flushAll(void){
    int i;

    for(i = 0; i<ANIM_CACHE_SIZE; i++){
        if(D_80379E20[i].alive){
            volatileFlag_get(VOLATILE_FLAG_0_IN_FURNACE_FUN_QUIZ);
            D_80379E20[i].life = 0;
            boneTransformList_free(D_80379E20[i].bone_xform);
            D_80379E20[i].bone_xform = NULL;
        }
    }
}

void animCache_update(void){
    int i;

    for(i = 0; i<ANIM_CACHE_SIZE; i++){
        if(D_80379E20[i].alive == TRUE && D_80379E20[i].bone_xform){
            if(--D_80379E20[i].life <= 0){
                boneTransformList_free(D_80379E20[i].bone_xform);
                D_80379E20[i].bone_xform = 0;
            }
        }
    }
}

s16 animCache_getNextFree(void){
    int i;

    for(i = 0; i<ANIM_CACHE_SIZE; i++){
        if(!D_80379E20[i].alive){
            return i;
        }
    }
    return -1;
}

void animCache_release(s16 index);
s16 animCache_getNew(void){
    int indx = animCache_getNextFree();
    if (indx < 0) {
        // Evict an expired slot, or if none are expired, evict slot 0 as a last resort.
        for (int i = 0; i < ANIM_CACHE_SIZE; i++) {
            if (D_80379E20[i].alive && D_80379E20[i].life <= 0) {
                animCache_release(i);
                indx = i;
                break;
            }
        }
        if (indx < 0) {
            animCache_release(0);
            indx = 0;
        }
    }
    D_80379E20[indx].alive = TRUE;
    D_80379E20[indx].life = 0;
    D_80379E20[indx].bone_xform = 0;
    return indx;
}

bool animCache_inUse(s16 index){
    return (D_80379E20[index].bone_xform) ? 1 : 0; 
}

void animCache_release(s16 index){
    if(D_80379E20[index].bone_xform){
        boneTransformList_free(D_80379E20[index].bone_xform);
    }
    D_80379E20[index].alive = 0;
    D_80379E20[index].bone_xform = 0;
    D_80379E20[index].life = 0;

}

int animCache_getBoneTransformList(s16 index, BoneTransformList **arg1){
    D_80379E20[index].life = 0x3C;
    if(D_80379E20[index].bone_xform){
        *arg1 = D_80379E20[index].bone_xform;
        return FALSE;
    }else{
        D_80379E20[index].bone_xform = boneTransformList_new();
        *arg1 = D_80379E20[index].bone_xform;
        return TRUE;
    }
}

void animCache_defrag(void){
    int i;
    for(i = 0; i < ANIM_CACHE_SIZE; i++){
        if(D_80379E20[i].alive == TRUE && D_80379E20[i].bone_xform){
            D_80379E20[i].bone_xform = boneTransformList_defrag(D_80379E20[i].bone_xform);
        }
    }
}
