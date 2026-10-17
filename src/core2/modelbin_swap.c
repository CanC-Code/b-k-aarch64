/* modelbin_swap.c — one-time BE→LE swap of loaded model bins.
 *
 * The port loads raw N64 ROM bytes, which are big-endian. Every reader
 * currently byte-swaps on access. This is fragile (37 files, ~900 read
 * sites, mixed swap conventions, double-swap bugs). Fix: swap the entire
 * model bin once after asset load. After this runs, every byte in the
 * bin is host-native and no reader has to swap anything.
 *
 * Convention:
 *   - magic_number is stored BE on disk. Native LE read = 0x0B000000.
 *   - After swap, magic_number reads 0x0000000B. That's the double-swap
 *     guard.
 */
#include <ultra64.h>
#include <android/log.h>
#include "functions.h"
#include "variables.h"
#include "model.h"

#define BKA_SWAP_TAG "BKA-SWAP"
#define SW16(v) ((u16)__builtin_bswap16((u16)(v)))
#define SW32(v) ((u32)__builtin_bswap32((u32)(v)))

/* Swap a BKVertexList in place at offset `off` inside `bin`. */
static void bka_swap_vtx_list(u8 *bin, s32 off, s32 bin_size) {
    if (off <= 0 || off + (s32)sizeof(BKVertexList) > bin_size) return;
    BKVertexList *v = (BKVertexList *)(bin + off);
    v->minCoord[0]    = (s16)SW16(v->minCoord[0]);
    v->minCoord[1]    = (s16)SW16(v->minCoord[1]);
    v->minCoord[2]    = (s16)SW16(v->minCoord[2]);
    v->maxCoord[0]    = (s16)SW16(v->maxCoord[0]);
    v->maxCoord[1]    = (s16)SW16(v->maxCoord[1]);
    v->maxCoord[2]    = (s16)SW16(v->maxCoord[2]);
    v->centerCoord[0] = (s16)SW16(v->centerCoord[0]);
    v->centerCoord[1] = (s16)SW16(v->centerCoord[1]);
    v->centerCoord[2] = (s16)SW16(v->centerCoord[2]);
    v->local_norm     = (s16)SW16(v->local_norm);
    v->count          = (s16)SW16(v->count);
    v->global_norm    = (s16)SW16(v->global_norm);
    s32 cnt = v->count;
    if (cnt < 0 || cnt > 0x10000) return;
    for (s32 i = 0; i < cnt; i++) {
        Vtx *x = &v->vertices[i];
        x->v.ob[0] = (s16)SW16(x->v.ob[0]);
        x->v.ob[1] = (s16)SW16(x->v.ob[1]);
        x->v.ob[2] = (s16)SW16(x->v.ob[2]);
        x->v.tc[0] = (s16)SW16(x->v.tc[0]);
        x->v.tc[1] = (s16)SW16(x->v.tc[1]);
        /* cn are bytes; no swap */
    }
}

/* Swap a BKMeshList in place at offset `off` inside `bin`. */
static void bka_swap_mesh_list(u8 *bin, s32 off, s32 bin_size) {
    if (off <= 0 || off + (s32)sizeof(BKMeshList) > bin_size) return;
    BKMeshList *m = (BKMeshList *)(bin + off);
    m->count = (s16)SW16(m->count);
    s32 cnt = m->count;
    if (cnt < 0 || cnt > 0x4000) return;
    BKMesh *mesh = m->data;
    for (s32 i = 0; i < cnt; i++) {
        if ((u8*)mesh - bin + (s32)sizeof(BKMesh) > bin_size) return;
        mesh->uid       = (s16)SW16(mesh->uid);
        mesh->vtx_count = (s16)SW16(mesh->vtx_count);
        s32 vc = mesh->vtx_count;
        if (vc < 0 || vc > 0x2000) return;
        for (s32 j = 0; j < vc; j++) {
            mesh->vertices[j] = (s16)SW16(mesh->vertices[j]);
        }
        mesh = (BKMesh *)&mesh->vertices[vc];
    }
}

/* Swap a BKCollisionList in place at offset `off` inside `bin`.
 * Layout after header: BKCollisionGeometry[geo_cnt], then
 * BKCollisionTriangle[tri_cnt]. */
