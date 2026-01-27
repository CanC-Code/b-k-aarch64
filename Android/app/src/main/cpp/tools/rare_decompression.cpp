// Android/app/src/main/cpp/tools/rare_decompression.cpp
#include "rare_decompression.h"
#include <zlib.h>
#include <stdlib.h>
#include <string.h>

/**
 * Decompresses a Rare ZLB asset.
 * Mirrors the logic of rareunzip.py:
 * 1. Checks for 0x1172 magic (2 bytes)
 * 2. Reads decompressed length (4 bytes)
 * 3. Inflates the remainder using raw deflate (wbits -15)
 */
uint8_t* decompress_rare_asset(const uint8_t* src, uint32_t src_size, uint32_t* out_size) {
    // 1. Validation: Minimum header size is 6 bytes (2 magic + 4 length)
    if (src_size < 6) return nullptr;

    // 2. Rare Magic Header check
    if (src[0] != 0x11 || src[1] != 0x72) return nullptr;

    // 3. Grab decompressed size (Big Endian)
    // This is used to allocate the output buffer
    uint32_t decompLen = (src[2] << 24) | (src[3] << 16) | (src[4] << 8) | src[5];
    
    if (decompLen == 0) return nullptr;

    uint8_t* outBuf = (uint8_t*)malloc(decompLen);
    if (!outBuf) return nullptr;

    // 4. Setup Zlib stream
    z_stream strm;
    memset(&strm, 0, sizeof(strm));
    
    strm.next_in = (Bytef*)(src + 6); 
    strm.avail_in = src_size - 6; // Correctly calculate remaining compressed data
    strm.next_out = (Bytef*)outBuf;
    strm.avail_out = decompLen;

    // -15 is the window bit for raw deflate, matching Python's wbits=-15
    if (inflateInit2(&strm, -15) != Z_OK) {
        free(outBuf);
        return nullptr;
    }

    // 5. Decompress
    int ret = inflate(&strm, Z_FINISH);
    inflateEnd(&strm);

    // Z_STREAM_END means we hit the end of the compressed block successfully
    if (ret != Z_STREAM_END) {
        free(outBuf);
        return nullptr;
    }

    *out_size = decompLen;
    return outBuf;
}
