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
