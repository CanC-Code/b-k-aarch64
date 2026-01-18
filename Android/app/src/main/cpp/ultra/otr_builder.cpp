// File: otr_builder.cpp
// Purpose: Deterministic ROM → OTR loader (Android NDK safe, with progress)

#include <cstdint>
#include <cstddef>
#include <vector>
#include <string>
#include <unordered_map>
#include <functional>
#include <fstream>
#include <cstring>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------------------------------------------------------------
// Minimal SHA1 implementation (public-domain style)
// ---------------------------------------------------------------------
struct SHA1Ctx {
    uint32_t state[5];
    uint64_t count;
    uint8_t buffer[64];
};

static inline uint32_t rol(uint32_t v, uint32_t bits) {
    return (v << bits) | (v >> (32 - bits));
}

static void sha1_transform(uint32_t state[5], const uint8_t buffer[64]) {
    uint32_t w[80];
    for (int i = 0; i < 16; ++i) {
        w[i] = (buffer[i*4] << 24) | (buffer[i*4+1] << 16) |
               (buffer[i*4+2] << 8) | (buffer[i*4+3]);
    }
    for (int i = 16; i < 80; ++i) {
        w[i] = rol(w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16], 1);
    }

    uint32_t a = state[0], b = state[1], c = state[2], d = state[3], e = state[4];

    for (int i = 0; i < 80; ++i) {
        uint32_t f, k;
        if (i < 20) { f = (b & c) | (~b & d); k = 0x5A827999; }
        else if (i < 40) { f = b ^ c ^ d; k = 0x6ED9EBA1; }
        else if (i < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC; }
        else { f = b ^ c ^ d; k = 0xCA62C1D6; }
        uint32_t temp = rol(a,5) + f + e + k + w[i];
        e = d; d = c; c = rol(b,30); b = a; a = temp;
    }

    state[0]+=a; state[1]+=b; state[2]+=c; state[3]+=d; state[4]+=e;
}

static void sha1_init(SHA1Ctx& ctx) {
    ctx.state[0]=0x67452301; ctx.state[1]=0xEFCDAB89;
    ctx.state[2]=0x98BADCFE; ctx.state[3]=0x10325476;
    ctx.state[4]=0xC3D2E1F0; ctx.count=0;
}

static void sha1_update(SHA1Ctx& ctx, const uint8_t* data, size_t len) {
    size_t i=0; size_t idx=ctx.count&63;
    ctx.count+=len;

    if(idx) {
        size_t fill=64-idx;
        if(len>=fill){
            memcpy(ctx.buffer+idx,data,fill);
            sha1_transform(ctx.state,ctx.buffer);
            i+=fill; idx=0;
        } else { memcpy(ctx.buffer+idx,data,len); return; }
    }

    for(; i+63<len; i+=64) sha1_transform(ctx.state,data+i);
    if(i<len) memcpy(ctx.buffer,data+i,len-i);
}

static std::string sha1_hex(const uint8_t* data, size_t len){
    SHA1Ctx ctx; sha1_init(ctx); sha1_update(ctx,data,len);

    uint64_t bits=ctx.count*8;
    ctx.buffer[ctx.count&63]=0x80;

    if((ctx.count&63)>55){
        memset(ctx.buffer+(ctx.count&63)+1,0,63-(ctx.count&63));
        sha1_transform(ctx.state,ctx.buffer);
        memset(ctx.buffer,0,56);
    } else memset(ctx.buffer+(ctx.count&63)+1,0,55-(ctx.count&63));

    for(int i=0;i<8;i++) ctx.buffer[56+i]=(bits>>(56-8*i))&0xFF;

    sha1_transform(ctx.state,ctx.buffer);

    static const char hex[]="0123456789abcdef";
    std::string out; out.reserve(40);
    for(int i=0;i<5;i++)
        for(int j=28;j>=0;j-=4) out.push_back(hex[(ctx.state[i]>>j)&0xF]);
    return out;
}

// ---------------------------------------------------------------------
// ROM SHA1 → BIN mapping
// ---------------------------------------------------------------------
static const std::unordered_map<std::string,std::string> g_romToBin = {
    {"1fb13cad402518d3ae9a8dc4b52c5c54b2a4adc7","us_v10.bin"}
};

// ---------------------------------------------------------------------
// File loader
// ---------------------------------------------------------------------
static bool loadFile(const std::string& path,std::vector<uint8_t>& out){
    std::ifstream f(path,std::ios::binary);
    if(!f){ LOGE("Failed to open BIN: %s",path.c_str()); return false; }
    f.seekg(0,std::ios::end);
    size_t size=static_cast<size_t>(f.tellg());
    f.seekg(0,std::ios::beg);
    out.resize(size);
    f.read(reinterpret_cast<char*>(out.data()),size);
    return true;
}

// ---------------------------------------------------------------------
// Build OTR with progress callback
// ---------------------------------------------------------------------
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* yamlData,
    size_t yamlSize,
    std::vector<uint8_t>& outOTR,
    std::function<void(float)> progressCallback
){
    outOTR.clear();
    if(!romData || romSize==0) return false;

    std::string sha1=sha1_hex(romData,romSize);
    LOGI("ROM SHA1: %s",sha1.c_str());

    auto it=g_romToBin.find(sha1);
    if(it==g_romToBin.end()){ LOGE("Unsupported ROM"); return false; }

    std::string path="/android_asset/otr_bins/"+it->second;
    if(!loadFile(path,outOTR)) return false;

    // Simulate progress in 10 steps
    for(int i=0;i<=10;i++){
        if(progressCallback) progressCallback(i/10.0f);
    }

    return true;
}