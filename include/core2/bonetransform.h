#ifndef _BONE_TRANSFORMATION_H_
#define _BONE_TRANSFORMATION_H_
#include <ultratypes.h>

typedef struct {
    f32 unk0[4];
    f32 scale[3];
    f32 unk1C[3];
}BoneTransform;

typedef struct bone_transform_list_s{
    BoneTransform *ptr;
    s32 count;
}BoneTransformList;

BoneTransformList *boneTransformList_new(void);
void boneTransformList_free(BoneTransformList *this);
void boneTransformList_reset(BoneTransformList *this);
void boneTransformList_getBoneScale(BoneTransformList *this, s32 bone_id, f32 scale[3]);
void boneTransformList_setBoneScale(BoneTransformList *this, s32 bone_id, f32 scale[3]);
void func_8033A8F0(BoneTransformList *this, s32 bone_id, f32 arg2[4]);
void func_8033A968(BoneTransformList *this, s32 bone_id, f32 arg2[3]);
void func_8033A9A8(BoneTransformList *this, s32 bone_id, f32 arg2[4]);
BoneTransformList *boneTransformList_defrag(BoneTransformList *this);
void boneTransformList_interpolate(BoneTransformList *this, BoneTransformList *start_xform_list, BoneTransformList *end_xform_list, f32 arg3);

#endif
