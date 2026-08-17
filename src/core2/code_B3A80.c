#include <stdint.h>
#include "../../Android/app/src/main/cpp/bka_safe_base.h"
static inline s16 bswap16(s16 v) { return (s16)__builtin_bswap16((u16)v); }
#include <android/log.h>
#define LOG_BKA_ACACHE(tag, ...) __android_log_print(ANDROID_LOG_INFO, "BKA-ACACHE", tag, ##__VA_ARGS__)
#include <ultra64.h>
#include "functions.h"
#include "variables.h"

#include "assets.h"
#include "animation.h"

extern f32 glspline_catmull_rom_interpolate(f32, s32, f32 *);
extern BKSpriteDisplayData * func_80344A1C(BKSprite *arg0);
f32 D_803709E0[] = {
    0.0f, 0.0f, 0.0f, 1.0f,
    1.0f, 1.0f, 0.0f, 0.0f,
    0.0f, 0.0f, 0.0f, 0.0f
};
s32 assetCacheCurrentSize = 0;
#define ASSET_CACHE_SIZE 512
 u16 assetCacheLength = 0; //assetCache_size;
 u16 assetCacheCurrentIndex = 0;
 u8 D_80370A1C = FALSE;


/* .bss */
u8 D_80383CB0[16];
u8 pad_80383CB8[0x8];
AssetROMHead *assetSectionRomHeader;
AssetFileMeta *assetSectionRomMetaList;
u32 D_80383CC8;
s32 D_80383CCC; //asset_data_rom_offset
void** assetCachePtrList; //assetCache_ptrs;
BKSpriteDisplayData **D_80383CD4;
u16* assetCacheDependencyCount; //assetCache_dependencies;
static u32 g_assetCacheCapacity = 0;
s16 *assetCacheAssetIdList; //assetCache_indexs
vector(struct21s) *D_80383CE0[2];

/* .public */
extern s32 assetcache_release(void * arg0);

f32  func_8033ABA0(AnimationFile *anim_file, f32 arg1);
f32  func_8033AC38(AnimationFile *anim_file, AnimationFileElement *arg1, f32 arg2);
s32  func_8033AC0C(AnimationFile *this);
void func_8033AFB8(BoneTransformList *arg0, s32 arg1, f32 arg2[3][3]);
void func_8033BAB0(enum asset_e asset_id, s32 offset, s32 size, void *dst_ptr);

/* .core2 */
f32 func_8033AA10(AnimationFile *this, s32 arg1){
    __android_log_print(ANDROID_LOG_ERROR, "BKA-BONE", "func_8033AFB8 entry\n");
    if(arg1 == this->unk2)
        return 0.999999f;
    return (f32)(arg1 - this->unk0)/(f32)(this->unk2 - this->unk0);
}
f32 func_8033ABA0(AnimationFile *this, f32 arg1){
    return this->unk0 + arg1*(this->unk2 - this->unk0);
}

void animationFile_getBoneTransformList(AnimationFile *anim_file, f32 progress, BoneTransformList *bone_transform_list){
    if (anim_file == NULL || bone_transform_list == NULL) return;
    s32 bone_id;
    int i;
    f32 tmp_f22;
    AnimationFileElement *tmp_s0;
    f32 sp54[3][3];

    tmp_f22 = func_8033ABA0(anim_file, progress);
    tmp_s0 = (AnimationFileElement *)((uintptr_t)anim_file + sizeof(AnimationFile));
    bone_id = 0;
    s16 elem_cnt = bswap16(anim_file->elem_cnt);
    for(i = 0; i < elem_cnt; i++){//L8033AAB8
        u16 packed = bswap16(*(u16*)tmp_s0);
        s16 bone = (packed >> 4) & 0xFFF;
        s16 channel = packed & 0xF;
        if (channel > 2) channel = 0; // clamp to valid transform channels
        s16 data_cnt = bswap16(tmp_s0->data_cnt);
        if(bone != bone_id){
            if(bone_id != 0)
                func_8033AFB8(bone_transform_list, bone_id, sp54);
            bone_id = bone;
            sp54[0][0] = sp54[0][1] = sp54[0][2] = 0.0f;
            sp54[1][0] = sp54[1][1] = sp54[1][2] = 1.0f;
            sp54[2][0] = sp54[2][1] = sp54[2][2] = 0.0f;
        }
        sp54[0][channel] = func_8033AC38(anim_file, tmp_s0, tmp_f22);
        tmp_s0 += data_cnt;
        tmp_s0++;
    }//L8033AB60
    func_8033AFB8(bone_transform_list, bone_id, sp54);
}


