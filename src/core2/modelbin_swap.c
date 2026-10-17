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
