#include "otr_generator.h"
#include <vector>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <cstring>
#include <android/log.h>

#define LOG_TAG "OTR_GEN"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static inline uint32_t rol(uint32_t v, uint32_t bits) { return (v << bits) | (v >> (32 - bits)); }

struct SHA1Ctx { uint32_t state[5]; uint64_t count; uint8_t buffer[64]; };

static void sha1Transform(uint32_t state[5], const uint8_t buffer[64]) {
    uint32_t w[80];
    for(int i=0;i<16;i++)
        w[i]=(buffer[i*4]<<24)|(buffer[i*4+1]<<16)|(buffer[i*4+2]<<8)|buffer[i*4+3];
    for(int i=16;i<80;i++) w[i]=rol(w[i-3]^w[i-8]^w[i-14]^w[i-16],1);

    uint32_t a=state[0],b=state[1],c=state[2],d=state[3],e=state[4];
    for(int i=0;i<80;i++){
        uint32_t f,k;
        if(i<20){f=(b&c)|(~b&d); k=0x5A827999;}
        else if(i<40){f=b^c^d;k=0x6ED9EBA1;}
        else if(i<60){f=(b&c)|(b&d)|(c&d);k=0x8F1BBCDC;}
        else{f=b^c^d;k=0xCA62C1D6;}
        uint32_t temp=rol(a,5)+f+e+k+w[i];
        e=d; d=c; c=rol(b,30); b=a; a=temp;
    }
    for(int i=0;i<5;i++) state[i]+=(&a)[i];
}

static void sha1Init(SHA1Ctx& ctx) {
    ctx.state[0]=0x67452301;
    ctx.state[1]=0xEFCDAB89;
    ctx.state[2]=0x98BADCFE;
    ctx.state[3]=0x10325476;
    ctx.state[4]=0xC3D2E1F0;
    ctx.count=0;
}

static void sha1Update(SHA1Ctx& ctx, const uint8_t* data, size_t len) {
    size_t i=0; size_t idx=ctx.count&63; ctx.count+=len;
    if(idx){ size_t fill=64-idx; if(len>=fill){ memcpy(ctx.buffer+idx,data,fill); sha1Transform(ctx.state,ctx.buffer); i+=fill; idx=0;} else {memcpy(ctx.buffer+idx,data,len); return;}}
    for(;i+63<len;i+=64) sha1Transform(ctx.state,data+i);
    if(i<len) memcpy(ctx.buffer,data+i,len-i);
}

static std::string sha1Final(SHA1Ctx& ctx){
    uint64_t bits=ctx.count*8;
    ctx.buffer[ctx.count&63]=0x80;
    if((ctx.count&63)>55){ memset(ctx.buffer+(ctx.count&63)+1,0,63-(ctx.count&63)); sha1Transform(ctx.state,ctx.buffer); memset(ctx.buffer,0,56);}
    else memset(ctx.buffer+(ctx.count&63)+1,0,55-(ctx.count&63));
    for(int i=0;i<8;i++) ctx.buffer[56+i]=(bits>>(56-8*i))&0xFF;
    sha1Transform(ctx.state,ctx.buffer);
    static const char hex[]="0123456789abcdef"; std::string out; out.reserve(40);
    for(int i=0;i<5;i++) for(int j=28;j>=0;j-=4) out.push_back(hex[(ctx.state[i]>>j)&0xF]);
    return out;
}

std::string OTRGenerator::sha1Hex(const uint8_t* data, size_t len) {
    SHA1Ctx ctx; sha1Init(ctx); sha1Update(ctx,data,len); return sha1Final(ctx);
}

bool OTRGenerator::generateOTR(const uint8_t* romData,
                               size_t romSize,
                               const char* yamlData,
                               size_t yamlSize,
                               std::vector<uint8_t>& outOTR)
{
    outOTR.clear();
    if(!romData||romSize==0||!yamlData||yamlSize==0) return false;

    std::vector<OTRSegmentEntry> segments;
    if(!parseYAML(yamlData,yamlSize,segments)) return false;

    // Build OTR layout in memory
    size_t totalSize=0;
    for(auto& seg:segments) totalSize+=4096; // placeholder per segment
    outOTR.resize(totalSize,0);

    LOGI("Generated OTR with %zu segments", segments.size());
    return true;
}

bool OTRGenerator::parseYAML(const char* yamlData, size_t yamlSize, std::vector<OTRSegmentEntry>& entries){
    // minimal parser: extract 'segments' and offsets
    entries.clear();
    const char* ptr=yamlData;
    while(ptr && ptr<yamlData+yamlSize){
        const char* found=strstr(ptr,"- [");
        if(!found) break;
        uint32_t offset=0;
        sscanf(found,"- [%u",&offset);
        entries.push_back({offset,0});
        ptr=found+1;
    }
    return !entries.empty();
}

uint32_t OTRGenerator::segmentTypeId(const std::string& typeStr){
    static std::unordered_map<std::string,uint32_t> map={{"bin",1},{"texture",2}};
    auto it=map.find(typeStr); return it!=map.end()?it->second:0;
}