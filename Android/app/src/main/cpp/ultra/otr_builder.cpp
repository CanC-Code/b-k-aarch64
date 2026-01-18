// File: Android/app/src/main/cpp/ultra/otr_builder.cpp
// Purpose: Fully integrated BK.OTR builder & loader for Android
// Author: CCVO
// Features:
//   - Load precomputed OTR BIN
//   - Auto-detect correct BIN via ROM SHA1
//   - Progress tracking for UI
//   - Self-contained SHA1 implementation (no OpenSSL required)

#include <cstdint>
#include <vector>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <string>
#include <unordered_map>
#include <android/log.h>

#define LOG_TAG "BKA_OTR"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ---- Global in-memory OTR ----
static std::vector<uint8_t> BK_OTR;
static std::atomic<float> g_progress{0.0f};

// ---- Segment descriptor from BIN ----
struct OTRSegment {
    uint32_t offset;
    uint32_t size;
};

// ------------------------
// Minimal SHA1 implementation
// ------------------------
struct SHA1Context {
    uint32_t h[5];
    uint64_t len;
    uint8_t block[64];
    size_t block_len;
};

static void sha1Init(SHA1Context* ctx) {
    ctx->h[0] = 0x67452301;
    ctx->h[1] = 0xEFCDAB89;
    ctx->h[2] = 0x98BADCFE;
    ctx->h[3] = 0x10325476;
    ctx->h[4] = 0xC3D2E1F0;
    ctx->len = 0;
    ctx->block_len = 0;
}

static uint32_t rol(uint32_t value, uint32_t bits) { return (value << bits) | (value >> (32 - bits)); }

static void sha1ProcessBlock(SHA1Context* ctx, const uint8_t* block) {
    uint32_t w[80];
    for (int i = 0; i < 16; i++) {
        w[i] = (block[i*4 + 0] << 24) | (block[i*4 + 1] << 16) | (block[i*4 + 2] << 8) | (block[i*4 + 3]);
    }
    for (int i = 16; i < 80; i++) {
        w[i] = rol(w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16], 1);
    }

    uint32_t a = ctx->h[0], b = ctx->h[1], c = ctx->h[2], d = ctx->h[3], e = ctx->h[4];

    for (int i = 0; i < 80; i++) {
        uint32_t f, k;
        if (i < 20) { f = (b & c) | ((~b) & d); k = 0x5A827999; }
        else if (i < 40) { f = b ^ c ^ d; k = 0x6ED9EBA1; }
        else if (i < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC; }
        else { f = b ^ c ^ d; k = 0xCA62C1D6; }
        uint32_t temp = rol(a,5) + f + e + k + w[i];
        e = d; d = c; c = rol(b,30); b = a; a = temp;
    }

    ctx->h[0] += a; ctx->h[1] += b; ctx->h[2] += c; ctx->h[3] += d; ctx->h[4] += e;
}

static void sha1Update(SHA1Context* ctx, const uint8_t* data, size_t len) {
    size_t i = 0;
    ctx->len += len * 8;
    while (i < len) {
        size_t to_copy = 64 - ctx->block_len;
        if (to_copy > len - i) to_copy = len - i;
        memcpy(ctx->block + ctx->block_len, data + i, to_copy);
        ctx->block_len += to_copy;
        i += to_copy;
        if (ctx->block_len == 64) {
            sha1ProcessBlock(ctx, ctx->block);
            ctx->block_len = 0;
        }
    }
}

static void sha1Final(SHA1Context* ctx, uint8_t hash[20]) {
    ctx->block[ctx->block_len++] = 0x80;
    if (ctx->block_len > 56) {
        while (ctx->block_len < 64) ctx->block[ctx->block_len++] = 0;
        sha1ProcessBlock(ctx, ctx->block);
        ctx->block_len = 0;
    }
    while (ctx->block_len < 56) ctx->block[ctx->block_len++] = 0;
    for (int i = 0; i < 8; i++) ctx->block[56 + i] = (ctx->len >> (56 - 8*i)) & 0xFF;
    sha1ProcessBlock(ctx, ctx->block);
    for (int i = 0; i < 5; i++) {
        hash[i*4+0] = (ctx->h[i] >> 24) & 0xFF;
        hash[i*4+1] = (ctx->h[i] >> 16) & 0xFF;
        hash[i*4+2] = (ctx->h[i] >> 8) & 0xFF;
        hash[i*4+3] = (ctx->h[i]) & 0xFF;
    }
}