f32 func_8033ABCC(AnimationFile *this){
    f32 tmp = func_8033AC0C(this);
    return (tmp - 1.0)/tmp;
}

s32 func_8033AC0C(AnimationFile *this){
    return this->unk2;
}

s32 func_8033AC14(AnimationFile *this){
    return this->unk0;
}

s32 func_8033AC1C(AnimationFile *this){
    return this->unk2 - this->unk0 + 1;
}

s32 animationFile_count(AnimationFile *this){
    return this->elem_cnt;
}

f32 func_8033AC38(AnimationFile *this, AnimationFileElement *elem, f32 time){
    AnimationFileData *end_anim;
    AnimationFileData *start_anim;
    AnimationFileData *var_v0;
    f32 temp_f12;
    f32 knot_list[4];
    s16 elem_count = bswap16(elem->data_cnt);

    start_anim = &elem->data[0];
    u16 s_info = bswap16(*(u16*)start_anim);
    s16 s_unk0_13 = s_info & 0x3FFF;
    s16 s_unk0_14 = (s_info >> 14) & 1;
    s16 s_unk0_15 = (s_info >> 15) & 1;
    s16 s_unk2 = bswap16(((s16*)start_anim)[1]);

    if ((s32)time < s_unk0_13) {
        u16 elem_packed = bswap16(*(u16*)elem);
        s16 elem_channel = elem_packed & 0xF;
        knot_list[0] = knot_list[1] = D_803709E0[elem_channel];
        knot_list[2] = (f32) s_unk2 / 64;
        knot_list[3] = (s_unk0_15 == 1 && elem_count >= 2) ? (f32)(bswap16(((s16*)(start_anim + 1))[1]))/64 : knot_list[2];
        return glspline_catmull_rom_interpolate((time - this->unk0)/(s_unk0_13 - this->unk0), 4, knot_list);
    }

    end_anim = start_anim + elem_count;
    end_anim--;
    u16 e_info = bswap16(*(u16*)end_anim);
    s16 e_unk0_13 = e_info & 0x3FFF;
    s16 e_unk0_14 = (e_info >> 14) & 1;
    s16 e_unk0_15 = (e_info >> 15) & 1;
    s16 e_unk2 = bswap16(((s16*)end_anim)[1]);

    if ((s32) time >= e_unk0_13) {
        knot_list[1] = (f32) e_unk2 / 64;
        knot_list[0] = ((e_unk0_14 == 1) && (elem_count >= 2)) ? (f32)(bswap16(((s16*)(end_anim - 1))[1]))/64 : knot_list[1];
        knot_list[2] = knot_list[3] = knot_list[1];
        return glspline_catmull_rom_interpolate(time - e_unk0_13, 4, knot_list);
    }

    var_v0 = start_anim + 1;
    while (var_v0 < end_anim){
        var_v0 = &start_anim[(end_anim - start_anim)/2];
        u16 v_info = bswap16(*(u16*)var_v0);
        s16 v_unk0_13 = v_info & 0x3FFF;
        if (v_unk0_13 <= (s32)time) {
            start_anim = var_v0;
            s_info = bswap16(*(u16*)start_anim);
            s_unk0_13 = s_info & 0x3FFF;
            s_unk0_14 = (s_info >> 14) & 1;
            s_unk0_15 = (s_info >> 15) & 1;
            s_unk2 = bswap16(((s16*)start_anim)[1]);
        } else {
            end_anim = var_v0;
            e_info = bswap16(*(u16*)end_anim);
            e_unk0_13 = e_info & 0x3FFF;
            e_unk0_14 = (e_info >> 14) & 1;
            e_unk0_15 = (e_info >> 15) & 1;
            e_unk2 = bswap16(((s16*)end_anim)[1]);
        }
        var_v0 = start_anim + 1;
    }

    knot_list[1] = (f32) s_unk2 / 64;
    knot_list[2] = (f32) e_unk2 / 64;
    temp_f12 = (time - s_unk0_13) / (e_unk0_13 - s_unk0_13);
    if ((s_unk0_14 == 0) && (e_unk0_15 == 0)) {
        return knot_list[1] + ((knot_list[2] - knot_list[1]) * temp_f12);
    }

    knot_list[0] = (s_unk0_14 == 1 && (start_anim - 1) >= &elem->data[0]) ? (f32)(bswap16(((s16*)(start_anim - 1))[1]))/64 : knot_list[1];
    knot_list[3] = (e_unk0_15 == 1 && (end_anim + 1) < &elem->data[elem_count]) ? (f32)(bswap16(((s16*)(end_anim + 1))[1]))/64 : knot_list[2];
    return glspline_catmull_rom_interpolate(temp_f12, 4, knot_list);
}