static void bka_swap_coll_list(u8 *bin, s32 off, s32 bin_size) {
    if (off <= 0 || off + (s32)sizeof(BKCollisionList) > bin_size) return;
    BKCollisionList *c = (BKCollisionList *)(bin + off);
    c->unk0[0] = (s16)SW16(c->unk0[0]);
    c->unk0[1] = (s16)SW16(c->unk0[1]);
    c->unk0[2] = (s16)SW16(c->unk0[2]);
    c->unk6[0] = (s16)SW16(c->unk6[0]);
    c->unk6[1] = (s16)SW16(c->unk6[1]);
    c->unk6[2] = (s16)SW16(c->unk6[2]);
    c->unkC   = (s16)SW16(c->unkC);
    c->unkE   = (s16)SW16(c->unkE);
    c->unk10  = (s16)SW16(c->unk10);
    c->unk12  = (s16)SW16(c->unk12);
    c->unk14  = (s16)SW16(c->unk14);

    s32 geo_cnt = c->unk10;
    if (geo_cnt < 0 || geo_cnt > 0x4000) return;
    BKCollisionGeometry *geos = (BKCollisionGeometry *)(c + 1);
    if ((u8*)geos - bin + geo_cnt * (s32)sizeof(BKCollisionGeometry) > bin_size) return;
    for (s32 i = 0; i < geo_cnt; i++) {
        geos[i].start_tri_index = (s16)SW16(geos[i].start_tri_index);
        geos[i].tri_count       = (s16)SW16(geos[i].tri_count);
    }

    s32 tri_cnt = c->unk14;
    if (tri_cnt < 0 || tri_cnt > 0x20000) return;
    BKCollisionTriangle *tris = (BKCollisionTriangle *)(geos + geo_cnt);
    if ((u8*)tris - bin + tri_cnt * (s32)sizeof(BKCollisionTriangle) > bin_size) return;
    for (s32 i = 0; i < tri_cnt; i++) {
        tris[i].unk0[0] = (s16)SW16(tris[i].unk0[0]);
        tris[i].unk0[1] = (s16)SW16(tris[i].unk0[1]);
        tris[i].unk0[2] = (s16)SW16(tris[i].unk0[2]);
        tris[i].unk6    = (s16)SW16(tris[i].unk6);
        tris[i].flags   = (s32)SW32(tris[i].flags);
    }
}

/* Swap a loaded BKModelBin buffer in place, once, after asset load.
 *
 * Detects and skips already-swapped bins via the magic number:
 *   - On LE host, raw BE bytes 00 00 00 0B read as 0x0B000000 (unswapped)
 *   - After this function runs, magic_number reads 0x0000000B (swapped)
 * Either the whole bin is native, or none of it is — never in between.
 *
 * Sub-lists handled here: BKVertexList, BKMeshList, BKCollisionList.
 * Others (geo cmds, textures, animation, unk14, camera) are covered by
 * their own per-site swaps or will be added in follow-up commits. */
void modelbin_byteswap_inplace(BKModelBin *bin, s32 bin_size) {
    if (!bin || bin_size < (s32)sizeof(BKModelBin)) return;

    u32 magic_native = bin->magic_number;
    if (magic_native == 0x0000000Bu) return;  /* already swapped */
    if (magic_native != 0x0B000000u) {
        __android_log_print(ANDROID_LOG_WARN, BKA_SWAP_TAG,
            "not a model bin, magic=0x%08X", magic_native);
        return;
    }

    /* Save header offsets before swapping the header in place. */
    s32 geo_off     = (s32)SW32(bin->geo_list_offset);
    s32 vtx_off     = (s32)SW32(bin->vtx_list_offset);
    s32 mesh_off    = (s32)SW32(bin->mesh_list_offset);
    s32 coll_off    = (s32)SW32(bin->collision_list_offset);
    s32 anim_off    = (s32)SW32(bin->animation_list_offset);
    s32 gfx_off     = (s32)SW32(bin->gfx_list_offset);
    s32 unk14_off   = (s32)SW32(bin->unk14_list_offset);
    s32 cam_off     = (s32)SW32(bin->camera_area_list_offset);
    s32 animvtx_off = (s32)SW32(bin->anim_vertices_list_offset);
    s32 animtex_off = (s32)SW32(bin->animated_texture_list_offset);
    s32 tex_len     = (s32)SW16((u16)bin->texture_list_offset);
    s16 geo_type    = (s16)SW16((u16)bin->geo_type);

    /* Swap header in place. */
    bin->magic_number                 = 0x0000000B;
    bin->geo_list_offset              = geo_off;
    bin->texture_list_offset          = (s16)tex_len;
    bin->geo_type                     = geo_type;
    bin->gfx_list_offset              = gfx_off;
    bin->vtx_list_offset              = vtx_off;
    bin->unk14_list_offset            = unk14_off;
    bin->animation_list_offset        = anim_off;
    bin->collision_list_offset        = coll_off;
    bin->camera_area_list_offset      = cam_off;
    bin->mesh_list_offset             = mesh_off;
    bin->anim_vertices_list_offset    = animvtx_off;
    bin->animated_texture_list_offset = animtex_off;
    bin->unk30                        = (u16)SW16(bin->unk30);
    bin->vertex_count                 = (u16)SW16(bin->vertex_count);
    {
        u32 fbits;
        __builtin_memcpy(&fbits, &bin->unk34, 4);
        fbits = SW32(fbits);
        __builtin_memcpy(&bin->unk34, &fbits, 4);
    }

    /* Dispatch to per-sublist helpers. */
    bka_swap_vtx_list(bin, vtx_off, bin_size);
    bka_swap_mesh_list(bin, mesh_off, bin_size);
    bka_swap_coll_list(bin, coll_off, bin_size);

    __android_log_print(ANDROID_LOG_INFO, BKA_SWAP_TAG,
        "swapped bin=%p vtx_off=%d mesh_off=%d coll_off=%d",
        (void*)bin, vtx_off, mesh_off, coll_off);
}
