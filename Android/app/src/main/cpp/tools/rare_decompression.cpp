// File: Android/app/src/main/cpp/tools/rare_decompression.cpp

#include "rare_decompression.h"

#include <android/log.h>
#include <zlib.h>

#include <cstdint>
#include <cstdlib>
#include <cstring>

#define LOG_TAG "BKA_DECOMP"

#define LOGI(...) \
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

#define LOGE(...) \
    __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

#define LOGW(...) \
    __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)


// ---------------------------------------------------------------------------
// Safety limits
// ---------------------------------------------------------------------------

// Prevent corrupted headers from requesting absurd allocations.
static constexpr uint32_t MAX_RARE_OUTPUT_SIZE = 0x10000000; // 256 MB

// Prevent malformed HLE metadata from reading unlimited memory.
static constexpr uint32_t MAX_HLE_COMPRESSED_SIZE = 0x10000000;


// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

static uint32_t read_be32(const uint8_t* p)
{
    return
        (static_cast<uint32_t>(p[0]) << 24) |
        (static_cast<uint32_t>(p[1]) << 16) |
        (static_cast<uint32_t>(p[2]) << 8)  |
        static_cast<uint32_t>(p[3]);
}


// ---------------------------------------------------------------------------
// Raw DEFLATE decompression (PATH B: 0x11 0x72 / 0x11 0x73)
// ---------------------------------------------------------------------------

static uint32_t inflate_raw_deflate_safe(
        const uint8_t* src,
        uint32_t src_size,
        uint8_t* dst,
        uint32_t dst_size)
{
    if (!src || src_size == 0 || !dst || dst_size == 0)
    {
        LOGE(
            "inflate rejected invalid buffer src=%p dst=%p src_size=%u dst_size=%u",
            src,
            dst,
            src_size,
            dst_size);

        return 0;
    }

    z_stream strm;
    memset(&strm, 0, sizeof(strm));

    // Force the statically linked zlib/miniz library to use its default
    // internal memory allocators to prevent ABI and struct offset mismatches.
    strm.zalloc = Z_NULL;
    strm.zfree  = Z_NULL;
    strm.opaque = Z_NULL;

    int init = inflateInit2(&strm, -15);

    if (init != Z_OK)
    {
        LOGE("inflateInit2 failed: %d", init);
        return 0;
    }

    strm.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(src));
    strm.avail_in = src_size;

    strm.next_out = reinterpret_cast<Bytef*>(dst);
    strm.avail_out = dst_size;

    int ret = Z_OK;

    while (true)
    {
        ret = inflate(&strm, Z_NO_FLUSH);

        if (ret == Z_STREAM_END)
        {
            break;
        }

        if (ret != Z_OK)
        {
            LOGE("inflate failed ret=%d avail_in=%u avail_out=%u", ret, strm.avail_in, strm.avail_out);
            inflateEnd(&strm);
            return 0;
        }

        if (strm.avail_out == 0)
        {
            LOGW("inflate output buffer exhausted");
            break;
        }

        if (strm.avail_in == 0)
        {
            LOGW("inflate input exhausted before stream end");
            break;
        }
    }

    uint32_t total_out = static_cast<uint32_t>(strm.total_out);

    inflateEnd(&strm);

    if (total_out == 0)
    {
        LOGE("inflate produced zero bytes");
        return 0;
    }

    return total_out;
}


// ---------------------------------------------------------------------------
// Standard GZIP decompression (PATH C: 0x1F 0x8B)
// ---------------------------------------------------------------------------

