#include "rare_decompression.h"
#include <zlib.h>
#include <stdlib.h>
#include <string.h>

extern "C" {

uint8_t* decompress_rare_asset(const uint8_t* src, uint32_t src_size, uint32_t* out_size) {
    // 1. Validation: Minimum header size is 6 bytes (2 magic + 4 length)
    if (!src || src_size < 6) return nullptr;

    // 2. Rare Magic Header check (0x1172)
    if (src[0] != 0x11 || src[1] != 0x72) return nullptr;

    // 3. Grab decompressed size (Big Endian)
    uint32_t decompLen = (src[2] << 24) | (src[3] << 16) | (src[4] << 8) | src[5];
    
    if (decompLen == 0) return nullptr;

    uint8_t* outBuf = (uint8_t*)malloc(decompLen);
    if (!outBuf) return nullptr;

    // 4. Setup Zlib stream
    z_stream strm;
    memset(&strm, 0, sizeof(strm));
    
    strm.next_in = (Bytef*)(src + 6); 
    strm.avail_in = src_size - 6; 
    strm.next_out = (Bytef*)outBuf;
    strm.avail_out = decompLen;

    // -15 is the window bit for raw deflate (no zlib/gzip headers)
    if (inflateInit2(&strm, -15) != Z_OK) {
        free(outBuf);
        return nullptr;
    }

    // 5. Decompress
    int ret = inflate(&strm, Z_FINISH);
    inflateEnd(&strm);

    if (ret != Z_STREAM_END) {
        free(outBuf);
        return nullptr;
    }

    if (out_size) {
        *out_size = decompLen;
    }
    
    return outBuf;
}

}