static std::string sha1Hex(const uint8_t* data, size_t size) {
    uint8_t hash[20];
    SHA1Context ctx;
    sha1Init(&ctx);
    sha1Update(&ctx, data, size);
    sha1Final(&ctx, hash);
    static const char hexDigits[] = "0123456789abcdef";
    std::string out;
    out.reserve(40);
    for (int i = 0; i < 20; i++) {
        out.push_back(hexDigits[(hash[i] >> 4) & 0xF]);
        out.push_back(hexDigits[hash[i] & 0xF]);
    }
    return out;
}

// ------------------------
// Known ROM SHA1 -> BIN mapping
// ------------------------
static const std::unordered_map<std::string,std::string> g_romToBin = {
    {"1fb13cad402518d3ae9a8dc4b52c5c54b2a4adc7","us_v10.bin"}, // US v1.0
    {"<PAL_SHA1_HERE>","pal.bin"}                                 // PAL version placeholder
};

// ------------------------
// Load precomputed BIN
// ------------------------
extern "C"
bool loadOTRFromBin(const char* binPath) {
    BK_OTR.clear();
    g_progress = 0.0f;
    if (!binPath) return false;

    FILE* f = fopen(binPath,"rb");
    if (!f) {
        LOGI("Failed to open BIN: %s", binPath);
        return false;
    }

    // Read entry count
    uint32_t entryCount = 0;
    if (fread(&entryCount, 4, 1, f) != 1) { fclose(f); LOGI("Failed to read entry count"); return false; }
    if (entryCount == 0) { fclose(f); LOGI("BIN has no entries"); return false; }

    struct EntryHeader { uint32_t offset; uint32_t size; };
    std::vector<EntryHeader> entries(entryCount);

    if (fread(entries.data(), sizeof(EntryHeader), entryCount, f) != entryCount) {
        fclose(f); LOGI("Failed to read entry headers"); return false;
    }

    for (uint32_t i=0;i<entryCount;i++) {
        const auto& e = entries[i];
        if (e.size==0) continue;
        if (fseek(f,e.offset,SEEK_SET)!=0) { fclose(f); LOGI("Failed seek offset 0x%X", e.offset); return false; }
        size_t curSize = BK_OTR.size();
        BK_OTR.resize(curSize + e.size);
        if (fread(BK_OTR.data()+curSize,1,e.size,f)!=e.size) { fclose(f); LOGI("Failed read segment %u", i); return false; }
        g_progress = float(i+1)/entryCount;
        LOGI("Segment %u: offset 0x%X size %u", i,e.offset,e.size);
    }

    fclose(f);
    size_t pad = (16 - (BK_OTR.size()%16))%16;
    BK_OTR.insert(BK_OTR.end(),pad,0);
    g_progress = 1.0f;
    LOGI("Loaded BIN OTR: %zu bytes (+%zu padding)", BK_OTR.size(), pad);
    return true;
}

// ------------------------
// Auto detect and load BIN based on ROM SHA1
// ------------------------
extern "C"
bool autoLoadOTR(const uint8_t* romData, size_t romSize, const char* assetDir) {
    if (!romData || romSize==0 || !assetDir) return false;
    std::string hash = sha1Hex(romData,romSize);
    auto it = g_romToBin.find(hash);
    if (it==g_romToBin.end()) {
        LOGI("Unknown ROM SHA1: %s", hash.c_str());
        return false;
    }
    std::string binPath = std::string(assetDir) + "/" + it->second;
    LOGI("Detected ROM SHA1 %s -> BIN %s", hash.c_str(), binPath.c_str());
    return loadOTRFromBin(binPath.c_str());
}

// ------------------------
// Accessors
// ------------------------
extern "C" uint8_t* getOTRData(size_t* outSize) {
    if (outSize) *outSize = BK_OTR.size();
    return BK_OTR.empty()?nullptr:BK_OTR.data();
}

extern "C" float getOTRProgress() { return g_progress.load(); }

extern "C"
bool saveOTRToFile(const char* path) {
    if (!path || BK_OTR.empty()) return false;
    FILE* f = fopen(path,"wb");
    if (!f) return false;
    fwrite(BK_OTR.data(),1,BK_OTR.size(),f);
    fclose(f);
    LOGI("Saved BK.OTR to %s (%zu bytes)", path,BK_OTR.size());
    return true;
}