void func_8033AFB8(BoneTransformList *bone_transform_list, s32 bone_id, f32 arg2[3][3]){
    __android_log_print(ANDROID_LOG_ERROR, "BKA-BONE", "func_8033AFB8 entry\n");
    f32 sp18[8];
    sp18[4] = sp18[5] = sp18[6] = sp18[7] = 0.0f;
    func_80345CD4(sp18, arg2[0]);
    __android_log_print(ANDROID_LOG_ERROR, "BKA-BONE", "func_8033AFB8 after CD4 tail=%f %f %f %f\n", sp18[4], sp18[5], sp18[6], sp18[7]);
    func_8033A8F0(bone_transform_list, bone_id, sp18);
    __android_log_print(ANDROID_LOG_ERROR, "BKA-BONE", "func_8033AFB8 after A8F0 tail=%f %f %f %f\n", sp18[4], sp18[5], sp18[6], sp18[7]);
    boneTransformList_setBoneScale(bone_transform_list, bone_id, arg2[1]);
    __android_log_print(ANDROID_LOG_ERROR, "BKA-BONE", "func_8033AFB8 after setBoneScale\n");
    func_8033A968(bone_transform_list, bone_id, arg2[2]);
    __android_log_print(ANDROID_LOG_ERROR, "BKA-BONE", "func_8033AFB8 after A968 tail=%f %f %f %f\n", sp18[4], sp18[5], sp18[6], sp18[7]);
}

void func_8033B020(void *ptr){
    struct21s *start_ptr;
    struct21s *end_ptr;
    struct21s *iPtr;

    end_ptr = (struct21s *) vector_getEnd(D_80383CE0[0]);
    start_ptr = (struct21s *) vector_getBegin(D_80383CE0[0]);

    for (iPtr = start_ptr; iPtr < end_ptr && ptr != iPtr->unk1; iPtr++);

    if (iPtr < end_ptr) {
        iPtr->unk0++;
    }
    else {
        iPtr = (struct21s *) vector_pushBackNew(&D_80383CE0[0]);
        iPtr->unk0 = 1;
        iPtr->unk1 = ptr;
    }
}

bool func_8033B0D0(void *arg0) {
    struct21s *start_ptr;
    struct21s *end_ptr;
    struct21s *iPtr;
    s32 j;

    for(j = 0; j < 2; j++){
        end_ptr = (struct21s *) vector_getEnd(D_80383CE0[j]);
        start_ptr = (struct21s *) vector_getBegin(D_80383CE0[j]);
        for(iPtr = start_ptr; iPtr < end_ptr && arg0 != iPtr->unk1; iPtr++){
        }
        if (iPtr < end_ptr){
            return TRUE;
        }
    }
    return FALSE;
}

void func_8033B180(void){
    D_80383CE0[0] = vector_new(sizeof(struct21s), 0x10);
    D_80383CE0[1] = vector_new(sizeof(struct21s), 0x10);
}

