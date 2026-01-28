#include "rare_decompression.h"
#include <zlib.h>
#include <stdlib.h>
#include <string.h>
#include <android/log.h>

extern "C" {

uint8_t* decompress_rare_asset(const uint8_t* src, uint32_t src_size, uint32_t* out_size) {
    // 2 bytes magic + 4 bytes length = 6 bytes header minimum
    if (!src || src_size < 6) return nullptr;

    // Rare Magic 0x1172
    if (src[0] != 0x11 || src[1] != 0x72) {
        return nullptr; 
    }

    // Decompressed size is Big Endian (4 bytes following the magic)
    uint32_t decompLen = (src[2] << 24) | (src[3] << 16) | (src[4] << 8) | src[5];

    if (decompLen == 0 || decompLen > 32 * 1024 * 1024) return nullptr;

    uint8_t* outBuf = (uint8_t*)malloc(decompLen);
    if (!outBuf) return nullptr;

    z_stream strm;
    memset(&strm, 0, sizeof(strm));

    // ALIGNMENT FIX: Python does data[4:] AFTER dropping the 2-byte magic.
    // Total offset from 'src' start: 2 (magic) + 4 (length) = 6.
    // However, if your Python 'data' already had the magic removed, 
    // the C++ needs to be careful. 
    // Based on: res = d.decompress(data[4:]) where data starts with length...
    
    strm.next_in = (Bytef*)(src + 6); 
    strm.avail_in = src_size - 6; 
    strm.next_out = (Bytef*)outBuf;
    strm.avail_out = decompLen;

    // -15 is the windowBits for raw deflate (no zlib/gzip headers)
    if (inflateInit2(&strm, -15) != Z_OK) {
        free(outBuf);
        return nullptr;
    }

    int ret = inflate(&strm, Z_FINISH);
    inflateEnd(&strm);

    if (ret != Z_STREAM_END) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_DECOMP", "Zlib Error: %d", ret);
        free(outBuf);
        return nullptr;
    }

    if (out_size) *out_size = decompLen;
    return outBuf;
}

}
