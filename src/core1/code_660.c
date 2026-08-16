#include "boot/rarezip.h"

extern struct huft_s gGlobalHuffTable;
#include <ultra64.h>
#include "core1/core1.h"


static int _rarezip_uncompress(u8 **arg0, u8 **arg1, struct huft_s * arg2);

#define COMP_HEADER_SIZE 6

//border[]= {    /* Order of the bit length code lengths */
u8  D_80275670[] = { 
    16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15
};

// static ush cplens[] = {         /* Copy lengths for literal codes 257..285 */
u16 D_80275684[] = { 
    3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31,
    35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258, 0, 0
};
//         /* note: see note #13 above about the 258 in this list. */

// static uch cplext[] = {         /* Extra bits for literal codes 257..285 */
u8 D_802756C4[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2,
    3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0, 99, 99
}; /* 99==invalid */

// static ush cpdist[] = {         /* Copy offsets for distance codes 0..29 */
u16 D_802756E4[] = {
    1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193,
    257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145,
    8193, 12289, 16385, 24577
};

// static uch cpdext[] = {         /* Extra bits for distance codes */
u8 D_80275720[] = {
        0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
        7, 7, 8, 8, 9, 9, 10, 10, 11, 11,
        12, 12, 13, 13
};

// ush mask_bits[] = {
u16 D_80275740[] = {
    0x0000,
    0x0001, 0x0003, 0x0007, 0x000f, 0x001f, 0x003f, 0x007f, 0x00ff,
    0x01ff, 0x03ff, 0x07ff, 0x0fff, 0x1fff, 0x3fff, 0x7fff, 0xffff
};

s32 D_80275764 = 9; //lbits
s32 D_80275768 = 6; //dbits

/* .data */
u8 pad_8027BF08[0x8];
u8 *D_8027BF10; //inbuf
u8 *D_8027BF14; //slide
u32 D_8027BF18; //inptr
u32 D_8027BF1C; //wp
u32 D_8027BF24; //bb
u32 D_8027BF28; //bk
u32 D_8027BF2C; //crc1
u32 D_8027BF30; //crc2
u32 D_8027BF34; //hufts

static int _rarezip_inflate(u8 * src, u8 * dst, struct huft_s * arg2);

/* .code */
u32 rarezip_get_uncompressed_size(u8 *arg0) {
    // N64 is big-endian, ARM64 is little-endian - need byteswap
    s32 size;
    memcpy(&size, arg0 + 2, 4);
    return __builtin_bswap32(size);
}
 
void rarezip_init(void){
    D_8027BF00 = &gGlobalHuffTable;
}

void rarezip_inflate(u8 *src, u8 *dst){
    _rarezip_inflate(src, dst, D_8027BF00);
}

void rarezip_uncompress(u8 **srcPtr, u8 **dstPtr){
    //updates in and out buffer ptrs,
    _rarezip_uncompress(srcPtr, dstPtr, D_8027BF00);
}

void func_8023E0E8(void){
    return;
}

static int _rarezip_inflate(u8 * src, u8 * dst, struct huft_s * arg2){
    // Set boot/inflate.c globals (the version the linker keeps)
    extern u8 *inflate_inbuf;
    extern u8 *inflate_slide;
    extern struct huft_s *inflate_huft;
    extern u32 inflate_inptr;
    extern u32 inflate_wp;
    
    inflate_inbuf = (u8 *)((uintptr_t)src & 0xFFFFFFFFFFFFULL);
    inflate_slide = (u8 *)((uintptr_t)dst & 0xFFFFFFFFFFFFULL);
    inflate_huft = (struct huft_s *)((uintptr_t)arg2 & 0xFFFFFFFFFFFFULL);
    inflate_inbuf += COMP_HEADER_SIZE;
    inflate_wp = 0;
    inflate_inptr = 0;
    
    // Also set D_ globals for any code that reads them
    D_8027BF10 = inflate_inbuf;
    D_8027BF14 = inflate_slide;
    D_8027BF20 = (struct huft_s *)inflate_huft;
    D_8027BF1C = 0;
    D_8027BF18 = 0;
    
    inflate();
    
    // Sync back
    D_8027BF1C = inflate_wp;
    D_8027BF18 = inflate_inptr;
    
    return inflate_wp;
}

static int _rarezip_uncompress(u8 **srcPtr, u8 **dstPtr, struct huft * arg2){
    int result;
    extern u32 inflate_wp;
    extern u32 inflate_inptr;
    
    result = _rarezip_inflate(*srcPtr, *dstPtr, arg2);
    *dstPtr = *dstPtr + inflate_wp;
    *dstPtr = ((uintptr_t)*dstPtr & 0xF) ? (u8 *) ((uintptr_t)*dstPtr & -0x10) + 0x10: *dstPtr;
    *srcPtr = *srcPtr + inflate_inptr + COMP_HEADER_SIZE;
    return result;
}
