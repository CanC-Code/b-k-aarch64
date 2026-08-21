#ifndef BANJO_KAZOOIE_CORE2_VLA_H
#define BANJO_KAZOOIE_CORE2_VLA_H

#include <ultra64.h>

typedef struct variable_length_array{
    s32 elem_size;
    void * begin;
    void * end;
    void * mem_end;
    u8  data[];
}VLA;

#define vector(T) struct variable_length_array
//^defined to keep element type with vla

/* vla - variable length array*/
void    vector_clear(VLA *this);
void *  vector_getBegin(VLA *this);
void *  vector_at(VLA *this, u32 n);
s32     vector_getIndex(VLA *this, void *element);
s32     vector_size(VLA *this);
void *  vector_getEnd(VLA *this);
void *  vector_pushBackNew(VLA **thisPtr);
void *  vector_insertNew(VLA **thisPtr, s32 indx);
void    vector_free(VLA *this);
VLA *   vector_new(u32 elemSize, u32 cnt);
void    vector_remove(VLA *this, u32 indx);
void    vector_popBack_n(VLA *this, u32 n);
void    vector_assign(VLA *this, s32 indx, void* value);
VLA *   vector_defrag(VLA *this);

#endif
