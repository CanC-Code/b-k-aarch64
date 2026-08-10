BKModel *meshList_createModel(BKMeshList *this, BKVertexList *bk_vtx_list) {
    // MTE-safe: use __builtin_memcpy for all reads from tagged source memory
    s16 mesh_count;
    s32 total_vtx_count;
    BKModel *model;
    BKMesh *src_mesh;
    BKModelMesh *dst_mesh;
    BKModelVtxRef *vtx_ref;
    int j, i;

    if (this == NULL || bk_vtx_list == NULL) return NULL;

    // Read mesh count safely from tagged memory
    __builtin_memcpy(&mesh_count, this, sizeof(s16));
    if (mesh_count <= 0 || mesh_count > 5000) return NULL;

    total_vtx_count = meshList_getVtxCount(this);

    // Allocate output model
    model = (BKModel *) malloc(sizeof(BKModel) + (mesh_count * sizeof(BKModelMesh)) + (total_vtx_count * sizeof(BKModelVtxRef)));
    if (model == NULL) return NULL;

    model->mesh_list = this;
    model->vtx_list = bk_vtx_list;

    // Source meshes start after the BKMeshList header
    src_mesh = (BKMesh *)((uint8_t*)this + sizeof(BKMeshList));
    dst_mesh = (BKModelMesh *) model->data;

    for (i = 0; i < mesh_count; i++) {
        BKMesh tmp;
        __builtin_memcpy(&tmp, src_mesh, sizeof(BKMesh));
        dst_mesh->uid = tmp.uid;
        dst_mesh->vtx_count = tmp.vtx_count;
        vtx_ref = (BKModelVtxRef *) dst_mesh->data;

        for (j = 0; j < tmp.vtx_count; j++) {
            s16 vtx_id;
            __builtin_memcpy(&vtx_id, &src_mesh->vertices[j], sizeof(s16));
            if (vtx_id < 0 || vtx_id >= bk_vtx_list->count) { vtx_id = 0; }
            vtx_ref->vtx_id = vtx_id;
            __builtin_memcpy(&vtx_ref->v, &bk_vtx_list->vertices[vtx_id], sizeof(Vtx));
            vtx_ref++;
        }

        src_mesh = (BKMesh *) &src_mesh->vertices[tmp.vtx_count];
        dst_mesh = (BKModelMesh *) ((BKModelVtxRef *) dst_mesh->data + dst_mesh->vtx_count);
    }

    return model;
}
