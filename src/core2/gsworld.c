#include <ultra64.h>
#include <android/log.h>
#define LOG_BKA_INIT(tag) __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "gsworld_set: %s", tag)
#include "core1/core1.h"
#include "functions.h"
#include "variables.h"

#include "core2/anim/sprite.h"
#include <core2/file.h>
#include "core2/particle.h"
#include "prop.h"
extern ActorArray *suBaddieActorArray;

struct gsworld_data_s {
    s32 unk0; // probably game_mode_e
    enum map_e map;
    s32 exit;
};

static u8 sHackDetected = FALSE; // seems related to some sort of cheatcode hack detection
struct gsworld_data_s sGsWorldData;
static bool sEnableUpdate;
static bool sEnableDraw;

enum gsWorldStartIndicators {
    GS_WORLD_START_INDICATOR_0_END,
    GS_WORLD_START_INDICATOR_1_CUBES,
    GS_WORLD_START_INDICATOR_2_UNUSED,
    GS_WORLD_START_INDICATOR_3_CAMERAS,
    GS_WORLD_START_INDICATOR_4_LIGHTING
};

void gsworld_draw(Gfx** gfx, Mtx **mtx, Vtx **vtx) {
    f32 near, far;

    __android_log_print(ANDROID_LOG_ERROR, "BKA-DRAW",
        "gsworld_draw entry: sEnableDraw=%d\n", sEnableDraw);

    if (!sEnableDraw) {
        drawRectangle2D(gfx, 0, 0, gFramebufferWidth, gFramebufferHeight, 0, 0, 0);
        core2_34790_getClipDistances(&near, &far);
        viewport_setNearAndFar(near, far);
        viewport_setRenderViewportAndPerspectiveMatrix(gfx, mtx);
        return;
    }

    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
        "gsworld_draw actors: suBaddieActorArray=%p cnt=%d map=%d",
        suBaddieActorArray, suBaddieActorArray ? suBaddieActorArray->cnt : -1,
        gsworld_getMap());

    if (!func_80320708()) {
        eeprom_writeBlocks(0, 0, (void *) PHYS_TO_K0(0x00BC7230), EEPROM_MAXBLOCKS);
    }

    spawnQueue_unlock();
    sky_draw(gfx, mtx, vtx);
    core2_34790_getClipDistances(&near, &far);
    viewport_setNearAndFar(near, far);
    viewport_setRenderViewportAndPerspectiveMatrix(gfx, mtx);

    if (mapModel_has_xlu_bin()) {
        mapModel_opa_draw(gfx, mtx, vtx);
        if (!game_is_frozen()) {
            leveloverlay_drawCallback(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            player_draw(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            // TEMPORARY skip cube draw due to missing world data
            // func_80302C94(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            jiggylist_draw(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            func_803500D8(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            // TEMPORARY skip bubble/particle draw
    // func_802F2ED0(func_8032994C(), gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            partEmitMgr_drawPass0(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            mapModel_xlu_draw(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            core2_A5BC0_drawUnknownMarkers(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            partEmitMgr_drawPass1(gfx, mtx, vtx);
        }
        if (!game_is_frozen()) {
            func_8034F6F0(gfx, mtx, vtx);
        }
        func_802D520C(gfx, mtx, vtx);
    } else {
        mapModel_opa_draw(gfx, mtx, vtx);
        leveloverlay_drawCallback(gfx, mtx, vtx);
        func_8034F6F0(gfx, mtx, vtx);
        player_draw(gfx, mtx, vtx);
        // TEMPORARY skip cube draw due to missing world data
        // func_80302C94(gfx, mtx, vtx);
        core2_A5BC0_drawUnknownMarkers(gfx, mtx, vtx);
        jiggylist_draw(gfx, mtx, vtx);
        func_803500D8(gfx, mtx, vtx);
        // TEMPORARY skip bubble/particle draw
    // func_802F2ED0(func_8032994C(), gfx, mtx, vtx);
        func_802D520C(gfx, mtx, vtx);
        partEmitMgr_draw(gfx, mtx, vtx);
    }

    if (!game_is_frozen()) {
        func_80350818(gfx, mtx, vtx);
    }

    if (!game_is_frozen()) {
        func_802BBD0C(gfx, mtx, vtx);
    }

    spawnQueue_lock();
}

void gsworld_stub1(s32 arg0, s32 arg1, s32 arg2) {}

enum map_e gsworld_getMap(void) {
    return sGsWorldData.map;
}

s32 gsworld_getExit() {
    return sGsWorldData.exit;
}

void gsworld_transitionToExit(s32 exit) {
    transitionToMap(sGsWorldData.map, exit, 1);
}

s32 gsworld_getUnk0() {
    return sGsWorldData.unk0;
}

void gsworld_free(void) {
    func_80255A14();
    gsworld_setUnk0(3);
    func_8034F734();
    func_803500E8();
    func_80350BC8();
    func_8030F1D0();
    gcparade_free();//null
    leveloverlay_releaseCallback_OnlyFP();
    func_803518E8();
    func_802D48F0();
    func_803224FC();
    func_8028E644();
    leveloverlay_releaseCallback_NotFP();
    func_80341A54();
    spawnQueue_free();
    print_freeBoldLetterFont();
    func_802FAC3C();
    bundle_free();
    commonParticle_freeAllParticles();
    func_8033FA24();
    func_80344C80();
    animsprite_terminate();
    animBinCache_free();
    func_802BC10C();
    ncCameraNodeList_free();
    pem_freeDependencies();
    pem_freeAll();
    partEmitMgr_free();
    func_802F7CE0();
    func_8031F9E0();
    func_80323100();
    cubeList_free();
    func_8031B710();
    mapModel_free();
    propModelList_free();
    lighting_free();
    sky_free();
    func_8034C8D8();
    func_80323238();
    func_803343AC();
    func_803308A0();
    func_8032AEB4();
    func_8033297C();
    func_803231E8();
    func_80320B7C();
    func_802BAF20();
    code7AF80_freeTotalCounts();
    func_80332A38();
    if (!func_802E4A08()) {
        itemPrint_free();
    }
    dialogBin_terminate();
    playerModel_free();
    if (!func_80322914()) {
        musicTrack_release(core2_9B650_getMusicTrackFromMap(sGsWorldData.map));
    }
    core1_7090_release();
    AnimTextureListCache_free();
    leveloverlay_debug();
    func_8033BD6C();
    func_80255198();//heap_flush_free_queue
    animCache_flushAll();
}

void gsworld_set(enum map_e map, s32 exit, bool reload) {
    LOG_BKA_INIT("start");
    if (map == MAP_1F_CS_START_RAREWARE) {
        map = MAP_1_SM_SPIRAL_MOUNTAIN;
    }
    sGsWorldData.unk0 = 3;
    sGsWorldData.map = map;
    sGsWorldData.exit = exit;
    LOG_BKA_INIT("leveloverlay_init"); leveloverlay_init();
    gsworld_setEnableUpdate(TRUE);
    gsworld_setEnableDraw(TRUE);
    LOG_BKA_INIT("func_802D2CB8"); func_802D2CB8();
    LOG_BKA_INIT("core1_7090_alloc"); core1_7090_alloc();
    if (gsworld_getMap() == MAP_8E_GL_FURNACE_FUN) {
        LOG_BKA_INIT("func_8038E7C4"); func_8038E7C4();
    }
    if (!func_80322914()) {
        LOG_BKA_INIT("musicTrack_load"); musicTrack_load(core2_9B650_getMusicTrackFromMap(sGsWorldData.map));
    }
    LOG_BKA_INIT("func_80320B84"); func_80320B84();
    LOG_BKA_INIT("AnimTextureListCache_init"); AnimTextureListCache_init();
    LOG_BKA_INIT("func_8034C97C"); func_8034C97C();
    LOG_BKA_INIT("func_8030A078"); func_8030A078();
    LOG_BKA_INIT("func_8031B718"); func_8031B718();
    LOG_BKA_INIT("playerModel_set"); playerModel_set();
    if (!func_802E4A08()) {
        LOG_BKA_INIT("itemPrint_init"); itemPrint_init();
    }
    LOG_BKA_INIT("dialogBin_initialize"); dialogBin_initialize();
    LOG_BKA_INIT("spawnQueue_malloc"); spawnQueue_malloc();
    LOG_BKA_INIT("func_803329AC"); func_803329AC();
    LOG_BKA_INIT("func_80350BFC"); func_80350BFC();
    LOG_BKA_INIT("func_80323190"); func_80323190();
    LOG_BKA_INIT("func_80332894"); func_80332894();
    LOG_BKA_INIT("func_803305AC"); func_803305AC();
    LOG_BKA_INIT("func_8031F9E8"); func_8031F9E8();
    LOG_BKA_INIT("func_80323230"); func_80323230();
    LOG_BKA_INIT("commonParticleType_init"); commonParticleType_init();
    LOG_BKA_INIT("animBinCache_init"); animBinCache_init();
    LOG_BKA_INIT("animsprite_init"); animsprite_init();
    LOG_BKA_INIT("func_80344C50"); func_80344C50();
    LOG_BKA_INIT("func_8033F9C0"); func_8033F9C0();
    LOG_BKA_INIT("ncCameraNodeList_init"); ncCameraNodeList_init();
    LOG_BKA_INIT("nccamera_init"); nccamera_init();
    LOG_BKA_INIT("partEmitMgr_init"); partEmitMgr_init();
    LOG_BKA_INIT("pem_setAllInactive"); pem_setAllInactive();
    LOG_BKA_INIT("pem_initDependencies"); pem_initDependencies();
    LOG_BKA_INIT("func_802F7D30"); func_802F7D30();
    LOG_BKA_INIT("propModelList_init"); propModelList_init();
    LOG_BKA_INIT("lighting_init"); lighting_init();
    LOG_BKA_INIT("sky_reset"); sky_reset();
    LOG_BKA_INIT("func_803343D0"); func_803343D0();
    LOG_BKA_INIT("cubeList_init"); cubeList_init();
    LOG_BKA_INIT("func_802FA69C"); func_802FA69C();
    LOG_BKA_INIT("commonParticle_init"); commonParticle_init();
    if (!reload) {
        LOG_BKA_INIT("gsworld_load"); gsworld_load(map);
    }
    LOG_BKA_INIT("func_80305990"); func_80305990(0);
    LOG_BKA_INIT("func_8030C740"); func_8030C740();
    LOG_BKA_INIT("gcdialog_init"); gcdialog_init();
    LOG_BKA_INIT("mapSpecificFlags_clearAll"); mapSpecificFlags_clearAll();
    LOG_BKA_INIT("func_803411B0"); func_803411B0();
    LOG_BKA_INIT("spawnQueue_reset"); spawnQueue_reset();
    LOG_BKA_INIT("leveloverlay_initCallback_NotFP"); leveloverlay_initCallback_NotFP();
    LOG_BKA_INIT("func_8028E4B0"); func_8028E4B0();
    LOG_BKA_INIT("leveloverlay_initCallback_OnlyFP"); leveloverlay_initCallback_OnlyFP();
    LOG_BKA_INIT("func_80323120"); func_80323120();
    LOG_BKA_INIT("func_803223AC"); func_803223AC();
    LOG_BKA_INIT("bundle_reset"); bundle_reset();
    LOG_BKA_INIT("func_8034F774"); func_8034F774();
    LOG_BKA_INIT("func_80350174"); func_80350174();
    LOG_BKA_INIT("gcparade_init"); gcparade_init();
    LOG_BKA_INIT("func_80351998"); func_80351998();
    LOG_BKA_INIT("func_802BC2CC"); func_802BC2CC(sGsWorldData.exit);
    LOG_BKA_INIT("func_802D63D4"); func_802D63D4();
    LOG_BKA_INIT("func_80255A04"); func_80255A04();
    LOG_BKA_INIT("func_802D6948"); func_802D6948();
    if (!func_802E4A08()) {
        LOG_BKA_INIT("print_resetBoldFontTexture"); print_resetBoldFontTexture();
    }
    if (map != MAP_1F_CS_START_RAREWARE) {
        LOG_BKA_INIT("func_8024F150"); func_8024F150();
    }
    LOG_BKA_INIT("complete");
}

void gsworld_reload(void) {
    gsworld_free();
    gsworld_set(sGsWorldData.map, sGsWorldData.exit, TRUE);
}

void gsworld_stub2(void) {
    gsworld_stub3(sGsWorldData.map);
}

void gsworld_setUnk0(s32 value) {
    core1_15B30_sendMesg3ToRenderThread();
    func_802BC21C(sGsWorldData.unk0, value);
    func_8028F7F4(sGsWorldData.unk0, value);
    func_8030D8A8(sGsWorldData.unk0, value);
    func_803045CC(sGsWorldData.unk0, value);
    func_80323140(sGsWorldData.unk0, value);
    func_80351A1C(sGsWorldData.unk0, value);
    func_803225B0(sGsWorldData.unk0, value);
    leveloverlay_unk14Callback(sGsWorldData.unk0, value);
    func_802F0E80(sGsWorldData.unk0, value);
    commonParticle_setActive(sGsWorldData.unk0, value);
    sGsWorldData.unk0 = value;
}

s32 gsworld_update(void) {
    u32 time_mask, time, delay;

    codeCF5F0_triggerAntiTamperMeasurement();
    func_802D5628();
    itemPrint_update();
    if (getGameMode() != GAME_MODE_4_PAUSED) {
        func_802F7E54();
    }
    if (!sEnableUpdate) {
        return 1;
    } else {
        func_802BAF40();
        func_8032AA9C();
        func_80323170();
        func_80351C48();
        func_80330FF4();
        func_8028E71C();

        time = globalTimer_getTime();
        time_mask = sHackDetected ? 0x0F : 0x1F;
        if (((time_mask & time) == 3) &&
            (overlayManager_getLoadedID() == OVERLAY_5_BEACH) &&
            (!maCastle_isSecretCheatCodeRelatedValueEqualToScrambledAddressValue() || sHackDetected))
        {
            sHackDetected = TRUE;
            for (delay = 0; delay != 150000000; delay++);
        }

        commonParticle_update();
        pem_updateAll();
        animCache_update();
        animBinCache_update();
        ncCamera_update();
        func_803045D8();
        func_80332E08();
        func_803465E4();
        func_8031B790();
        func_8034C9D4();
        propModelList_flush(1);
        sky_update();
        partEmitMgr_update();
        func_8034F918();
        func_80350250();
        #if ANTI_TAMPER
        if (!mapSpecificFlags_validateCRC1()) {
            func_8028FCBC();
        }
        #endif
        AnimTextureListCache_update();
        func_80350CA4();
        dialogBin_update();
        func_80310D2C();
        gcparade_update();
        leveloverlay_updateCallback();
        func_80321924();
        func_80334428();
        cutscenetrigger_update();
        func_802D2CDC();
        func_803306C8(1);
        func_8032AD7C(1);
        func_80322490();
        if (map_getLevel(sGsWorldData.map) == LEVEL_D_CUTSCENE) {
            func_802C79C4();
        }
        func_8032AABC();
        sns_stub();
        return 1;
    }
}

void gsworld_setEnableUpdate(bool value) {
    sEnableUpdate = value;
}

bool gsworld_getEnableUpdate() {
    return sEnableUpdate;
}

void gsworld_setEnableDraw(bool value) {
    sEnableDraw = value;
}

bool gsworld_getEnableDraw() {
    return sEnableDraw;
}

/*
Opens the setup file and reads the contents.

0x01 (GS_WORLD_START_INDICATOR_1_CUBES)
 - This section contains the cube dimensions and list.
 - Cubes are 1000 by 1000 sections of space that may have props inside.

0x02 (GS_WORLD_START_INDICATOR_2_UNUSED)
 - Unused

0x03 (GS_WORLD_START_INDICATOR_3_CAMERAS)
 - This section contains the cameras list.

0x04 (GS_WORLD_START_INDICATOR_4_LIGHTING)
 - This section contains environment lighting.
 - It's only used in a handful of maps.

0x00 (GS_WORLD_START_INDICATOR_0_END)
 - Indicates the end of the file.
*/
void gsworld_load(enum map_e map_id) {
    File *f;

    LOG_BKA_INIT("gsworld_load: start");
    core1_15B30_sendMesg3ToRenderThread();

    f = file_openMap(map_id);
    __android_log_print(ANDROID_LOG_INFO, "BKA-CORE", "gsworld_load: file_openMap returned %p", (void*)f);
    // TEMPORARY: skip world file parsing to bypass cubeList_fromFile hang
    if (f) file_close(f);
    return;

    if (!f) return;
    while (!file_isNextByteExpected(f, GS_WORLD_START_INDICATOR_0_END)) {
        if (file_isNextByteExpected(f, GS_WORLD_START_INDICATOR_2_UNUSED)) {
            LOG_BKA_INIT("gsworld_load: unused section");
        } else if (file_isNextByteExpected(f, GS_WORLD_START_INDICATOR_1_CUBES)) {
            LOG_BKA_INIT("gsworld_load: before cubeList_fromFile");
            cubeList_fromFile(f);
            LOG_BKA_INIT("gsworld_load: after cubeList_fromFile");
        } else if (file_isNextByteExpected(f, GS_WORLD_START_INDICATOR_3_CAMERAS)) {
            LOG_BKA_INIT("gsworld_load: before ncCameraNodeList_fromFile");
            ncCameraNodeList_fromFile(f);
            LOG_BKA_INIT("gsworld_load: after ncCameraNodeList_fromFile");
        } else if (file_isNextByteExpected(f, GS_WORLD_START_INDICATOR_4_LIGHTING)) {
            LOG_BKA_INIT("gsworld_load: before lightingVectorList_fromFile");
            lightingVectorList_fromFile(f);
            LOG_BKA_INIT("gsworld_load: after lightingVectorList_fromFile");
        }
    }

    file_close(f);
    LOG_BKA_INIT("gsworld_load: complete");
}

void gsworld_stub3(enum map_e map) {}