void func_8033B1BC(void){
    vector(struct21s) *tmp_a0;
    struct21s *iPtr;
    struct21s *start_ptr;
    struct21s *endPtr;
    int i;

    tmp_a0 = D_80383CE0[0];
    D_80383CE0[0] = D_80383CE0[1];
    D_80383CE0[1] = tmp_a0;
    
    endPtr = (struct21s *) vector_getEnd(D_80383CE0[0]);
    start_ptr = (struct21s *) vector_getBegin(D_80383CE0[0]);
    for(iPtr = start_ptr; iPtr < endPtr; iPtr++){
        for(i = 0; i < iPtr->unk0; i++)
            assetcache_release(iPtr->unk1);
    }
    
    vector_clear(D_80383CE0[0]);
}

void func_8033B268(void){
#if VERSION == VERSION_USA_1_0
    D_80383CE0[0] = (vector(struct21s) *)defrag(D_80383CE0[0]);
    D_80383CE0[1] = (vector(struct21s) *)defrag(D_80383CE0[1]);
#else
    D_80383CE0[0] = (vector(struct21s) *)vector_defrag(D_80383CE0[0]);
    D_80383CE0[1] = (vector(struct21s) *)vector_defrag(D_80383CE0[1]);
#endif
}

void func_8033B2A4(s32 arg0) {
    assetCachePtrList[assetCacheLength] = malloc(arg0);
    D_80383CD4[assetCacheLength] = NULL;
    assetCacheDependencyCount[assetCacheLength] = 1;
    assetCacheAssetIdList[assetCacheLength] = -1;
    assetCacheLength += 1;
}

bool codeB3A80_releaseSprite(BKSprite **sprite_ptr, BKSpriteDisplayData **sprite_gfx_ptr)
{
    BKSprite *sprite;
    if ((*sprite_ptr) == NULL)
        return FALSE;

    sprite = *sprite_ptr;
    assetcache_release(sprite);
    *sprite_ptr = NULL;
    *sprite_gfx_ptr = NULL;
    return TRUE;
}

bool func_8033B388(BKSprite **sprite_ptr, BKSpriteDisplayData **arg1){
    if(*sprite_ptr == NULL)
        return FALSE;
    
    func_8033B020(*sprite_ptr);
    *sprite_ptr = NULL;
    *arg1 = NULL;

    if(sprite_ptr);
    
    return TRUE;
}

s32 assetcache_release(void * arg0){
    s32 i;
    if(arg0){
        for(i = 0; i < assetCacheLength  && arg0 != assetCachePtrList[i]; i++);

        if(i == assetCacheLength)
            return 2;

        assetCacheCurrentIndex = i;
        if(assetCacheDependencyCount[i] == 1){
            if(D_80383CD4[i])
                func_803449DC(D_80383CD4[i]);
            free(arg0);
            assetCacheLength--;
            assetCacheDependencyCount[i] = assetCacheDependencyCount[assetCacheLength];
            assetCachePtrList[i] = assetCachePtrList[assetCacheLength];
            D_80383CD4[i] = D_80383CD4[assetCacheLength];
            assetCacheAssetIdList[i] = assetCacheAssetIdList[assetCacheLength];
            return 0;
        }
        else{
            assetCacheDependencyCount[i]--;
            return 1;
        }
    } else{
        return 3;
    }
}

void assetcache_update_ptr(void * arg0, void* arg1){
    s32 i;

    if((arg0 == NULL) || (arg1 == NULL) || (arg0 == arg1))
        return;

    for(i = 0; i < assetCacheLength  && arg0 != assetCachePtrList[i]; i++);

    if(i != assetCacheLength && arg1 != assetCachePtrList[i])
        assetCachePtrList[i] = arg1;
}

void func_8033B5FC(void){
    func_8033B268();
}

void func_8033B61C(void){
    core1_15B30_sendMesg3ToRenderThread();
    func_8033B1BC();
    func_8033B1BC();
}

s32 asset_getFlag(enum asset_e arg0){
    return assetSectionRomMetaList[arg0].unk6;
}

s32 assetSection_getCount(void){
    return assetSectionRomHeader->count-1;
}

s32 func_8033B678(void ){
    return assetCacheCurrentSize;
}