static uint32_t inflate_gzip_safe(
        const uint8_t* src,
        uint32_t src_size,
        uint8_t* dst,
        uint32_t dst_size)
{
    if (!src || src_size == 0 || !dst || dst_size == 0)
    {
        LOGE(
            "gzip inflate rejected invalid buffer src=%p dst=%p src_size=%u dst_size=%u",
            src,
            dst,
            src_size,
            dst_size);

        return 0;
    }

    z_stream strm;
    memset(&strm, 0, sizeof(strm));
    strm.zalloc = Z_NULL;
    strm.zfree  = Z_NULL;
    strm.opaque = Z_NULL;

    // 15 + 32 tells zlib to auto-detect zlib- or gzip-framed streams.
    int init = inflateInit2(&strm, 15 + 32);

    if (init != Z_OK)
    {
        LOGE("gzip inflateInit2 failed: %d", init);
        return 0;
    }

    strm.next_in = const_cast<Bytef*>(reinterpret_cast<const Bytef*>(src));
    strm.avail_in = src_size;

    strm.next_out = reinterpret_cast<Bytef*>(dst);
    strm.avail_out = dst_size;

    int ret = inflate(&strm, Z_FINISH);

    uint32_t total_out = static_cast<uint32_t>(strm.total_out);

    inflateEnd(&strm);

    if (ret != Z_STREAM_END && total_out == 0)
    {
        LOGE("gzip inflate failed ret=%d", ret);
        return 0;
    }

    return total_out;
}


// ---------------------------------------------------------------------------
// Rare LZSS decompression (PATH A: 0x50 0x10)
//
// This mirrors bka_rare_lzss_decompress() in rarezip.c exactly. It is kept
// as a self-contained copy here rather than shared, because rarezip.c's
// version is wired into the HLE interpreter's N64-address resolution and
// global wp/inptr call convention, which doesn't fit this file's plain
// offset-based API. If the ring-buffer format ever changes, update both.
// ---------------------------------------------------------------------------

static uint32_t lzss_decompress_bounded(
        const uint8_t* src,
        uint32_t src_size,
        uint8_t* dst,
        uint32_t dst_cap)
{
    if (!src || src_size == 0 || !dst || dst_cap == 0)
    {
        LOGE(
            "lzss_decompress_bounded rejected invalid buffer src=%p dst=%p src_size=%u dst_cap=%u",
            src,
            dst,
            src_size,
            dst_cap);

        return 0;
    }

    uint8_t ring[0x1000];
    memset(ring, 0x00, sizeof(ring));
    uint32_t ring_pos = 0xFEEu;

    const uint8_t* src_ptr = src;
    const uint8_t* src_end = src + src_size;
    uint8_t* dst_ptr = dst;
    const uint8_t* dst_end = dst + dst_cap;

    while (src_ptr < src_end && dst_ptr < dst_end)
    {
        uint8_t flags = *src_ptr++;
        for (int bit = 0; bit < 8 && src_ptr < src_end && dst_ptr < dst_end; bit++)
        {
            if (flags & (1u << bit))
            {
                if (src_ptr >= src_end) break;
                uint8_t lit = *src_ptr++;
                *dst_ptr++ = lit;
                ring[ring_pos] = lit;
                ring_pos = (ring_pos + 1u) & 0xFFFu;
            }
            else
            {
                if (src_ptr + 1 >= src_end) break;
                uint8_t b0 = *src_ptr++;
                uint8_t b1 = *src_ptr++;
                uint32_t ring_off = (uint32_t)b0 | (((uint32_t)(b1 & 0xF0u)) << 4u);
                uint32_t length = (uint32_t)(b1 & 0x0Fu) + 3u;
                for (uint32_t i = 0; i < length && dst_ptr < dst_end; i++)
                {
                    uint8_t byte = ring[(ring_off + i) & 0xFFFu];
                    *dst_ptr++ = byte;
                    ring[ring_pos] = byte;
                    ring_pos = (ring_pos + 1u) & 0xFFFu;
                }
            }
        }
    }

    uint32_t written = static_cast<uint32_t>(dst_ptr - dst);

    if (written == 0)
    {
        LOGE("lzss_decompress_bounded produced zero bytes");
    }

    return written;
}


// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

