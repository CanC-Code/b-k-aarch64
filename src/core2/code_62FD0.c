#include <ultra64.h>
static inline s16 bswap16(s16 v) { return (s16)__builtin_bswap16((u16)v); }
#include "functions.h"
#include "variables.h"

s32 meshList_getVtxCount(BKMeshList *this) {
    int i;
    s32 vertex_count = 0;
    s16 count = bswap16(this->count);
    BKMesh *mesh = this->data;

    for (i = 0; i < count; ++i) {
        s16 vtx_count = bswap16(mesh->vtx_count);
        vertex_count += vtx_count;
        mesh = (BKMesh *) &mesh->vertices[vtx_count];
    }

    return vertex_count;
}

BKMesh *meshList_getMesh(BKMeshList *this, s32 mesh_id) {
    int i;
    s16 count = bswap16(this->count);
    BKMesh *mesh = this->data;

    for (i = 0; i < count; i++) {
        if (bswap16(mesh->uid) == mesh_id) {
            return mesh;
        }
        mesh = (BKMesh *) &mesh->vertices[bswap16(mesh->vtx_count)];
    }

    return NULL;
}

bool meshList_meshContainsVtx(BKMeshList *this, s32 mesh_id, s16 *vtx_id) {
    int i;
    BKMesh *mesh = meshList_getMesh(this, mesh_id);

    if (mesh) {
        for (i = 0; i < mesh->vtx_count; i++) {
            if (mesh->vertices[i] == *vtx_id) {
                return TRUE;
            }
        }
    }

    return FALSE;
}
