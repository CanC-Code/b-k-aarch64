// Android/app/src/main/cpp/tools/rare_decompression.cpp
#include "rare_decompression.h"
#include <zlib.h>
#include <stdlib.h>

uint8_t* decompress_rare_asset(const uint8_t* src, uint32_t* out_size) {
    // Rare Magic Header check (0x1172)
    if (src[0] != 0x11 || src[1] != 0x72) return nullptr;

    // Grab decompressed size from the Rare header (Big Endian)
    uint32_t decompLen = (src[2] << 24) | (src[3] << 16) | (src[4] << 8) | src[5];
    *out_size = decompLen;

    uint8_t* outBuf = (uint8_t*)malloc(decompLen);
    
    z_stream strm = {0};
    strm.next_in = (Bytef*)(src + 6); // Skip the 6-byte Rare header
    strm.avail_in = 0xFFFFFF;        // Large enough to cover the compressed chunk
    strm.next_out = (Bytef*)outBuf;
    strm.avail_out = decompLen;

    // -15 is the "Perfect" window bit for raw deflate (no headers) used in BK
    if (inflateInit2(&strm, -15) != Z_OK) return nullptr;
    
    int ret = inflate(&strm, Z_FINISH);
    inflateEnd(&strm);

    if (ret != Z_STREAM_END && ret != Z_OK) {
        free(outBuf);
        return nullptr;
    }

    return outBuf;
}
