#include <ultra64.h>
#include <android/log.h>
#include "functions.h"
#include "variables.h"

void animVerticesList_setCoords(BKAnimVerticesList *this, BKVertexList *bk_vtx_list, s32 index, f32 coords[3]) {
    Vtx *vtx, *vtx_list;
    int i;
    BKAnimVertices *anim_vertices;

    vtx_list = vtxList_getVertices(bk_vtx_list);
    anim_vertices = this->data;

    while (index != 0) {
        anim_vertices = (BKAnimVertices *) ((s16*)(anim_vertices + 1) + (anim_vertices->vtx_count - 1)); // TODO: Remove this ugly pointer calculation
        index--;
    }

    for (i = 0; i < anim_vertices->vtx_count; i++) {
        vtx = &vtx_list[anim_vertices->vtx_list[i]];
        vtx->v.ob[0] = coords[0];
        vtx->v.ob[1] = coords[1];
        vtx->v.ob[2] = coords[2];
    }
}

void animVerticesList_transform(BKAnimVerticesList *this, BKVertexList *bk_vtx_list, AnimMtxList *mtx_list) {
    Vtx *vtx, *vtx_list;
    int j;
    BKAnimVertices *anim_vertices;
    s16 transformed_coords[3];
    s32 mtx_index;
    int i;
    int vtx_total;
    extern int bka_is_readable(void*);

    /* port 2026-10-11: bound both variable-length walks.  Garbage anim
       bin data made this function write past the end of vtx_list and
       SEGV_ACCERR at +244 (index 976 into a much smaller array). */
    if (this == NULL || bk_vtx_list == NULL || mtx_list == NULL) return;
    if (this->count <= 0 || this->count > 1024) return;

    vtx_list = vtxList_getVertices(bk_vtx_list);
    vtx_total = vtxList_getVtxCount(bk_vtx_list);
    if (vtx_list == NULL || vtx_total <= 0 || vtx_total > 0x2000) return;

    anim_vertices = this->data;
    mtx_index = -2;

    for(i = 0; i < this->count; i++) {
        if (!bka_is_readable(anim_vertices)) break;
        if (anim_vertices->vtx_count <= 0 ||
            anim_vertices->vtx_count > vtx_total) break;
        if (mtx_index != anim_vertices->anim_index) {
            mtx_index = anim_vertices->anim_index;
            mlMtxSet(animMtxList_get(mtx_list, mtx_index));
        }
        mlMtx_apply_vec3s(transformed_coords, anim_vertices->coord);
        for (j = 0; j < anim_vertices->vtx_count; j++) {
            int __idx = anim_vertices->vtx_list[j];
            if (__idx < 0 || __idx >= vtx_total) continue;
            vtx = &vtx_list[__idx];
            vtx->v.ob[0] = transformed_coords[0];
            vtx->v.ob[1] = transformed_coords[1];
            vtx->v.ob[2] = transformed_coords[2];
        }

        anim_vertices = (BKAnimVertices *) ((s16*)(anim_vertices + 1) + (anim_vertices->vtx_count - 1));
    }

    osWritebackDCache(vtx_list, vtx_total * sizeof(Vtx));
}
