#include <ultra64.h>
#include "functions.h"
#include "core2/vla.h"

/* VARIABLE LENGTH ARRAY */

void vector_clear(VLA *this){
    this->end = this->begin;
}

void *vector_getBegin(VLA *this){
    return this->begin;
}

void *vector_at(VLA *this, u32 n){
    return (void *)((u32) this->begin + n*this->elem_size);
}

s32 vector_getIndex(VLA *this, void *elemPtr){
    return ((s32)elemPtr - (intptr_t)this->begin)/(intptr_t)this->elem_size;
}

s32 vector_size(VLA *this){
    return ((intptr_t)this->end - (intptr_t)this->begin)/this->elem_size;
}

void *vector_getEnd(VLA *this){
    return this->end;
}

void *vector_pushBackNew(VLA **thisPtr){
    void *retVal;
    VLA* this;
    s32 size;
    s32 mem_size;

    this = *thisPtr;
    if(this->end == this->mem_end){
        size = ((intptr_t)this->end - (intptr_t)this->begin)/this->elem_size;
        mem_size = size + 5;
        this = realloc(this,  mem_size*this->elem_size + sizeof(VLA));
        this->begin = &this->data;
        this->end = (u8 *)this->begin + size* this->elem_size;
        this->mem_end = (u8 *)this->begin + mem_size* this->elem_size;
        *thisPtr = this; 
    }
    retVal = this->end;
    this->end = (void *)((intptr_t)this->end + this->elem_size);
    return retVal;
}

void *vector_insertNew(VLA **thisPtr, s32 indx){
    VLA *this;
    s32 i;

    vector_pushBackNew(thisPtr);
    this = *thisPtr;
    i = ((intptr_t)this->end - (intptr_t)this->begin)/this->elem_size;
    while(indx < --i){
        memcpy((void *)((intptr_t)this->begin + (i)*this->elem_size), (void *)((intptr_t)this->begin + (i -1)*this->elem_size), this->elem_size);
    }
    return (void *)((intptr_t)this->begin +  indx*this->elem_size);
}

void vector_free(VLA *this){
    free(this);
}

VLA *vector_new(u32 elemSize, u32 cnt){
    VLA *this = malloc(cnt*elemSize + sizeof(VLA));
    this->elem_size = elemSize;
    this->begin = &this->data;
    this->end = &this->data;
    this->mem_end = (u8*)this->end + cnt*elemSize;
    return this;
}

void vector_remove(VLA *this, u32 indx){
    u32 elemOffset = (u32)this->begin + indx * this->elem_size;\
    u32 nextOffset = (u32)this->begin + (indx + 1) * this->elem_size;\
    u32 size = (u32)this->end - (u32)this->begin;
    
    memcpy((void *)elemOffset, (void *)nextOffset, size - (indx + 1) * this->elem_size);
    this->end = (void *)((u32)this->end - this->elem_size);
}


void vector_popBack_n(VLA *this, u32 n){
    this->end = (void *)((u32)this->end - n * this->elem_size);
}

void vector_assign(VLA *this, s32 indx, void* value){
    memcpy((void*)((intptr_t)this->begin + indx * this->elem_size), value, this->elem_size);
}

VLA * vector_defrag(VLA *this){
   s32 oldSize;
   s32 oldMemSize;

   oldSize = (intptr_t)this->end - (intptr_t)this->begin;
   oldMemSize = (intptr_t)this->mem_end - (intptr_t)this->begin;
   this = (VLA *)defrag(this);
   this->begin = &this->data;
   this->end = (void *)((intptr_t)this->begin + oldSize);
   this->mem_end = (void *)((intptr_t)this->begin + oldMemSize);
   return this;
}