s32 asset_getSize(s32 arg0){
    return assetSectionRomMetaList[arg0+1].offset - assetSectionRomMetaList[arg0].offset;
}

bool asset_isCompressed(enum asset_e arg0){ //asset_compressed?
    return (assetSectionRomMetaList[arg0].compFlag & 1) !=0;
}

//returns raw sprite(as saved in ROM) and points arg1 to a parsed sprite(?)
BKSprite *codeB3A80_getSprite(enum asset_e sprite_id, BKSpriteDisplayData **arg1){
    BKSprite *s0;
    s0 = assetcache_get(sprite_id);
    if(D_80383CD4[assetCacheCurrentIndex] == NULL){
        codeAEDA0_setSpriteDrawMode(-1);
        func_80338308(sprite_getUnk8(s0), sprite_getUnkA(s0));
        D_80383CD4[assetCacheCurrentIndex] = func_80344A1C(s0);
    }
    *arg1 = D_80383CD4[assetCacheCurrentIndex];
    return s0;
}

void assetcache_func_8033B788(void) {
    D_80370A1C = TRUE;
}

void *assetcache_get(enum asset_e assetId) {
    s32 comp_size;
    s32 i;
    volatile s32 sp3C;
    s32 uncomp_size;
    void *uncompressed_file;
    u8 sp33;
    void *compressed_file;
    bool sp28;

    __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: START assetId=%d", assetId);
    sp28 = D_80370A1C;
    D_80370A1C = FALSE;

    for(i = 0; i < assetCacheLength && assetId != assetCacheAssetIdList[i]; i++);
    assetCacheCurrentIndex = i;

    if(i < assetCacheLength){
        assetCacheDependencyCount[i]++;
        __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: CACHE HIT assetId=%d", assetId);
        return assetCachePtrList[i];
    }

    comp_size = assetSectionRomMetaList[assetId+1].offset - assetSectionRomMetaList[assetId].offset;
    if(comp_size & 1) comp_size++;
    sp3C = comp_size;
    __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: comp_size=%d", comp_size);

    if(assetSectionRomMetaList[assetId].compFlag & 0x0001){
        __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: COMPRESSED assetId=%d, reading header", assetId);
        func_8033BAB0(assetId, 0, 0x10, &D_80383CB0);
        assetCacheCurrentSize = rarezip_get_uncompressed_size(&D_80383CB0);
        uncomp_size = assetCacheCurrentSize;
        if(uncomp_size & 0xF){
            uncomp_size -= uncomp_size & 0xF;
            uncomp_size += 0x10;
        }
        __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: uncomp_size=%d", uncomp_size);

        if (func_8025498C((u32)comp_size + uncomp_size) && !sp28) {
            sp33 = 1;
            uncompressed_file = malloc((u32)comp_size + uncomp_size + 64);
            compressed_file = (void *)((u8*)uncompressed_file + uncomp_size);
            __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: single alloc uncomp=%p comp=%p", uncompressed_file, compressed_file);
        } else {
            sp33 = 2;
            if (sp28) {
                func_80254C98();
            }
            uncompressed_file = malloc(uncomp_size);
            compressed_file = malloc(comp_size);
            __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: double alloc uncomp=%p comp=%p", uncompressed_file, compressed_file);
        }
    } else {
        uncompressed_file = malloc(comp_size + 64);
        compressed_file = uncompressed_file;
        __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: UNCOMPRESSED assetId=%d ptr=%p", assetId, uncompressed_file);
    }

    __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: before piMgr_read assetId=%d", assetId);
    piMgr_read(compressed_file, assetSectionRomMetaList[assetId].offset + D_80383CCC, sp3C);
    __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: after piMgr_read assetId=%d", assetId);

    if(assetSectionRomMetaList[assetId].compFlag & 0x0001){
        __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: before bk_inflate assetId=%d", assetId);
        rarezip_inflate(compressed_file, uncompressed_file);
        __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: after bk_inflate assetId=%d", assetId);

        uncompressed_file = (void*)realloc(uncompressed_file, assetCacheCurrentSize);
        osWritebackDCache(uncompressed_file, assetCacheCurrentSize);
        if (sp33 == 2) {
            free(compressed_file);
        }
    }

    if (assetCacheLength >= g_assetCacheCapacity - 1) {
        u32 new_cap = g_assetCacheCapacity * 2;
        assetCachePtrList = (void**)realloc(assetCachePtrList, new_cap * sizeof(void*));
        D_80383CD4 = (BKSpriteDisplayData**)realloc(D_80383CD4, new_cap * sizeof(BKSpriteDisplayData*));
        assetCacheDependencyCount = (u16*)realloc(assetCacheDependencyCount, new_cap * sizeof(u16));
        assetCacheAssetIdList = (s16*)realloc(assetCacheAssetIdList, new_cap * sizeof(s16));
        if (!assetCachePtrList || !D_80383CD4 || !assetCacheDependencyCount || !assetCacheAssetIdList) {
            return NULL;
        }
        g_assetCacheCapacity = new_cap;
    }

    assetCacheCurrentIndex = assetCacheLength;
    assetCacheDependencyCount[assetCacheLength] = 1;
    assetCachePtrList[assetCacheLength] = uncompressed_file;
    D_80383CD4[assetCacheLength] = 0;
    assetCacheAssetIdList[assetCacheLength] = assetId;
    assetCacheLength++;

    __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "assetcache_get: COMPLETE assetId=%d", assetId);
    return uncompressed_file;
}
void func_8033BAB0(enum asset_e asset_id, s32 offset, s32 size, void *dst_ptr) {
    piMgr_read(dst_ptr, assetSectionRomMetaList[asset_id].offset + D_80383CCC + offset, size);
}

