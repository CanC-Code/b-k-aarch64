#include <android/log.h>
#include <ultra64.h>
#include "functions.h"
#include "variables.h"

extern void func_8034CF74(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034D170(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034DD74(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034E6A8(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034CB64(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034EE2C(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034CD30(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034F250(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);
extern void func_8034F570(void *arg0, s32 arg1, BKModel *arg2, s32 arg3);

extern void func_8034CF90(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034D194(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034E26C(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034E8E4(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034CB9C(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034EF60(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034CD8C(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034F268(void *arg0, BKModel *arg1, s32 arg2);
extern void func_8034F5B0(void *arg0, BKModel *arg1, s32 arg2);

extern void func_8034CF6C(void *arg0);
extern void func_8034D168(void *arg0);
extern void func_8034DD48(void *arg0);
extern void func_8034E6A0(void *arg0);
extern void func_8034CB5C(void *arg0);
extern void func_8034EE24(void *arg0);
extern void func_8034CD28(void *arg0);
extern void func_8034F248(void *arg0);
extern void func_8034F568(void *arg0);

enum mesh_xform_e{
    MESH_XFORM_3_WATER = 3
};

typedef struct struct_1D_s{
    BKModel *model;
    s16 unk4;
    u8 xform_id;
    // u8 pad7[1];
    Struct70s unk8;//union of subtypes
}struct1Ds;

typedef struct struct_1E_s{
    void (* unk0)(void * arg0, s32 arg1, BKModel *arg2, s32 arg3);
    void (* unk4)(void * arg0, BKModel *arg1, s32 arg2);
    void (* unk8)(void * arg0);
}struct1Es;


struct1Es D_80372030[] = {
    {func_8034CF74, func_8034CF90, func_8034CF6C},
    {func_8034D170, func_8034D194, func_8034D168},
    {func_8034DD74, func_8034E26C, func_8034DD48},
    {func_8034E6A8, func_8034E8E4, func_8034E6A0}, //water?
    {func_8034CB64, func_8034CB9C, func_8034CB5C},
    {func_8034EE2C, func_8034EF60, func_8034EE24},
    {func_8034CD30, func_8034CD8C, func_8034CD28},
    {func_8034F250, func_8034F268, func_8034F248},
    {func_8034F570, func_8034F5B0, func_8034F568}, //lightning?
};

/* .bss */
struct {
    u8 unk0;
    vector(struct1Ds) *unk4;
} D_80386140;

/* .public */
void func_8034C9B0(int arg0);

//.code
func_8034C3D0(BKModel *arg0, s32 arg1, s32 vtx_xform_id, s32 arg3){
    struct1Ds * v0 = vector_pushBackNew(&D_80386140.unk4);
    v0->xform_id = vtx_xform_id;
    v0->model = arg0;
    v0->unk4 = arg1;
    D_80372030[v0->xform_id].unk0(&v0->unk8, arg3, v0->model, v0->unk4);
}

Struct70s *func_8034C448(s32 arg0){
    struct1Ds *iPtr;
    struct1Ds *endPtr = vector_getEnd(D_80386140.unk4);

    for(iPtr = vector_getBegin(D_80386140.unk4); iPtr < endPtr; iPtr++){
        if(iPtr->xform_id == 8 && iPtr->unk4 == arg0)
            return &iPtr->unk8;
    }
    return NULL;
}

int func_8034C4CC(void){
    return D_80386140.unk0 ? 1 : 0;
}

s32 func_8034C4F0(s32 arg0) {
    u8 sp8[0xA8];
    u8 *temp_v1;

    temp_v1 = sp8;
    return *(s32*)(arg0 - (intptr_t)(&temp_v1[8] - &temp_v1[0]));
}

s16 func_8034C50C(s32 arg0) {
    u8 sp8[0xA8];
    u8 *temp_v1;

    temp_v1 = sp8;
    return *(s16*)(arg0 - (intptr_t)(&temp_v1[4] - &temp_v1[0]));
}


Struct70s *func_8034C528(s32 arg0){
    struct1Ds *iPtr;
    struct1Ds *endPtr = vector_getEnd(D_80386140.unk4);

    for (iPtr = vector_getBegin(D_80386140.unk4); iPtr < endPtr; iPtr++) {
        if (iPtr->xform_id == 2 && iPtr->unk4 == arg0) {
            return &iPtr->unk8;
        }
    }

    return NULL;
}

Struct70s *func_8034C5AC(s32 arg0){
    struct1Ds *iPtr;
    struct1Ds *endPtr = vector_getEnd(D_80386140.unk4);

    for(iPtr = vector_getBegin(D_80386140.unk4); iPtr < endPtr; iPtr++){
        if(iPtr->xform_id == 3 && iPtr->unk4 == arg0)
            return &iPtr->unk8;
    }
    return NULL;
}

Struct70s *func_8034C630(s32 arg0){
    struct1Ds *iPtr;
    struct1Ds *endPtr = vector_getEnd(D_80386140.unk4);

    for(iPtr = vector_getBegin(D_80386140.unk4); iPtr < endPtr; iPtr++){
        if( (iPtr->xform_id == 3)
            && meshList_meshContainsVtx(model_getMeshList(iPtr->model), iPtr->unk4, arg0)
        ){
            return &iPtr->unk8;
        }
    }
    return NULL;
}

void func_8034C6DC(BKModel *arg0){
    BKMeshList *mesh_list = model_getMeshList(arg0);
    BKMesh *mesh = mesh_list->data;
    int i;
    s16 mesh_count = (s16)__builtin_bswap16((u16)mesh_list->count);

    __android_log_print(ANDROID_LOG_ERROR, "BKA-MESH",
        "func_8034C6DC ENTER arg0=%p mesh_list=%p count=%d data=%p",
        (void*)arg0, (void*)mesh_list,
        (int)mesh_count,
        mesh_list ? (void*)mesh_list->data : NULL);

    for (i = 0; i < mesh_count; i++) {
        s16 uid = (s16)__builtin_bswap16((u16)mesh->uid);
        s16 vtx_count = (s16)__builtin_bswap16((u16)mesh->vtx_count);

        if (i < 3) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA-MESH",
                "  iter=%d mesh=%p uid=%d vtx_count=%d",
                i, (void*)mesh, (int)uid, (int)vtx_count);
        }
        if ((uid >= 101) && (uid < 200)) {
            func_8034C3D0(arg0, uid, 1, uid - 100);
        } else if ((uid >= 200) && (uid < 300)) {
            func_8034C3D0(arg0, uid, 0, uid - 200);
        } else if ((uid >= 300) && (uid < 400)) {
            func_8034C3D0(arg0, uid, 3, uid - 300);
        } else if ((uid >= 400) && (uid < 500)) {
            func_8034C3D0(arg0, uid, 2, uid - 400);
        } else if ((uid >= 500) && (uid < 600)) {
            func_8034C3D0(arg0, uid, 4, uid - 500);
        } else if ((uid >= 600) && (uid < 700)) {
            func_8034C3D0(arg0, uid, 2, uid - 600);
        } else if ((uid >= 700) && (uid < 800)) {
            func_8034C3D0(arg0, uid, 5, uid - 700);
        } else if ((uid >= 800) && (uid < 900)) {
            func_8034C3D0(arg0, uid, 6, uid - 800);
        } else if ((uid >= 900) && (uid < 1000)) {
            func_8034C3D0(arg0, uid, 8, uid - 900);
        } else if ((uid >= 1000) && (uid < 1100)) {
            func_8034C3D0(arg0, uid, 7, uid - 1000);
        }

        mesh = (BKMesh *)&mesh->vertices[vtx_count];
    }
}

void func_8034C8D8(void){
    struct1Ds *iPtr;
    struct1Ds *endPtr = vector_getEnd(D_80386140.unk4);

    for(iPtr = vector_getBegin(D_80386140.unk4); iPtr < endPtr; iPtr++){
       D_80372030[iPtr->xform_id].unk8(&iPtr->unk8);
    }
    vector_free(D_80386140.unk4);
}

void func_8034C97C(void){
    D_80386140.unk4 = vector_new(sizeof(struct1Ds), 0x10);
    func_8034C9B0(1);
}

void func_8034C9B0(int arg0){
    D_80386140.unk0 = arg0 ? 1 : 0;
}

void * func_8034C9D4(void){
    return NULL; // TEMPORARY skip mesh transforms to avoid pointer truncation crash
    struct1Ds *iPtr;
    struct1Ds *endPtr = vector_getEnd(D_80386140.unk4);

    for(iPtr = vector_getBegin(D_80386140.unk4); iPtr < endPtr; iPtr++){
       D_80372030[iPtr->xform_id].unk4(&iPtr->unk8, iPtr->model, iPtr->unk4);
    }

}