extern "C"
{

// Retained for otr_builder.cpp standalone archive extraction
uint8_t* decompress_rare_asset(
        const uint8_t* src,
        uint32_t src_size,
        uint32_t* out_size)
{
    if (out_size)
        *out_size = 0;

    if (!src || !out_size)
    {
        LOGE("decompress_rare_asset invalid arguments");
        return nullptr;
    }

    if (src_size < 8)
    {
        LOGE("Rare asset too small: %u bytes", src_size);
        return nullptr;
    }

    if (src[0] != 0x11 || src[1] != 0x72)
    {
        LOGE("Missing Rare magic: %02X %02X", src[0], src[1]);
        return nullptr;
    }

    uint32_t uncompressed_size = read_be32(src + 2);

    LOGI("Rare asset header compressed=%u expected_output=%u", src_size, uncompressed_size);

    if (uncompressed_size == 0 || uncompressed_size > MAX_RARE_OUTPUT_SIZE)
    {
        LOGE("Invalid Rare output size: %u", uncompressed_size);
        return nullptr;
    }

    uint8_t* dst = static_cast<uint8_t*>(malloc(uncompressed_size));

    if (!dst)
    {
        LOGE("Allocation failed: %u bytes", uncompressed_size);
        return nullptr;
    }

    uint32_t result = inflate_raw_deflate_safe(
            src + 6,
            src_size - 6,
            dst,
            uncompressed_size);

    if (result == 0)
    {
        LOGE("Rare decompression failed");
        free(dst);
        return nullptr;
    }

    *out_size = result;
    return dst;
}

// Implemented for resource_mgr.cpp absolute offset targeting.
//
// Dispatches on the same magic bytes as func_800005C0_locked() in
// rarezip.c (PATH A / PATH B / PATH C):
//   0x50 0x10        -> Rare LZSS, 6-byte header (2 magic + BE32 size)
//   0x11 0x72 / 0x73  -> Rare-wrapped raw DEFLATE, 6-byte header
//   0x1F 0x8B         -> standard GZIP, 2-byte header
//   anything else     -> not a recognized compressed format; returns 0 so
//                        the caller can safely fall back to a raw copy.
//
// PATH D in rarezip.c (the legacy stateful Huffman inflate, bkboot_inflate())
// is intentionally NOT mirrored here -- it depends on interpreter-global
// state (huft pool, wp/inptr) tied to the HLE call convention and was a
// last-resort fallback in the original boot code. In practice every real
// asset is expected to match A/B/C; if you start seeing "no known
// compression magic" warnings for data you know is compressed, that's the
// signal PATH D coverage is actually needed here too.
uint32_t decompress_rare_to_offset(
    const uint8_t* src,
    uint32_t src_size,
    uint8_t* out_buffer,
    uint32_t out_offset,
    uint32_t out_size)
{
    if (!src || !out_buffer)
    {
        LOGE("decompress_rare_to_offset invalid pointer");
        return 0;
    }

    if (src_size < 6)
    {
        LOGW("decompress_rare_to_offset: src_size=%u too small for a compression header, skipping", src_size);
        return 0;
    }

    if (src_size > MAX_HLE_COMPRESSED_SIZE)
    {
        LOGE("Invalid compressed size=%u", src_size);
        return 0;
    }

    if (out_size == 0 || out_size > MAX_RARE_OUTPUT_SIZE)
    {
        LOGE("Invalid output size=%u", out_size);
        return 0;
    }

    uint8_t* dst = out_buffer + out_offset;
    uint8_t magic0 = src[0];
    uint8_t magic1 = src[1];

    LOGI("decompress_rare_to_offset: magic=%02X %02X out_offset=%u (compressed<=%u, expected=%u)",
         magic0, magic1, out_offset, src_size, out_size);

    // PATH A: Rare LZSS (0x50 0x10)
    if (magic0 == 0x50 && magic1 == 0x10)
    {
        return lzss_decompress_bounded(src + 6, src_size - 6, dst, out_size);
    }

    // PATH B: Rare-wrapped raw DEFLATE (0x11 0x72 / 0x11 0x73)
    if (magic0 == 0x11 && (magic1 == 0x72 || magic1 == 0x73))
    {
        return inflate_raw_deflate_safe(src + 6, src_size - 6, dst, out_size);
    }

    // PATH C: standard GZIP (0x1F 0x8B)
    if (magic0 == 0x1F && magic1 == 0x8B)
    {
        uint32_t gzipAvail = (src_size > 2) ? (src_size - 2) : 0;
        return inflate_gzip_safe(src + 2, gzipAvail, dst, out_size);
    }

    LOGW("decompress_rare_to_offset: no known compression magic (%02X %02X) at offset %u -- treating as uncompressed",
         magic0, magic1, out_offset);
    return 0;
}

}