void assetCache_resizeAsset(void *assetPtr, s32 size){
    s32 tmp;
    s32 i;

    for(i = 0; i < assetCacheLength  && assetPtr != assetCachePtrList[i]; i++);
    assetCachePtrList[i] = realloc(assetPtr, size);
}

void assetCache_init(void){
    D_80370A1C = FALSE;
    func_8033B180();
    assetCachePtrList = (void **)malloc(ASSET_CACHE_SIZE*sizeof(void*));
    D_80383CD4 = (BKSpriteDisplayData **)malloc(ASSET_CACHE_SIZE * sizeof(BKSpriteDisplayData*));
    assetCacheDependencyCount = (u16*)malloc(ASSET_CACHE_SIZE*sizeof(u16));
    assetCacheAssetIdList = (s16 *)malloc(ASSET_CACHE_SIZE*sizeof(s16));
    g_assetCacheCapacity = ASSET_CACHE_SIZE;
    assetCacheLength = 0;
    assetSectionRomHeader = (AssetROMHead *)malloc(sizeof(AssetROMHead));
    D_80383CC8 = assets_ROM_START;
    piMgr_read(assetSectionRomHeader, D_80383CC8, sizeof(AssetROMHead));

    // Byteswap header fields (N64 big-endian -> host little-endian)
    assetSectionRomHeader->count = __builtin_bswap32(assetSectionRomHeader->count);
    assetSectionRomHeader->unk4  = __builtin_bswap32(assetSectionRomHeader->unk4);

    __android_log_print(ANDROID_LOG_INFO, "BKA-META", "swapped count=0x%08X unk4=0x%08X",
        assetSectionRomHeader->count, assetSectionRomHeader->unk4);

    assetSectionRomMetaList = (AssetFileMeta *)malloc(assetSectionRomHeader->count * sizeof(AssetFileMeta));
    piMgr_read(assetSectionRomMetaList, D_80383CC8 + sizeof(AssetROMHead),
               assetSectionRomHeader->count * sizeof(AssetFileMeta));

    for (u32 _i = 0; _i < assetSectionRomHeader->count; _i++) {
        assetSectionRomMetaList[_i].offset = __builtin_bswap32(assetSectionRomMetaList[_i].offset);
        assetSectionRomMetaList[_i].compFlag = (s16)__builtin_bswap16((u16)assetSectionRomMetaList[_i].compFlag);
        assetSectionRomMetaList[_i].unk6 = (s16)__builtin_bswap16((u16)assetSectionRomMetaList[_i].unk6);
    }

    __android_log_print(ANDROID_LOG_INFO, "BKA-META", "swapped meta[0] offset=0x%08X comp=%d unk6=%d",
        assetSectionRomMetaList[0].offset, assetSectionRomMetaList[0].compFlag, assetSectionRomMetaList[0].unk6);
    __android_log_print(ANDROID_LOG_INFO, "BKA-META", "swapped meta[1] offset=0x%08X comp=%d unk6=%d",
        assetSectionRomMetaList[1].offset, assetSectionRomMetaList[1].compFlag, assetSectionRomMetaList[1].unk6);
    __android_log_print(ANDROID_LOG_INFO, "BKA-META", "swapped meta[2] offset=0x%08X comp=%d unk6=%d",
        assetSectionRomMetaList[2].offset, assetSectionRomMetaList[2].compFlag, assetSectionRomMetaList[2].unk6);

    D_80383CCC = D_80383CC8 + sizeof(AssetROMHead) + assetSectionRomHeader->count * sizeof(AssetFileMeta);
}

s32 asset_getCompressedSize(enum asset_e arg0){
    return assetSectionRomMetaList[arg0+1].offset - assetSectionRomMetaList[arg0].offset;
}

s32 assetCache_getDependencyCount(enum asset_e arg0){
    s32 i;

    for(i = 0; i < assetCacheLength  && arg0 != assetCacheAssetIdList[i]; i++);
    if(i < assetCacheLength){
        return assetCacheDependencyCount[i];
    }
    return 0;
}

void func_8033BD20(BKModelBin **arg0){
    func_8033B020(*arg0);
    *arg0 = NULL;
}

void assetCache_free(void *arg0){
    func_8033B020(arg0);
}

void func_8033BD6C(void){
    func_8033B1BC();
}

void func_8033BD8C(void* arg0){
    func_8033B0D0(arg0);
}

s32 code_B3A80_func_8033BDAC(enum asset_e id, void *dst, s32 size) {
    s32 comp_size;
    s32 var_s0;
    s32 sp34;
    s32 phi_v0;
    u8* comp_ptr;
    u8 sp2B;

    //find asset in cache
    for(phi_v0 = 0; phi_v0 < assetCacheLength && id != assetCacheAssetIdList[phi_v0]; phi_v0++);
    assetCacheCurrentIndex = phi_v0;
    if (phi_v0 == assetCacheLength) { //asset not in cache
        return 0;
    }
    comp_size = assetSectionRomMetaList[id + 1].offset - assetSectionRomMetaList[id].offset;
    if (comp_size & 1) {
        comp_size++;
    }
    sp34 = comp_size;
        
    if (assetSectionRomMetaList[id].compFlag & 1) {
        func_8033BAB0(id, 0, 0x10, &D_80383CB0);
        assetCacheCurrentSize = rarezip_get_uncompressed_size(&D_80383CB0);

        // get aligned uncompressed size
        var_s0 = assetCacheCurrentSize;
        if (var_s0 & 0xF) {
            var_s0 = (var_s0 - (var_s0 & 0xF)) + 0x10;
        }

        if (size >= (comp_size + var_s0)) {
            sp2B = 1;
            comp_ptr = (u8*)dst + var_s0;
        }
        else if(size >= var_s0) {
            sp2B = 2;
            comp_ptr = (u8*)malloc(comp_size);
        }
        else{
            return 0;
        }
    }
    else{
        var_s0 = comp_size;
        if(comp_size & (0x10 -1)) 
           var_s0 = (comp_size - (comp_size & (0x10 -1))) + 0x10;
        
        if(size >= comp_size){
            comp_ptr = (u8*)dst;
        }
        else{
            return 0;
        }
    }
    comp_size = assetSectionRomMetaList[id].offset + D_80383CCC;
    piMgr_read(comp_ptr, comp_size, sp34);
    if (assetSectionRomMetaList[id].compFlag & 1) {
        rarezip_inflate(comp_ptr, dst);
        osWritebackDCache(dst, assetCacheCurrentSize);
        if (sp2B == 2) {
            free(comp_ptr);
        }
    }
    return var_s0;
}
