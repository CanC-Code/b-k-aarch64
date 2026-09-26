#include "gfx_interpreter.h"
#include <android/log.h>
#include <cstring>
#include <cstdlib>
#include <cmath>
#include <time.h>
#include <algorithm>

#define LOG_TAG "BKA_GFX"

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

/* High-volume per-command traces.  These were essential for bootstrapping the
 * decoder but each RSP task fires ~1000 of them, throttling the RSP thread to
 * ~1 Hz on device.  Flip to true to re-enable for a focused debugging session. */
static const bool BKA_GFX_VERBOSE = false;
#define LOGV(...) do { if (BKA_GFX_VERBOSE) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__); } while (0)

extern "C" {
    extern uint32_t g_active_fb_offset;
extern uint16_t gFramebuffers[2][FB_WIDTH * FB_HEIGHT];
    int getActiveFramebuffer(void);
    extern uint8_t* gN64_RDRAM;
    extern "C" void* bka_lookup_addr_by_low32(uint32_t low32);
void* bka_lookup_addr_mapping(uint32_t key);
void* bka_lookup_addr_by_low32(uint32_t low32);
    void* bka_lookup_addr_mapping_range_c(uint32_t key);
    int bka_is_mapped(void* ptr);
    int bka_is_readable(void* ptr);
    uintptr_t bka_get_mapped_end(void* ptr);
    void* bka_find_registered_in_range(uintptr_t lo, uintptr_t hi);
}

static uint8_t* g_bka_dl_cur = nullptr;   // walker sets before dispatch; Cmd_* helpers read for context

static RDPState s_rdp;
static int g_bka_task_tri_count = 0;
int g_bka_last_tri2_count = 0;   /* Fix DD: total TRI2 calls, monotonic */
static int g_mtx_flag_hist[256] = {0};
volatile uint32_t g_bka_frame_gen = 0;
static int g_bka_task_max_depth = 0;
static int g_bka_task_pops = 0;
static int s_rsp_dump_sizes = [](){ LOGV("RDP-SIZE=%zu sizeof dmem=%zu offsetof(dmem)=%zu offsetof(dmemVertexCount)=%zu", sizeof(RDPState), sizeof(s_rdp.dmem), offsetof(RDPState, dmem), offsetof(RDPState, dmemVertexCount)); return 0; }();
static uint64_t bka_canary_post = 0xBEEFCAFEBABE5678ull;
static inline bool bka_in_rdram(void* p, size_t n) {
    uintptr_t a = (uintptr_t)p;
    uintptr_t lo = (uintptr_t)gN64_RDRAM;
    uintptr_t hi = lo + 0x04000000;
    return a >= lo && (a + n) <= hi;
}
static inline void bka_guard_write(void* p, size_t n, const char* tag) {
    if (bka_in_rdram(p, n)) {
        static int _gw = 0;
        if (_gw++ < 20) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "RDRAM-WRITE %s dst=%p len=%zu", tag, p, n);
    }
}
static int s_mtx_log_frame = 0;
static int s_mtx_dump_frame = 0;
static const uint8_t* s_current_cmd = nullptr;

#include <signal.h>
#include <ucontext.h>
#include <sys/mman.h>
#include <unistd.h>
#include <dlfcn.h>
static void bka_sigsegv_handler(int sig, siginfo_t* si, void* uc) {
    ucontext_t* ctx = (ucontext_t*)uc;
    uintptr_t pc = (uintptr_t)ctx->uc_mcontext.pc;
    uintptr_t lr = (uintptr_t)ctx->uc_mcontext.regs[30];
    uintptr_t page = (uintptr_t)si->si_addr & ~0xFFFULL;

    Dl_info di_pc = {0}, di_lr = {0};
    dladdr((void*)pc, &di_pc);
    dladdr((void*)lr, &di_lr);

    const char* pc_name = di_pc.dli_sname ? di_pc.dli_sname : "?";
    const char* pc_lib  = di_pc.dli_fname ? di_pc.dli_fname : "?";
    uintptr_t pc_off = di_pc.dli_saddr ? (pc - (uintptr_t)di_pc.dli_saddr) : pc;
    uintptr_t pc_base = di_pc.dli_fbase ? ((uintptr_t)di_pc.dli_fbase) : 0;

    const char* lr_name = di_lr.dli_sname ? di_lr.dli_sname : "?";
    const char* lr_lib  = di_lr.dli_fname ? di_lr.dli_fname : "?";
    uintptr_t lr_off = di_lr.dli_saddr ? (lr - (uintptr_t)di_lr.dli_saddr) : lr;
    uintptr_t lr_base = di_lr.dli_fbase ? ((uintptr_t)di_lr.dli_fbase) : 0;

    static int s_seen = 0;
    if (s_seen++ < 20)
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "WRITEHIT addr=%p page=0x%lX pc=0x%lX pc_off=0x%lX pc_base=0x%lX pc_sym=%s+0x%lX lib=%s lr=0x%lX lr_off=0x%lX lr_sym=%s+0x%lX",
            si->si_addr, (unsigned long)page,
            (unsigned long)pc, (unsigned long)pc_off, (unsigned long)pc_base,
            pc_name, (unsigned long)pc_off, pc_lib,
            (unsigned long)lr, (unsigned long)lr_off,
            lr_name, (unsigned long)lr_off);
    mprotect((void*)page, 0x1000, PROT_READ | PROT_WRITE);
}
static void bka_install_watch(void) {
    struct sigaction sa = {0};
    sa.sa_sigaction = bka_sigsegv_handler;
    sa.sa_flags = SA_SIGINFO;
    sigaction(SIGSEGV, &sa, nullptr);
}

static uintptr_t s_dl_base = 0;

/* F3DEX opcodes that we recognize.  Used to distinguish LE-encoded runtime
 * commands from BE-encoded ROM-copied geometry commands. */
static inline bool bka_is_f3dex_opcode(uint8_t op) {
    /* Fix N: F3DEX2-only whitelist.  B-K uses F3DEX2; F3DEX 1.0 opcodes
     * 0x02, 0x05, 0x07, 0x08, 0xE0-0xE3 are drift tokens in this data.
     *
     * DMA: 0x00 SPNOOP, 0x01 MTX, 0x03 MOVEMEM, 0x04 VTX, 0x06 DL
     * Imm: 0xAF-0xBF (LOAD_UCODE..TRI1)
     * RDP: 0xE4-0xFF (TEXRECT..SETCIMG) */
    if (op == 0x00 || op == 0x01 || op == 0x03 ||
        op == 0x04 || op == 0x06) return true;
    if (op >= 0xAF && op <= 0xBF) return true;
    if (op >= 0xE4) return true;
    return false;
}


// Deterministic default segment bases (from decomp overlay layout)
// Populated before any RDP command runs, fixing many unmapped address errors.
static struct RDPStateDefaultSegments {
    RDPStateDefaultSegments() {
        s_rdp.segmentBase[0x00] = 0x00000000u;
        s_rdp.segmentBase[0x01] = 0x80000000u;
        s_rdp.segmentBase[0x02] = 0x80000000u;
        s_rdp.segmentBase[0x03] = 0x80000000u;
        s_rdp.segmentBase[0x0C] = 0x0C000000u;
        s_rdp.segmentBase[0x0D] = 0x80000000u;
        s_rdp.segmentBase[0x0E] = 0x80000000u;
        s_rdp.segmentBase[0x0F] = 0x80000000u;
    }
} s_rdpDefaultSegments;


// Heuristic: the two known bad DL addresses (0xFFF9153F, 0xFFFF153F)
// share low16 = 0x153F and differ by 0x60000.  Search readable heap
// regions for a base with that low16 whose two Vtx arrays look real.
static inline int bka_plausible_vtx(const uint8_t* b) {
    int16_t x = (int16_t)(b[0] | (b[1] << 8));
    int16_t y = (int16_t)(b[2] | (b[3] << 8));
    int16_t z = (int16_t)(b[4] | (b[5] << 8));
    if (x < -0x4000 || x > 0x4000) return 0;
    if (y < -0x4000 || y > 0x4000) return 0;
    if (z < -0x4000 || z > 0x4000) return 0;
    // Not all-zero, not all-same, not all-FF.
    int nonZero = 0, nonFF = 0;
    for (int i = 0; i < 16; i++) {
        if (b[i] != 0) nonZero = 1;
        if (b[i] != 0xFF) nonFF = 1;
    }
    if (!nonZero || !nonFF) return 0;
    return 1;
}

static uint8_t* bka_scan_heap_for_vertex_base(uint32_t dl_addr) {
    uint32_t off16 = dl_addr & 0xFFFF;
    uint32_t delta = (dl_addr == 0xFFFF153F) ? 0x60000u : 0u;

    FILE* f = fopen("/proc/self/maps", "r");
    if (!f) return nullptr;
    char line[512];
    uint8_t* found = nullptr;
    while (fgets(line, sizeof line, f)) {
        uintptr_t start, end;
        char perms[8];
        if (sscanf(line, "%lx-%lx %7s", &start, &end, perms) != 3) continue;
        if (perms[0] != 'r') continue;
        if (start < 0x7000000000ULL || start > 0x7700000000ULL) continue;
        if (end - start < (0x60000ULL + 0x40)) continue;

        // First 64K-aligned address in this region with low16 == off16.
        uintptr_t c = (start & ~(uintptr_t)0xFFFF) | (uintptr_t)off16;
        if (c < start) c += 0x10000;
        for (; c + 0x60000 + 0x40 <= end; c += 0x10000) {
            const uint8_t* p1 = (const uint8_t*)c;
            const uint8_t* p2 = p1 + delta;
            if (!bka_plausible_vtx(p1)) continue;
            if (delta && !bka_plausible_vtx(p2)) continue;

            static int s_h = 0;
            if (s_h++ < 2) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "HEAPVTX dl=0x%08X cand=%p delta=0x%X "
                    "b1=%02X%02X%02X%02X  b2=%02X%02X%02X%02X",
                    dl_addr, (void*)c, delta,
                    p1[0],p1[1],p1[2],p1[3], p2[0],p2[1],p2[2],p2[3]);
            }
            found = (uint8_t*)c;
            break;
        }
        if (found) break;
    }
    fclose(f);
    return found;
}

static inline uint8_t* RDP_TranslateAddr(uint32_t addr) {
    // Prefer the 64-bit host pointer in the recomp's 16-byte DL entry payload.

    if (addr == 0x7A7B0620) {
        static int s_trace = 0;
        if (s_trace++ < 5)
            LOGV("XLT TRACE enter addr=0x%08X", addr);
    }

    { static int s_xtrace2 = 0; uint32_t __s = (addr >> 24) & 0x0F;      if (__s >= 1 && __s <= 15 && s_xtrace2++ < 100) {        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",          "XT2 addr=0x%08X seg=%u base=0x%lX",          addr, __s, (unsigned long)s_rdp.segmentBase[__s]); } }
    if (addr == 0) return nullptr;

    // Known-bad DL address?  Try scanning the heap for the real buffer.
    if (addr == 0xFFF9153F || addr == 0xFFFF153F) {
        // Cache the resolved base for the process lifetime.
        static uint8_t* cached_ff = nullptr;
        static uint8_t* cached_ffff = nullptr;
        if (addr == 0xFFF9153F) {
            if (!cached_ff) cached_ff = bka_scan_heap_for_vertex_base(addr);
            if (cached_ff) return cached_ff;
        } else {
            if (!cached_ffff) cached_ffff = bka_scan_heap_for_vertex_base(addr);
            if (cached_ffff) return cached_ffff;
        }
    }

    if (addr == 0xFFF9153F || addr == 0xFFFF153F) {
        static int s_xtrace = 0;
        if (s_xtrace++ < 40) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "XLTPATH addr=0x%08X seg=%X segBase=%08lX gRDRAM=%p",
                addr, (addr >> 24) & 0x0F,
                (unsigned long)s_rdp.segmentBase[(addr >> 24) & 0x0F],
                (void*)gN64_RDRAM);
        }
    }

    if (addr >= 0x60000000u && addr < 0x80000000u) { uint64_t c = 0x7900000000ULL | (uint64_t)addr; if (bka_is_readable((void*)c)) return (uint8_t*)c; c = 0x7A00000000ULL | (uint64_t)addr; if (bka_is_readable((void*)c)) return (uint8_t*)c; }
    // Try exact-match mapping table first.
    void* p = bka_lookup_addr_mapping(addr);
    if (p) return (uint8_t*)p;

    // Fallback: reconstruct the 64-bit host pointer from a 32-bit truncation.
    // Every allocation in this build lands in the 0x72xxxxxxxx / 0x73xxxxxxxx
    // heap range. If the low32 matches an allocation, use it directly.
    // Reconstruct only when the low32 looks like a real heap pointer.
    // Flag/length fields (e.g. G_VTX's 0xFFFF153F) must not be treated
    // as truncated host addresses.
    // Skip addresses that live inside RDRAM (below 16 MB) and flag/\n    // length fields (above 0x7F000000). Only reconstruct in between.
    // Segment-relative translation.
    {
        uint32_t seg = (addr >> 24) & 0x0F;
        if (seg >= 1 && seg <= 15) {
            uintptr_t base = s_rdp.segmentBase[seg];
            if (base != 0 && base != (uintptr_t)-1) {
                uint32_t off = addr & 0x00FFFFFFu;
                // Case A: heap low-32 (0x60..0x7F): map lookup on base, add off.
                if (base < 0x80000000u) {
                    void* mapped = bka_lookup_addr_mapping((uint32_t)base);
                    if (mapped) {
                        uint8_t* cand = (uint8_t*)mapped + off;
                        if (bka_is_readable(cand)) return cand;
                    }
                }
                // Case B: physical RDRAM (0x00..0x03FFFFFF).
                if (base < 0x04000000u && gN64_RDRAM) {
                    uint32_t phys = (uint32_t)base + off;
                    if (phys < 0x04000000u) return gN64_RDRAM + phys;
                }
                // Case C: KSEG0 (0x80..0x83FFFFFF).
                if (base >= 0x80000000u && base < 0x84000000u && gN64_RDRAM) {
                    uint32_t phys = (uint32_t)(base - 0x80000000u) + off;
                    if (phys < 0x04000000u) return gN64_RDRAM + phys;
                }
            }
        }
    }
        if ((addr >= 0x20000000ULL && addr < 0x22F00000ULL) || (addr >= 0x70000000ULL && addr < 0x7F000000ULL)) {
        uint64_t cand72 = (addr >= 0x70000000ULL ? 0x7900000000ULL : 0x7200000000ULL) | (uint64_t)addr;
        if (bka_is_readable((void*)cand72)) {
            static int rec_log72 = 0;
            if (rec_log72++ < 6) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "XLT RECONSTRUCT 0x%08X -> %p (0x72 base)", addr, (void*)cand72);
            }
            return (uint8_t*)cand72;
        }
        uint64_t cand73 = (addr >= 0x70000000ULL ? 0x7A00000000ULL : 0x7300000000ULL) | (uint64_t)addr;
        if (bka_is_readable((void*)cand73)) {
            static int rec_log73 = 0;
            if (rec_log73++ < 6) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "XLT RECONSTRUCT 0x%08X -> %p (0x73 base)", addr, (void*)cand73);
            }
            return (uint8_t*)cand73;
        }
    }

    // By-low32 lookup: only meaningful for values that could plausibly be
    // truncated heap pointers (>=16 MB, <2 GB).  Small values like 0x800 are
    // never truncated heap addresses; matching them just picks up random
    // allocations whose offset happens to end in those low bits.
    if (addr >= 0x10000000u && addr < 0x80000000u) {
        void* byLow = bka_lookup_addr_by_low32(addr);
        if (byLow) {
            static int b1 = 0;
            if (b1++ < 8) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "XLT LOW32MATCH addr=0x%08X -> %p", addr, byLow);
            return (uint8_t*)byLow;
        }
    }
    // Prefix reconstruction with a "looks like vertex data" heuristic.
    // Accept a candidate iff:
    //   - first 16 bytes are not all-zero and not all-identical, AND
    //   - the first three s16 fields (x,y,z) are in a plausible range.
    if ((addr & 0xFF000000u) == 0xFF000000u || (addr & 0xC0000000u) == 0xC0000000u) {
        for (uint64_t pfx = 0x7000000000ULL; pfx <= 0x7F00000000ULL; pfx += 0x0100000000ULL) {
            uint64_t cand = pfx | (uint64_t)addr;
            if (!bka_is_readable((void*)cand)) continue;
            uint8_t* b = (uint8_t*)cand;

            int allZero = 1, allSame = 1;
            uint8_t v0 = b[0];
            for (int k = 0; k < 16; k++) {
                if (b[k] != 0) allZero = 0;
                if (b[k] != v0) allSame = 0;
            }
            if (allZero || allSame) continue;

            int16_t x = (int16_t)(b[0] | (b[1] << 8));
            int16_t y = (int16_t)(b[2] | (b[3] << 8));
            int16_t z = (int16_t)(b[4] | (b[5] << 8));
            if (x < -2048 || x > 2048) continue;
            if (y < -2048 || y > 2048) continue;
            if (z < -2048 || z > 2048) continue;

            static int b2 = 0;
            if (b2++ < 12) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "VTXRECON addr=0x%08X pfx=0x%llX -> %p x=%d y=%d z=%d",
                addr, (unsigned long long)(pfx >> 32), (void*)cand, x, y, z);
            return (uint8_t*)cand;
        }
        static int b3 = 0;
        if (b3++ < 3) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "VTXRECON FAILED addr=0x%08X (no plausible prefix)", addr);
    }

    if (addr == 0x7A7B0620) {
        LOGV("XLT TRACE about to miss addr=0x%08X", addr);
    }

    // Diagnostic: log misses so we can see what the game asked for
    static int miss_log = 0;
    if (miss_log++ < 12) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "XLT miss addr=0x%08X map_size=?", addr);
    }

    if (addr == 0x7A7B0620) {
        LOGV("XLT TRACE reached segment block addr=0x%08X", addr);
    }

    // Segment address (F3DEX_GBI)
    uint32_t seg = (addr >> 24) & 0x0F;
    uint32_t off = addr & 0x00FFFFFF;
    { static int s_sc = 0; if (s_sc++ < 6) LOGV("SEGCHK addr=0x%08X seg=%u segB1=0x%lX dlbase=0x%lX cur=%p", addr, seg, (unsigned long)s_rdp.segmentBase[1], (unsigned long)s_dl_base, (void*)s_current_cmd); }
    if (seg == 1 && s_rdp.segmentBase[1] == 0x80000000u && s_current_cmd) { uintptr_t c = (uintptr_t)s_current_cmd; uintptr_t cands[6] = { c - 0x1D0, c - 0x1C0, c - 0x1A0, c - 0xC80, c - 0x400, c - 0x200 }; for (int k = 0; k < 6; k++) { uintptr_t v = cands[k]; if (!bka_is_readable((void*)v)) continue; uint8_t* b = (uint8_t*)v; int hits = 0; for (int i = 0; i < 8; i++) { uint8_t* q = b + i*16; if (!bka_is_readable((void*)(q+16))) break; int16_t z = (int16_t)((q[4] << 8) | q[5]); int cn = (q[12] == 0x80 && q[13] == 0x7F) || (q[12] == 0x7F && q[13] == 0x80); if (z == 0 && cn) hits++; } static int s_v = 0; if (s_v++ < 20) LOGV("SEG1VTX2 k=%d cand=0x%lX hits=%d/8 cur=0x%lX", k, (unsigned long)v, hits, (unsigned long)c); if (hits >= 3) return (uint8_t*)(v + off); } }
    if (seg != 0 && s_rdp.segmentBase[seg] != 0) {
        uint32_t base = s_rdp.segmentBase[seg];
        void *base_pm = bka_lookup_addr_mapping(base);
        if (base_pm) {
            if (addr == 0xFFF9153F || addr == 0xFFFF153F)
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "XLTPATH-USE segbase (base=%08X off=%X)", base, off);
            return (uint8_t*)base_pm + off;
        }
        uint32_t combined = base + off;
        void *pm = bka_lookup_addr_mapping(combined);
        if (pm) {
            if (addr == 0xFFF9153F || addr == 0xFFFF153F)
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "XLTPATH-USE combined (combined=%08X)", combined);
            return (uint8_t*)pm;
        }
        if (combined < 0x4000000u && gN64_RDRAM) {
            if (addr == 0xFFF9153F || addr == 0xFFFF153F)
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "XLTPATH-USE combined-rdram (combined=%08X)", combined);
            return gN64_RDRAM + combined;
        }
        if (combined >= 0x80000000u && combined < 0x84000000u && gN64_RDRAM) {
            uint32_t off2 = combined - 0x80000000u;
            if (off2 < 0x800000u) {   // must be within an 8 MB RDRAM
                return gN64_RDRAM + off2;
            }
        }
        if (combined >= 0xA0000000u && combined < 0xA4000000u && gN64_RDRAM) {
            uint32_t off2 = combined - 0xA0000000u;
            if (off2 < 0x04000000u) {
                if (addr == 0xFFF9153F || addr == 0xFFFF153F)
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "XLTPATH-USE kseg1 (combined=%08X off=%X)", combined, off2);
                return gN64_RDRAM + off2;
            }
        }
        // fall through if none matched
    }

    // Direct physical RDRAM fallback
    if ((addr < 0x4000000u || (addr >= 0x80000000u && addr < 0x84000000u) || (addr >= 0xA0000000u && addr < 0xA4000000u)) && gN64_RDRAM) {
        uint32_t off = addr & 0x00FFFFFFu;
        if (off < 0x04000000u) return gN64_RDRAM + off;
    }

    // Only allow the "low addr is RDRAM offset" fallback for small addresses.
    // Anything >= 0x10000000 that got here is a bogus lookup key; return null
    // so the caller logs a real failure instead of reading random RDRAM.
    if (gN64_RDRAM && addr < 0x10000000u) {
        uint32_t off2 = addr & 0x00FFFFFF;
        return gN64_RDRAM + off2;
    }

    static int miss2 = 0;
    if (miss2++ < 20) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "XLT GIVEUP addr=0x%08X (not in map, not segment, not RDRAM)", addr);
    }
    return nullptr;
}

static int s_frameCount = 0;

// =======================================================================
// Helpers
// =======================================================================

static inline uint32_t RDP_BPP(uint32_t size) {
    static const uint32_t bpp[] = {0, 1, 2, 2};
    return bpp[size & 3];
}

static inline uint16_t RGBA8_TO_RGB565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
}

static inline int16_t read_int16(const uint8_t* ptr) {
    return (int16_t)((ptr[0] << 8) | ptr[1]);
}

// =======================================================================
// RDP State Management
// =======================================================================

static void RDP_InitState() {
    // Seed matrices to identity so the first MUL/PUSH ops are well-defined.
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            s_rdp.projection[i][j] = s_rdp.modelview[i][j] =
                s_rdp.viewProj[i][j] = (i == j) ? 1.0f : 0.0f;
    s_rdp.modelviewStackDepth = 0;

    // Preserve vertex buffer and count across display list tasks.
    static BKVertex saved_dmem[DMEM_VERTEX_COUNT];
    static int saved_dmemVertexCount = 0;
    memcpy(saved_dmem, s_rdp.dmem, sizeof(saved_dmem));
    saved_dmemVertexCount = s_rdp.dmemVertexCount;
    // Preserve texture state across task boundary (2026-09-23).
    static uint8_t  saved_tmem[4096];
    static uint8_t  saved_tiles[sizeof(s_rdp.tiles)];
    static uint8_t* saved_texAddr = nullptr;
    static uint32_t saved_texWidth = 0, saved_texFmt = 0, saved_texSize = 0;
    static int      saved_activeTile = 0, saved_textureEnabled = 0;
    memcpy(saved_tmem, s_rdp.tmem, sizeof(saved_tmem));
    memcpy(saved_tiles, &s_rdp.tiles, sizeof(saved_tiles));
    saved_texAddr = s_rdp.texAddr;
    saved_texWidth = s_rdp.texWidth;
    saved_texFmt = s_rdp.texFmt;
    saved_texSize = s_rdp.texSize;
    saved_activeTile = s_rdp.activeTile;
    saved_textureEnabled = s_rdp.textureEnabled;

    // Clear all state except vertices.
    memset(&s_rdp, 0, sizeof(s_rdp));
    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX", "INIT-MEMSET-RAN");

    // Re-seed segment bases — the memset above wipes them.
    // These match the defaults set by the RDPStateDefaultSegments constructor.
    s_rdp.segmentBase[0x00] = 0x00000000u;
    s_rdp.segmentBase[0x01] = 0x80000000u;
    s_rdp.segmentBase[0x02] = 0x80000000u;
    s_rdp.segmentBase[0x03] = 0x80000000u;
    s_rdp.segmentBase[0x0C] = 0x0C000000u;
    s_rdp.segmentBase[0x0D] = 0x80000000u;
    s_rdp.segmentBase[0x0E] = 0x80000000u;
    s_rdp.segmentBase[0x0F] = 0x80000000u;

    // Restore vertices and count.
    memcpy(s_rdp.dmem, saved_dmem, sizeof(saved_dmem));
    s_rdp.dmemVertexCount = saved_dmemVertexCount;
    // Restore texture state (2026-09-23).
    memcpy(s_rdp.tmem, saved_tmem, sizeof(saved_tmem));
    memcpy(&s_rdp.tiles, saved_tiles, sizeof(saved_tiles));
    s_rdp.texAddr = saved_texAddr;
    s_rdp.texWidth = saved_texWidth;
    s_rdp.texFmt = saved_texFmt;
    s_rdp.texSize = saved_texSize;
    s_rdp.activeTile = saved_activeTile;
    s_rdp.textureEnabled = saved_textureEnabled;

    s_rdp.primR = s_rdp.primG = s_rdp.primB = s_rdp.primA = 255;
    s_rdp.envR = s_rdp.envG = s_rdp.envB = s_rdp.envA = 255;
    s_rdp.blendR = s_rdp.blendG = s_rdp.blendB = 255; s_rdp.blendA = 255;
    s_rdp.fillR = s_rdp.fillG = s_rdp.fillB = 255; s_rdp.fillA = 255;
    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX", "INIT-FILL-SET (%d,%d,%d)", s_rdp.fillR, s_rdp.fillG, s_rdp.fillB);
    s_rdp.fogR = s_rdp.fogG = s_rdp.fogB = 255; s_rdp.fogA = 255;
    // s_rdp.activeTile preserved above — do NOT reset
    // s_rdp.textureEnabled preserved above — do NOT reset
    s_rdp.matrixMode = 0;

    // Initialize matrices to identity
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            s_rdp.projection[i][j] = s_rdp.modelview[i][j] = (i == j) ? 1.0f : 0.0f;
}

// =======================================================================
// Matrix Operations
// =======================================================================

static void Matrix_Identity(BKMatrix m) {
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            m[i][j] = (i == j) ? 1.0f : 0.0f;
}

static void Matrix_MultVec(const BKMatrix m, float x, float y, float z, float w,
                           float* ox, float* oy, float* oz, float* ow) {
    // N64 SDK convention: v' = v * M  where M is column-major
    //     out[col] = sum over rows of  m[row][col] * v[row]
    // (equivalently, transpose of the row-vector convention)
    *ox = m[0][0]*x + m[1][0]*y + m[2][0]*z + m[3][0]*w;
    *oy = m[0][1]*x + m[1][1]*y + m[2][1]*z + m[3][1]*w;
    *oz = m[0][2]*x + m[1][2]*y + m[2][2]*z + m[3][2]*w;
    *ow = m[0][3]*x + m[1][3]*y + m[2][3]*z + m[3][3]*w;
}

// Load N64 fixed-point matrix (int16_t[4][4] with 32-bit integer parts)
static void Matrix_LoadFromN64(BKMatrix* out, const void* src) {
    {
        static int s_raw = 0;
        if (s_raw++ < 2) {
            const uint8_t* b = (const uint8_t*)src;
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRAW 00-15: %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X",
                b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],
                b[8],b[9],b[10],b[11],b[12],b[13],b[14],b[15]);
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRAW 16-31: %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X",
                b[16],b[17],b[18],b[19],b[20],b[21],b[22],b[23],
                b[24],b[25],b[26],b[27],b[28],b[29],b[30],b[31]);
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRAW 32-47: %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X",
                b[32],b[33],b[34],b[35],b[36],b[37],b[38],b[39],
                b[40],b[41],b[42],b[43],b[44],b[45],b[46],b[47]);
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRAW 48-63: %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X %02X%02X",
                b[48],b[49],b[50],b[51],b[52],b[53],b[54],b[55],
                b[56],b[57],b[58],b[59],b[60],b[61],b[62],b[63]);
        }
    }
    // N64 Mtx layout (64 bytes):
    //   bytes  0-31: integer parts, packed 2 per int32 word
    //   bytes 32-63: fraction parts, packed 2 per int32 word
    //
    // The recompiled ARM code writes these as NATIVE little-endian int32
    // values (they're just int32s in memory to the ARM CPU). We read each
    // 32-bit word in LE, then split into high and low 16-bit halves.
    // Integer half is signed; fraction half is unsigned (two's complement of
    // the whole fixed-point value carries the sign into the integer half).
    //
    //   word 0 -> m00 (high), m01 (low)
    //   word 1 -> m02 (high), m03 (low)
    //   word 2 -> m10 (high), m11 (low)
    //   etc.
    const uint8_t* p = (const uint8_t*)src;
    for (int r = 0; r < 4; r++) {
        for (int c = 0; c < 4; c++) {
            int idx       = r * 4 + c;
            int word_idx  = idx >> 1;
            int side      = idx & 1;   // 0 = high half, 1 = low half
            const uint8_t* iw = p + word_idx * 4;
            const uint8_t* fw = p + 32 + word_idx * 4;

            uint32_t iw32 = (uint32_t)iw[0]        | ((uint32_t)iw[1] << 8)
                          | ((uint32_t)iw[2] << 16) | ((uint32_t)iw[3] << 24);
            uint32_t fw32 = (uint32_t)fw[0]        | ((uint32_t)fw[1] << 8)
                          | ((uint32_t)fw[2] << 16) | ((uint32_t)fw[3] << 24);

            int16_t  e_int;
            uint16_t e_frac;
            if (side == 0) {
                e_int  = (int16_t)(iw32 >> 16);
                e_frac = (uint16_t)(fw32 >> 16);
            } else {
                e_int  = (int16_t)(iw32 & 0xFFFF);
                e_frac = (uint16_t)(fw32 & 0xFFFF);
            }
            (*out)[r][c] = (float)e_int + (float)e_frac / 65536.0f;
        }
    }
    {
        static int s_res = 0;
        if (s_res++ < 2) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRES r0=(%.4f %.4f %.4f %.4f)", (*out)[0][0],(*out)[0][1],(*out)[0][2],(*out)[0][3]);
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRES r1=(%.4f %.4f %.4f %.4f)", (*out)[1][0],(*out)[1][1],(*out)[1][2],(*out)[1][3]);
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRES r2=(%.4f %.4f %.4f %.4f)", (*out)[2][0],(*out)[2][1],(*out)[2][2],(*out)[2][3]);
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "MTXRES r3=(%.4f %.4f %.4f %.4f)", (*out)[3][0],(*out)[3][1],(*out)[3][2],(*out)[3][3]);
        }
    }
}

// =======================================================================
// Texture Fetch from TMEM
// =======================================================================

static void RDP_FetchTexel(int tile, uint32_t s, uint32_t t, uint8_t* outRGBA) {
    uint32_t u = s >> 5, v = t >> 5;
    auto& tdesc = s_rdp.tiles[tile];
    uint32_t bpp = RDP_BPP(tdesc.size);
    uint32_t texW = (tdesc.sh >> 2) + 1, texH = (tdesc.th >> 2) + 1;
    
    if (tdesc.clampS) { if (u >= texW) u = texW - 1; } else { u &= (texW - 1); }
    if (tdesc.clampT) { if (v >= texH) v = texH - 1; } else { v &= (texH - 1); }
    
    uint32_t tmemBase = tdesc.tmemAddr * 8, lineBytes = tdesc.line * 8;
    
    if (bpp == 2) {
        uint32_t offset = tmemBase + v * lineBytes + u * 2;
        if (offset + 1 < 4096) {
            uint16_t pixel = (s_rdp.tmem[offset] << 8) | s_rdp.tmem[offset + 1];
            if (tdesc.format == 0) {
                outRGBA[0] = ((pixel >> 11) & 0x1F) << 3;
                outRGBA[1] = ((pixel >> 6) & 0x1F) << 3;
                outRGBA[2] = ((pixel >> 1) & 0x1F) << 3;
                outRGBA[3] = (pixel & 1) ? 255 : 0;
            } else if (tdesc.format == 5) {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = (pixel >> 8) & 0xFF;
                outRGBA[3] = pixel & 0xFF;
            } else {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 255;
            }
        } else { outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 0; }
    } else if (bpp == 1) {
        uint32_t offset = tmemBase + v * lineBytes + u;
        if (offset < 4096) {
            uint8_t pixel = s_rdp.tmem[offset];
            if (tdesc.format == 4) {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = (pixel & 0xF0);
                outRGBA[3] = (pixel & 0x0F) << 4;
            } else {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = pixel;
            }
        } else { outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 0; }
    } else {
        outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 255;
    }
}

// =======================================================================
// Triangle Rasterizer (flat shaded, no Z-buffer yet)
// =======================================================================

static int s_triangleCount = 0;
static int s_invalidTriCount = 0;

static int s_synth_test_done = 0;
static void RasterizeTriangle(
    float x0, float y0, float x1, float y1, float x2, float y2,
    uint8_t r0, uint8_t g0, uint8_t b0, uint8_t a0,
    uint8_t r1, uint8_t g1, uint8_t b1, uint8_t a1,
    uint8_t r2, uint8_t g2, uint8_t b2, uint8_t a2,
    int16_t s0 = 0, int16_t t0 = 0, int16_t s1 = 0, int16_t t1 = 0, int16_t s2 = 0, int16_t t2 = 0)
{
    { static int s_rt = 0; if (s_rt++ < 30 || s_rt % 100 == 0)
        __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
            "RAST-ENTER #%d s1=%08lX s3=%08lX texEn=%d tile=%d xy=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f)",
            s_rt, (unsigned long)s_rdp.segmentBase[1], (unsigned long)s_rdp.segmentBase[3],
            (int)s_rdp.textureEnabled, (int)s_rdp.activeTile,
            x0, y0, x1, y1, x2, y2); }

    {
        static int s_raster_enter = 0;
        if (++s_raster_enter < 5 || s_raster_enter % 5000 == 1) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "RasterizeTriangle #%d ENTER: (%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f)",
                s_raster_enter, x0, y0, x1, y1, x2, y2);
        }
    }
    if (!std::isfinite(x0) || !std::isfinite(y0) ||
        !std::isfinite(x1) || !std::isfinite(y1) ||
        !std::isfinite(x2) || !std::isfinite(y2)) {
        return;
    }

    s_triangleCount++;
    if (s_triangleCount % 5000 == 1 || s_triangleCount < 5) {
        __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
            "RasterizeTriangle #%d: (%.1f,%.1f) (%.1f,%.1f) (%.1f,%.1f)",
            s_triangleCount, x0, y0, x1, y1, x2, y2);
    }
    // Sort vertices by Y (y0 <= y1 <= y2)
    if (y0 > y1) { std::swap(x0, x1); std::swap(y0, y1); std::swap(r0, r1); std::swap(g0, g1); std::swap(b0, b1); std::swap(a0, a1); std::swap(s0, s1); std::swap(t0, t1); }
    if (y1 > y2) { std::swap(x1, x2); std::swap(y1, y2); std::swap(r1, r2); std::swap(g1, g2); std::swap(b1, b2); std::swap(a1, a2); std::swap(s1, s2); std::swap(t1, t2); }
    if (y0 > y1) { std::swap(x0, x1); std::swap(y0, y1); std::swap(r0, r1); std::swap(g0, g1); std::swap(b0, b1); std::swap(a0, a1); std::swap(s0, s1); std::swap(t0, t1); }

    // Barycentric UV denominator (2026-09-23): constant for the triangle.
    float t_area = (x1-x0)*(y2-y0) - (x2-x0)*(y1-y0);
    float t_invArea = (t_area != 0.0f) ? (1.0f/t_area) : 0.0f;

    int iy0 = (int)ceilf(y0), iy1 = (int)ceilf(y1), iy2 = (int)ceilf(y2);
    if (iy0 < 0) iy0 = 0;
    if (iy1 < 0) iy1 = 0;                       // bottom-half loop starts here; negative causes OOB write
    if (iy2 > FB_HEIGHT) iy2 = FB_HEIGHT;
    if (iy1 > FB_HEIGHT) iy1 = FB_HEIGHT;
    if (iy0 >= iy2) return;

    int activeFb = getActiveFramebuffer();
    uint16_t* fb = (uint16_t*)(gN64_RDRAM + g_active_fb_offset);
    static int s_pix_total = 0;
    static int s_call = 0;
    s_call++;
    if (s_call <= 3 || s_call % 500 == 0) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
            "call #%d activeFb=%d fb=%p x0y0=%.1f,%.1f x1y1=%.1f,%.1f x2y2=%.1f,%.1f",
            s_call, activeFb, (void*)fb, x0, y0, x1, y1, x2, y2);
    }

    float dy10 = y1 - y0, dy21 = y2 - y1, dy20 = y2 - y0;
    { static int s_geom = 0; if (s_geom++ < 20) __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST", "TRI-GEOM iy0=%d iy1=%d iy2=%d dy10=%.2f dy21=%.2f dy20=%.2f", iy0, iy1, iy2, dy10, dy21, dy20); }
    float dx10 = x1 - x0, dx21 = x2 - x1, dx20 = x2 - x0;
    if (dy10 <= 0.0f && dy20 <= 0.0f) return;

    // Top half (y0 to y1)
    if (dy10 > 0.0f) {
        for (int y = iy0; y < iy1 && y < FB_HEIGHT; y++) {
            float fy = (float)y + 0.5f;
            float st0 = (fy - y0) / dy20;
            float st1 = (fy - y0) / dy10;
            
            float lx = x0 + st0 * dx20;
            float rx = x0 + st1 * dx10;
            if (lx > rx) std::swap(lx, rx);
            
            int ilx = (int)ceilf(lx), irx = (int)ceilf(rx);
            if (ilx < 0) ilx = 0; if (irx > FB_WIDTH) irx = FB_WIDTH;
            
            for (int x = ilx; x < irx; x++) {
                // Flat shading - use average color
                uint8_t r = (uint8_t)(((int)r0 + r1 + r2) / 3);
                uint8_t g = (uint8_t)(((int)g0 + g1 + g2) / 3);
                uint8_t b = (uint8_t)(((int)b0 + b1 + b2) / 3);
                if (s_rdp.textureEnabled) {
                    uint8_t tex[4] = {255,255,255,255};
                    float fx = (float)x + 0.5f;
                    float fy = (float)y + 0.5f;
                    float bw0 = ((x1-fx)*(y2-fy) - (x2-fx)*(y1-fy)) * t_invArea;
                    float bw1 = ((x2-fx)*(y0-fy) - (x0-fx)*(y2-fy)) * t_invArea;
                    float bw2 = 1.0f - bw0 - bw1;
                    int32_t uu = (int32_t)(bw0*(float)s0 + bw1*(float)s1 + bw2*(float)s2);
                    int32_t vv = (int32_t)(bw0*(float)t0 + bw1*(float)t1 + bw2*(float)t2);
                    uint32_t uuc = (uu < 0) ? 0u : (uint32_t)uu;
                    uint32_t vvc = (vv < 0) ? 0u : (uint32_t)vv;
                    { static int s_uv = 0; if (s_uv++ < 30)
                        __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
                            "UVTRACE #%d s=(%d,%d,%d) t=(%d,%d,%d) bw=(%.3f,%.3f,%.3f) uu=%d vv=%d",
                            s_uv, s0, s1, s2, t0, t1, t2, bw0, bw1, bw2, uu, vv); }
                    RDP_FetchTexel(s_rdp.activeTile, uuc, vvc, tex);
                    { static int s_txdbg = 0; if (s_txdbg++ < 3) {
                        auto& td = s_rdp.tiles[s_rdp.activeTile];
                        uint32_t tb = td.tmemAddr * 8;
                        __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
                            "TEXDBG fmt=%u size=%u line=%u tmemAddr=0x%X sh=%u th=%u "
                            "tmem[%u..%u]=%02X%02X%02X%02X%02X%02X%02X%02X "
                            "texAddr=%p texWidth=%u texFmt=%u texSize=%u",
                            td.format, td.size, td.line, td.tmemAddr, td.sh, td.th,
                            tb, tb+7,
                            s_rdp.tmem[tb+0],s_rdp.tmem[tb+1],s_rdp.tmem[tb+2],s_rdp.tmem[tb+3],
                            s_rdp.tmem[tb+4],s_rdp.tmem[tb+5],s_rdp.tmem[tb+6],s_rdp.tmem[tb+7],
                            (void*)s_rdp.texAddr, s_rdp.texWidth, s_rdp.texFmt, s_rdp.texSize); } }
                    { static int s_tx = 0; if (s_tx++ < 300)
                        __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
                            "TEXFETCH #%d tile=%d texel=%02X%02X%02X%02X vtxin=(%d,%d,%d)",
                            s_tx, s_rdp.activeTile, tex[0], tex[1], tex[2], tex[3], r, g, b); }
                    r = (uint8_t)(((int)r * tex[0]) / 255);
                    g = (uint8_t)(((int)g * tex[1]) / 255);
                    b = (uint8_t)(((int)b * tex[2]) / 255);
                }
            { static int s_px = 0; if (s_px++ < 500) __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST", "PIXWRITE #%d y=%d x=%d rgb=(%d,%d,%d) rgb565=0x%04X fb=%p rdr=%p ofs=0x%X idx=%d", s_px, (int)y, (int)x, r, g, b, RGBA8_TO_RGB565(r,g,b), (void*)&fb[y*FB_WIDTH+x], (void*)gN64_RDRAM, g_active_fb_offset, (int)(y*FB_WIDTH+x)); }
                bka_guard_write(&fb[y * FB_WIDTH + x], 2, "Raster.fb");
                *(volatile uint16_t *)&fb[y * FB_WIDTH + x] = RGBA8_TO_RGB565(r, g, b);
            }
        }
    }
    
    // Bottom half (y1 to y2)
    if (dy21 > 0.0f) {
        for (int y = iy1; y < iy2 && y < FB_HEIGHT; y++) {
            float fy = (float)y + 0.5f;
            float st0 = (fy - y0) / dy20;
            float st1 = (fy - y1) / dy21;
            
            float lx = x0 + st0 * dx20;
            float rx = x1 + st1 * dx21;
            if (lx > rx) std::swap(lx, rx);
            
            int ilx = (int)ceilf(lx), irx = (int)ceilf(rx);
            if (ilx < 0) ilx = 0; if (irx > FB_WIDTH) irx = FB_WIDTH;
            
            for (int x = ilx; x < irx; x++) {
                uint8_t r = (uint8_t)(((int)r0 + r1 + r2) / 3);
                uint8_t g = (uint8_t)(((int)g0 + g1 + g2) / 3);
                uint8_t b = (uint8_t)(((int)b0 + b1 + b2) / 3);
                if (s_rdp.textureEnabled) {
                    uint8_t tex[4] = {255,255,255,255};
                    float fx = (float)x + 0.5f;
                    float fy = (float)y + 0.5f;
                    float bw0 = ((x1-fx)*(y2-fy) - (x2-fx)*(y1-fy)) * t_invArea;
                    float bw1 = ((x2-fx)*(y0-fy) - (x0-fx)*(y2-fy)) * t_invArea;
                    float bw2 = 1.0f - bw0 - bw1;
                    int32_t uu = (int32_t)(bw0*(float)s0 + bw1*(float)s1 + bw2*(float)s2);
                    int32_t vv = (int32_t)(bw0*(float)t0 + bw1*(float)t1 + bw2*(float)t2);
                    uint32_t uuc = (uu < 0) ? 0u : (uint32_t)uu;
                    uint32_t vvc = (vv < 0) ? 0u : (uint32_t)vv;
                    RDP_FetchTexel(s_rdp.activeTile, uuc, vvc, tex);
                    { static int s_tx = 0; if (s_tx++ < 300)
                        __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
                            "TEXFETCH #%d tile=%d texel=%02X%02X%02X%02X vtxin=(%d,%d,%d)",
                            s_tx, s_rdp.activeTile, tex[0], tex[1], tex[2], tex[3], r, g, b); }
                    r = (uint8_t)(((int)r * tex[0]) / 255);
                    g = (uint8_t)(((int)g * tex[1]) / 255);
                    b = (uint8_t)(((int)b * tex[2]) / 255);
                }
                *(volatile uint16_t *)&fb[y * FB_WIDTH + x] = RGBA8_TO_RGB565(r, g, b);
            }
        }
    }
}

// =======================================================================
// Vertex Transform: apply combined matrix + viewport
// =======================================================================

// Returns the clip-space w for a vertex.  Used to reject triangles with
// any vertex at or behind the near plane, which would otherwise divide by
// w <= 0 and produce astronomically large screen coordinates.
struct BkaClipVtx { float x, y, z, w; };

// Full clip-space position (before the perspective divide).
static void ComputeClip(const BKVertex* v, float* cx, float* cy, float* cz, float* cw) {
    float x = (float)v->x, y = (float)v->y, z = (float)v->z;
    float ox, oy, oz, ow;
    Matrix_MultVec(s_rdp.modelview, x, y, z, 1.0f, &ox, &oy, &oz, &ow);
    Matrix_MultVec(s_rdp.projection, ox, oy, oz, ow, cx, cy, cz, cw);
}

// Sutherland-Hodgman clip of a single triangle against w > eps.
// Returns 0, 3, or 4 vertices (the visible polygon).
static int BkaClipNear(const BkaClipVtx in[3], float eps, BkaClipVtx out[4]) {
    int n = 0;
    BkaClipVtx prev = in[2];
    bool prevIn = prev.w > eps;
    for (int i = 0; i < 3; i++) {
        BkaClipVtx cur = in[i];
        bool curIn = cur.w > eps;
        if (curIn != prevIn) {
            float t = (eps - prev.w) / (cur.w - prev.w);
            out[n].x = prev.x + t * (cur.x - prev.x);
            out[n].y = prev.y + t * (cur.y - prev.y);
            out[n].z = prev.z + t * (cur.z - prev.z);
            out[n].w = eps;
            n++;
        }
        if (curIn) out[n++] = cur;
        prev = cur;
        prevIn = curIn;
    }
    return n;
}

static float ComputeClipW(const BKVertex* v) {
    float x = (float)v->x, y = (float)v->y, z = (float)v->z;
    float ox, oy, oz, ow;
    Matrix_MultVec(s_rdp.modelview, x, y, z, 1.0f, &ox, &oy, &oz, &ow);
    float px, py, pz, pw;
    Matrix_MultVec(s_rdp.projection, ox, oy, oz, ow, &px, &py, &pz, &pw);
    return pw;
}

static void TransformVertex(const BKVertex* v, float* sx, float* sy) {
    float x = (float)v->x, y = (float)v->y, z = (float)v->z;
    {
        static int s_tv = 0;
        if (s_tv++ < 0) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "TV-IN v=(%.1f,%.1f,%.1f) m00=%.4f m11=%.4f m22=%.4f m32=%.4f m23=%.4f",
                x, y, z,
                s_rdp.projection[0][0], s_rdp.projection[1][1],
                s_rdp.projection[2][2], s_rdp.projection[3][2],
                s_rdp.projection[2][3]);
        }
    }

    // Apply modelview
    float ox, oy, oz, ow;
    Matrix_MultVec(s_rdp.modelview, x, y, z, 1.0f, &ox, &oy, &oz, &ow);

    // Apply projection — use locals to avoid aliasing input/output
    float px, py, pz, pw;
    Matrix_MultVec(s_rdp.projection, ox, oy, oz, ow, &px, &py, &pz, &pw);
    ox = px; oy = py; oz = pz; ow = pw;

    {
        static int s_rd = 0;
        if (s_rd++ < 0) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "PRE-DIV post-proj ox=%.2f oy=%.2f oz=%.2f ow=%.4f",
                ox, oy, oz, ow);
        }
    }
    {
        static int s_dv = 0;
        if (s_dv++ < 20)
            __android_log_print(ANDROID_LOG_ERROR, "BKA-VERT",
                "V world=(%.0f,%.0f,%.0f) view=(%.1f,%.1f,%.1f) w=%.1f "
                "clip=(%.1f,%.1f,%.1f,%.1f)",
                (float)v->x, (float)v->y, (float)v->z,
                ox, oy, oz, ow,
                px, py, pz, pw);
    }
    // Perspective divide — MUST use clip.w (pw), not view.w (ow).
    // Forgetting this leaves coordinates in clip space (which for a
    // vertex 500 units away is ~500x too large), and every triangle
    // gets clamped to the clip box edge.
    {
        float inv = (fabsf(pw) > 0.0001f) ? (1.0f / pw) : 0.0f;
        ox = px * inv;
        oy = py * inv;
        oz = pz * inv;
    }

    // Viewport transform: NDC [-1,1] → screen [0,FB_WIDTH/HEIGHT]
    *sx = (ox + 1.0f) * 0.5f * (float)FB_WIDTH;
    *sy = (1.0f - oy) * 0.5f * (float)FB_HEIGHT;

    static int s_off = 0;
    if ((*sx < 0 || *sx > FB_WIDTH || *sy < 0 || *sy > FB_HEIGHT) && s_off++ < 5) {
        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
            "TransformVertex: off-screen (%.1f, %.1f) orig(%.1f,%.1f,%.1f) ndc(%.3f,%.3f)",
            *sx, *sy, x, y, z, ox, oy);
    }
}

// =======================================================================
// Command Handlers
// =======================================================================

static void Cmd_SetPrimColor(GfxCommand cmd) {
    s_rdp.primR = (cmd.w1 >> 24) & 0xFF;
    s_rdp.primG = (cmd.w1 >> 16) & 0xFF;
    s_rdp.primB = (cmd.w1 >> 8) & 0xFF;
    s_rdp.primA = cmd.w1 & 0xFF;
}

static void Cmd_SetEnvColor(GfxCommand cmd) {
    s_rdp.envR = (cmd.w1 >> 24) & 0xFF;
    s_rdp.envG = (cmd.w1 >> 16) & 0xFF;
    s_rdp.envB = (cmd.w1 >> 8) & 0xFF;
    s_rdp.envA = cmd.w1 & 0xFF;
}

static void Cmd_SetFillColor(GfxCommand cmd) {
    { static int s_fc = 0; if (s_fc++ < 20)
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "SETFILL-ENTRY #%d w0=0x%08X w1=0x%08X", s_fc, cmd.w0, cmd.w1); }
    uint32_t c = cmd.w0 & 0x00FFFFFF;  // F3DEX2: RRGGBB in low 24 bits of w0
    s_rdp.fillR = (c >> 16) & 0xFF;
    s_rdp.fillG = (c >>  8) & 0xFF;
    s_rdp.fillB =  c        & 0xFF;
    s_rdp.fillA = 255;
    { static int s_pf = 0; if (s_pf++ < 20)
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX", "SETFILL-POST #%d fillRGB=(%d,%d,%d)", s_pf, s_rdp.fillR, s_rdp.fillG, s_rdp.fillB); }
}

static void Cmd_SetOtherModeL(GfxCommand cmd) {
    uint32_t length = (cmd.w0 >> 8) & 0xFF, shift = cmd.w0 & 0xFF, data = cmd.w1;
    uint32_t mask = ((1 << (length + 1)) - 1) << shift;
    s_rdp.otherModeL = (s_rdp.otherModeL & ~mask) | ((data << shift) & mask);
}

static void Cmd_SetOtherModeH(GfxCommand cmd) {
    uint32_t length = (cmd.w0 >> 8) & 0xFF, shift = cmd.w0 & 0xFF, data = cmd.w1;
    uint32_t mask = ((1 << (length + 1)) - 1) << shift;
    s_rdp.otherModeH = (s_rdp.otherModeH & ~mask) | ((data << shift) & mask);
}

static void Cmd_SetCombine(GfxCommand cmd) {
    s_rdp.combineMode = (cmd.w0 & 0x00FFFFFF) | (cmd.w1 & 0xFF000000);
}

static void Cmd_Texture(GfxCommand cmd) {
    uint8_t op = (uint8_t)(cmd.w0 >> 24);
    uint32_t enable, tile;
    if (op == 0xBB) {
        // F3DEX (non-2): w0=[BB:8][bowtie:8][level:3][tile:3][on:8]
        enable =  cmd.w0        & 0xFF;
        tile   = (cmd.w0 >>  8) & 0x7;
    } else {
        // F3DEX2 (0xD7): on=w0[16], tile=w0[8]
        enable = (cmd.w0 >> 16) & 0xFF;
        tile   = (cmd.w0 >>  8) & 0xFF;
    }
    s_rdp.textureEnabled = (enable != 0);
    if (tile < 8) s_rdp.activeTile = tile;
    { static int s_ct = 0; if (s_ct++ < 40)
        __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
            "CMDTEX #%d op=%02X enable=%u tile=%u w0=%08X w1=%08X", s_ct, op, enable, tile, cmd.w0, cmd.w1); }
}

static void Cmd_SetTile(GfxCommand cmd) {
    uint32_t tile = (cmd.w1 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    t.format  = (cmd.w0 >> 21) & 0x7;
    t.size    = (cmd.w0 >> 19) & 0x3;
    t.line    = (cmd.w0 >> 9) & 0x1FF;
    t.tmemAddr = cmd.w0 & 0x1FF;
    t.palette = (cmd.w0 >> 20) & 0xF;
    t.clampT  = (cmd.w0 >> 18) & 0x1;
    t.mirrorT = (cmd.w0 >> 17) & 0x1;
    t.maskT   = (cmd.w0 >> 13) & 0xF;
    t.shiftT  = (cmd.w0 >> 9) & 0xF;
    t.clampS  = (cmd.w1 >> 31) & 0x1;
    t.mirrorS = (cmd.w1 >> 30) & 0x1;
    t.maskS   = (cmd.w1 >> 26) & 0xF;
    t.shiftS  = (cmd.w1 >> 22) & 0xF;
}

static void Cmd_SetTileSize(GfxCommand cmd) {
    uint32_t tile = (cmd.w1 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    t.sl = (cmd.w0 >> 12) & 0xFFF;
    t.tl = cmd.w0 & 0xFFF;
    t.sh = (cmd.w1 >> 12) & 0xFFF;
    t.th = cmd.w1 & 0xFFF;
}

static void Cmd_SetTImg(GfxCommand cmd) {
    // SETIMG address: some DLs emit pre-resolved physical addresses, some
    // emit segment-relative. Direct translate handles the first; if it
    // returns null, combine with the segment base and retry.
    uint8_t* resolved = RDP_TranslateAddr(cmd.w1);
    if (!resolved) {
        uint8_t  seg = (cmd.w1 >> 24) & 0x0F;
        uint32_t off = cmd.w1 & 0x00FFFFFF;
        uint32_t combined = (uint32_t)(s_rdp.segmentBase[seg] + off);
        resolved = RDP_TranslateAddr(combined);
        static int s_fb = 0; if (s_fb++ < 10)
            __android_log_print(ANDROID_LOG_ERROR, "BKA-SETIMG",
                "FALLBACK seg=%X off=%06X combined=%08X -> %p",
                seg, off, combined, (void*)resolved);
    }
    { uint8_t seg = (cmd.w1 >> 24) & 0x0F;
      uint32_t off = cmd.w1 & 0x00FFFFFF;
      uintptr_t segBase = s_rdp.segmentBase[seg];
      uint32_t combined = (uint32_t)(segBase + off);
      uint8_t* viaSeg = RDP_TranslateAddr(combined);
      static int s_sg = 0; if (s_sg++ < 20)
          __android_log_print(ANDROID_LOG_ERROR, "BKA-SETIMG",
              "SEGCHECK w1=%08X seg=%X off=%06X segBase=%08lX combined=%08X directRes=%p viaSegRes=%p",
              cmd.w1, seg, off, (unsigned long)segBase, combined, (void*)resolved, (void*)viaSeg); }
    // Drift guard (2026-09-23): real gDPSetTextureImage has fmt <= 5
    // and a resolvable image address. Reject anything else — the
    // walker is landing on non-command bytes and previously clobbered
    // s_rdp.texAddr with null, blocking LoadTile from ever running.
    { uint32_t _fmt = (cmd.w0 >> 21) & 0x7;
      if (_fmt > 5 || resolved == nullptr) {
          static int s_sr = 0; if (s_sr++ < 15)
              __android_log_print(ANDROID_LOG_ERROR, "BKA-SETIMG",
                  "SKIP drift w0=%08X w1=%08X fmt=%u resolved=%p",
                  cmd.w0, cmd.w1, _fmt, (void*)resolved);
          return;
      } }
    uint32_t fmt = (cmd.w0 >> 21) & 0x7;
    uint32_t siz = (cmd.w0 >> 19) & 0x3;
    uint32_t wd  = (cmd.w0 & 0xFFF) + 1;   // F3DEX: width-1 in bits [11:0]
    if (fmt > 5 && g_bka_dl_cur) {
        const uint8_t* p = g_bka_dl_cur;
        static int s_dft = 0; if (s_dft++ < 8)
            __android_log_print(ANDROID_LOG_ERROR, "BKA-SETIMG",
                "DRIFT ctx[-16..15]: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
                p[-16],p[-15],p[-14],p[-13],p[-12],p[-11],p[-10],p[-9],
                p[-8],p[-7],p[-6],p[-5],p[-4],p[-3],p[-2],p[-1],
                p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],
                p[8],p[9],p[10],p[11],p[12],p[13],p[14],p[15]);
    }
    { static int s_st = 0; if (s_st++ < 25)
        __android_log_print(ANDROID_LOG_ERROR, "BKA-SETIMG",
            "SETIMG #%d fmt=%u siz=%u wd=%u image=%08X resolved=%p",
            s_st, fmt, siz, wd, cmd.w1, (void*)resolved); }
    s_rdp.texFmt   = fmt;
    s_rdp.texSize  = siz;
    s_rdp.texWidth = wd;
    s_rdp.texAddr  = resolved;
}

static void Cmd_LoadTile(GfxCommand cmd) {
    uint32_t tile = (cmd.w0 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    uint32_t sl = (cmd.w0 >> 12) & 0xFFF, tl = cmd.w0 & 0xFFF;
    uint32_t sh = (cmd.w1 >> 12) & 0xFFF, th = cmd.w1 & 0xFFF;
    t.sl = sl; t.tl = tl; t.sh = sh; t.th = th;
    
    uint32_t bpp = RDP_BPP(t.size);
    if (bpp == 0) bpp = 1;
    uint32_t texWidth = (sh >> 2) + 1, texHeight = (th >> 2) + 1;
    uint32_t texSize = texWidth * texHeight * bpp;
    uint32_t lineWords = (texWidth * bpp + 7) / 8;
    
    { static int s_lt = 0; if (s_lt++ < 20)
        __android_log_print(ANDROID_LOG_ERROR, "BKA-LOAD",
            "LOADTILE #%d tile=%u sl=%u tl=%u sh=%u th=%u bpp=%u texAddr=%p texWidth=%u texSize=%u",
            s_lt, tile, sl, tl, sh, th, bpp, (void*)s_rdp.texAddr, s_rdp.texWidth, texSize); }
    if (s_rdp.texAddr && texSize <= 4096) {
        { static int s_lt2 = 0; if (s_lt2++ < 20) {
            uint32_t tmemBase = t.tmemAddr * 8;
            uint32_t srcLineStride = s_rdp.texWidth * bpp;
            uint32_t srcOff0 = tl * srcLineStride + sl * bpp;
            __android_log_print(ANDROID_LOG_ERROR, "BKA-LOAD",
                "LOADTILE-2 #%d tmemBase=%u lineWords=%u srcLineStride=%u srcOff0=%u src[0..7]=%02X%02X%02X%02X%02X%02X%02X%02X",
                s_lt2, tmemBase, lineWords, srcLineStride, srcOff0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+0] : 0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+1] : 0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+2] : 0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+3] : 0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+4] : 0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+5] : 0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+6] : 0,
                s_rdp.texAddr ? s_rdp.texAddr[srcOff0+7] : 0); } }
        uint32_t tmemBase = t.tmemAddr * 8;
        uint32_t srcLineStride = s_rdp.texWidth * bpp;
        for (uint32_t row = 0; row < texHeight; row++) {
            uint32_t srcOffset = (tl + row) * srcLineStride + sl * bpp;
            uint32_t dstOffset = tmemBase + row * lineWords * 8;
            if (dstOffset + lineWords * 8 <= 4096)
                memcpy(s_rdp.tmem + dstOffset, s_rdp.texAddr + srcOffset, lineWords * 8);
        }
        t.line = lineWords;
    }
}

static void Cmd_LoadTLUT(GfxCommand cmd) {
    uint32_t tile = (cmd.w0 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    uint32_t sl = (cmd.w0 >> 12) & 0xFFF;
    uint32_t tl = cmd.w0 & 0xFFF;
    uint32_t count = (cmd.w1 >> 14) & 0x3FF;
    if (s_rdp.texAddr) {
        uint32_t tmemBase = t.tmemAddr * 8;
        uint32_t srcOffset = tl * 2 + sl * 2;
        memcpy(s_rdp.tmem + tmemBase, s_rdp.texAddr + srcOffset, (count + 1) * 2);
    }
}

static void Cmd_LoadBlock(GfxCommand cmd) {
    /* Fix T: F3DEX LoadBlock.  Tile field is bits 16-23 of w0, NOT low 3.
     * Contiguous transfer; sh encodes 16-bit word count - 1. */
    uint32_t tile = (cmd.w0 >> 16) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    uint32_t sl = (cmd.w0 >> 12) & 0xFFF, tl = cmd.w0 & 0xFFF;
    uint32_t sh = (cmd.w1 >> 12) & 0xFFF, th = cmd.w1 & 0xFFF;
    t.sl = sl; t.tl = tl; t.sh = sh; t.th = th;

    uint32_t texSizeBytes = (sh + 1) * 2;
    uint32_t tmemBase = t.tmemAddr * 8;
    t.line = (texSizeBytes + 7) / 8;

    if (s_rdp.texAddr && texSizeBytes > 0 &&
        texSizeBytes <= 4096 && tmemBase + texSizeBytes <= 4096) {
        memcpy(s_rdp.tmem + tmemBase, s_rdp.texAddr, texSizeBytes);
        static int s_lbcopy = 0;
        if (s_lbcopy++ < 20) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA-LOADBLK",
                "COPY tile=%u tmemBase=%u bytes=%u src0..7=%02X%02X%02X%02X %02X%02X%02X%02X tmem0..7=%02X%02X%02X%02X %02X%02X%02X%02X",
                tile, tmemBase, texSizeBytes,
                s_rdp.texAddr[0],s_rdp.texAddr[1],s_rdp.texAddr[2],s_rdp.texAddr[3],
                s_rdp.texAddr[4],s_rdp.texAddr[5],s_rdp.texAddr[6],s_rdp.texAddr[7],
                s_rdp.tmem[tmemBase+0],s_rdp.tmem[tmemBase+1],s_rdp.tmem[tmemBase+2],s_rdp.tmem[tmemBase+3],
                s_rdp.tmem[tmemBase+4],s_rdp.tmem[tmemBase+5],s_rdp.tmem[tmemBase+6],s_rdp.tmem[tmemBase+7]);
        }
    } else {
        static int s_lbskip = 0;
        if (s_lbskip++ < 20) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA-LOADBLK",
                "SKIP tile=%u texAddr=%p bytes=%u tmemBase=%u",
                tile, (void*)s_rdp.texAddr, texSizeBytes, tmemBase);
        }
    }
}

// =======================================================================
// G_VTX - Load vertices into DMEM (F3DEX_GBI format)
// w0 = [G_VTX:8][v0:8][n:6][length:10]
// w1 = address of Vtx data in RDRAM
// =======================================================================
static int s_vtxCallCount = 0;
static void Cmd_Vtx(GfxCommand cmd) {
    s_vtxCallCount++;
    uint32_t v0 = ((cmd.w0 >> 16) & 0xFF) / 2;   // F3DEX stores v0*2
    uint32_t n  = ((cmd.w0 >> 10) & 0x3F) + 1;   // count - 1
    uint32_t addr = cmd.w1;

    static int s_vtx_dump = 0;
    if (s_vtx_dump++ < 3) {
        extern const uint8_t* s_current_cmd;
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "Cmd_Vtx CALL #%d: v0=%u n=%u addr=0x%08X w0=0x%08X cur=%p cur+8=%p delta=%ld",
            s_vtxCallCount, v0, n, addr, cmd.w0,
            (void*)s_current_cmd, (void*)((uintptr_t)s_current_cmd + 8),
            (long)((intptr_t)0));  // placeholder, filled below
    }

    if (v0 >= DMEM_VERTEX_COUNT || v0 + n > DMEM_VERTEX_COUNT) {
        LOGW("Cmd_Vtx: v0=%u n=%u exceeds DMEM limit (%d)",
             v0, n, DMEM_VERTEX_COUNT);
        return;
    }

    uint8_t* src = RDP_TranslateAddr(addr);
    if (!src) {
        static int s_ft = 0;
        if (s_ft++ < 200) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "VtxFAIL addr=0x%08X v0=%u n=%u w0=0x%08X", addr, v0, n, cmd.w0);
        }
        return;
    }
    uint8_t* src_base = src;

    static int s_vtx_resolve_log = 0;
    if (s_vtx_resolve_log++ < 0) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "VTXRESOLVE addr=0x%08X -> src=%p bytes: "
            "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
            addr, (void*)src,
            src[0],src[1],src[2],src[3],src[4],src[5],src[6],src[7],
            src[8],src[9],src[10],src[11],src[12],src[13],src[14],src[15]);
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "VTXSEGS [0]=%08lX [1]=%08lX [2]=%08lX [3]=%08lX "
            "[4]=%08lX [5]=%08lX [6]=%08lX [7]=%08lX "
            "[8]=%08lX [9]=%08lX [A]=%08lX [B]=%08lX "
            "[C]=%08lX [D]=%08lX [E]=%08lX [F]=%08lX",
            (unsigned long)s_rdp.segmentBase[0x0],
            (unsigned long)s_rdp.segmentBase[0x1],
            (unsigned long)s_rdp.segmentBase[0x2],
            (unsigned long)s_rdp.segmentBase[0x3],
            (unsigned long)s_rdp.segmentBase[0x4],
            (unsigned long)s_rdp.segmentBase[0x5],
            (unsigned long)s_rdp.segmentBase[0x6],
            (unsigned long)s_rdp.segmentBase[0x7],
            (unsigned long)s_rdp.segmentBase[0x8],
            (unsigned long)s_rdp.segmentBase[0x9],
            (unsigned long)s_rdp.segmentBase[0xA],
            (unsigned long)s_rdp.segmentBase[0xB],
            (unsigned long)s_rdp.segmentBase[0xC],
            (unsigned long)s_rdp.segmentBase[0xD],
            (unsigned long)s_rdp.segmentBase[0xE],
            (unsigned long)s_rdp.segmentBase[0xF]);
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "RDRAM=%p max_offset=%08lX (alloc 0x%lX)",
            (void*)gN64_RDRAM,
            (unsigned long)(addr & 0x00FFFFFF),
            (unsigned long)0x04000000);
    }

    for (uint32_t i = 0; i < n; i++) {
        BKVertex* v = &s_rdp.dmem[v0 + i];
        bka_guard_write(v, sizeof(BKVertex), "Cmd_Vtx.dmem");
        { static int s_vtxwr = 0; if (s_vtxwr++ < 0) LOGV("VTXWR i=%u v=%p src=%p dmem=%p idx=%u", i, (void*)v, (void*)src, (void*)s_rdp.dmem, v0+i); }
        v->x = read_int16(src + 0);
        v->y = read_int16(src + 2);
        v->z = read_int16(src + 4);
        v->flag = (src[6] << 8) | src[7];
        v->s = read_int16(src + 8);
        v->t = read_int16(src + 10);
        v->r = src[12];
        v->g = src[13];
        v->b = src[14];
        v->a = src[15];
        src += 16;
    }

    if (v0 + n > (uint32_t)s_rdp.dmemVertexCount)
        s_rdp.dmemVertexCount = v0 + n;
    {
        static int s_l = 0;
        if (s_l++ < 3) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "VtxOK addr=0x%08X v0=%u n=%u first8=%02X%02X%02X%02X %02X%02X%02X%02X",
                addr, v0, n,
                src_base[0],src_base[1],src_base[2],src_base[3],
                src_base[4],src_base[5],src_base[6],src_base[7]);
        }
    }

    static int s_vtx_hex = 0;
    if (s_vtx_hex++ < 3 && n >= 3 && src) {
        const uint8_t* raw = src_base;
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "VTXRAW %u bytes @%p: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
            n * 16, (const void*)raw,
            raw[0],raw[1],raw[2],raw[3],raw[4],raw[5],raw[6],raw[7],
            raw[8],raw[9],raw[10],raw[11],raw[12],raw[13],raw[14],raw[15]);
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "VTXDEC v0=(%d,%d,%d) v1=(%d,%d,%d) v2=(%d,%d,%d)",
            s_rdp.dmem[v0].x, s_rdp.dmem[v0].y, s_rdp.dmem[v0].z,
            s_rdp.dmem[v0+1].x, s_rdp.dmem[v0+1].y, s_rdp.dmem[v0+1].z,
            s_rdp.dmem[v0+2].x, s_rdp.dmem[v0+2].y, s_rdp.dmem[v0+2].z);
    }

    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
        "Cmd_Vtx: loaded %u vertices, dmemVertexCount=%d", n, s_rdp.dmemVertexCount);
}

// =======================================================================
// G_TRI1 - Draw 1 triangle
// w0 = [G_TRI1:8][v2:8][v1:8][v0:8]
// w1 = [flag:24][00000000]
// =======================================================================

static void Cmd_Tri1(GfxCommand cmd) {
    g_bka_task_tri_count++;
    static int s_tri1_calls = 0;
    if (++s_tri1_calls % 200 == 1 || s_tri1_calls < 5) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "Cmd_Tri1 CALLED #%d: w0=0x%08X w1=0x%08X dmem=%d",
            s_tri1_calls, cmd.w0, cmd.w1, s_rdp.dmemVertexCount);
    }
    // No vertices loaded yet; skip to avoid out-of-bounds and crash.
    if (s_rdp.dmemVertexCount == 0) return;

    uint32_t packed = cmd.w1;   // F3DEX_GBI: indices packed in w1, opcode only in w0
    uint32_t v0 = ((packed >> 16) & 0xFF) >> 1;
    uint32_t v1 = ((packed >> 8) & 0xFF) >> 1;
    uint32_t v2 = (packed & 0xFF) >> 1;

    if (v0 >= (uint32_t)s_rdp.dmemVertexCount ||
        v1 >= (uint32_t)s_rdp.dmemVertexCount ||
        v2 >= (uint32_t)s_rdp.dmemVertexCount) {
        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
            "Cmd_Tri1: INVALID vertex indices %u,%u,%u (dmemVertexCount=%d) w1=0x%08X",
            v0, v1, v2, s_rdp.dmemVertexCount, cmd.w1);
        return;
    }

    BKVertex* vert0 = &s_rdp.dmem[v0];
    BKVertex* vert1 = &s_rdp.dmem[v1];
    BKVertex* vert2 = &s_rdp.dmem[v2];

    if (ComputeClipW(vert0) <= 0.01f || ComputeClipW(vert1) <= 0.01f ||
        ComputeClipW(vert2) <= 0.01f) {
        return;  // vertex at or behind camera; skip
    }

    float sx0, sy0, sx1, sy1, sx2, sy2;
    TransformVertex(vert0, &sx0, &sy0);
    TransformVertex(vert1, &sx1, &sy1);
    TransformVertex(vert2, &sx2, &sy2);

    { static int s_rt = 0; if (s_rt++ < 20) LOGV("RASTER v=(%p %p %p) dmembase=%p", (void*)vert0, (void*)vert1, (void*)vert2, (void*)s_rdp.dmem); }
    { static int s_t1 = 0; if (s_t1++ < 20)
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "TRI1-DRAW color=(%d,%d,%d,%d) xy=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f)",
            vert0->r,vert0->g,vert0->b,vert0->a,
            sx0,sy0, sx1,sy1, sx2,sy2); }
    RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
        vert0->r, vert0->g, vert0->b, vert0->a,
        vert1->r, vert1->g, vert1->b, vert1->a,
        vert2->r, vert2->g, vert2->b, vert2->a,
        vert0->s, vert0->t, vert1->s, vert1->t, vert2->s, vert2->t);
}

// =======================================================================
// G_TRI2 - Draw 2 triangles (4 vertices)
// w0 = [G_TRI2:8][v2:8][v1:8][v0:8]  -- triangle 1 uses v0,v1,v2
// w1 = [flag2:8][v4:8][v3:8][flag1:8]  -- triangle 2 uses v1,v2,v3
// =======================================================================

static void Cmd_Tri2(GfxCommand cmd) {
    g_bka_task_tri_count++;
    { extern int g_bka_last_tri2_count; g_bka_last_tri2_count++; }
    static int s_tri2_calls = 0;
    if (++s_tri2_calls % 200 == 1 || s_tri2_calls < 5) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "Cmd_Tri2 CALLED #%d: w0=0x%08X w1=0x%08X dmem=%d",
            s_tri2_calls, cmd.w0, cmd.w1, s_rdp.dmemVertexCount);
    }
    if (s_rdp.dmemVertexCount == 0) return;

    uint32_t tri1 = cmd.w0 & 0xFFFFFF;  // first triangle packed in lower 24 bits
    uint32_t tri2 = cmd.w1;             // second triangle packed in w1

    uint32_t v00 = ((tri1 >> 16) & 0xFF) >> 1;
    uint32_t v01 = ((tri1 >> 8) & 0xFF) >> 1;
    uint32_t v02 = (tri1 & 0xFF) >> 1;
    uint32_t v10 = ((tri2 >> 16) & 0xFF) >> 1;
    uint32_t v11 = ((tri2 >> 8) & 0xFF) >> 1;
    uint32_t v12 = (tri2 & 0xFF) >> 1;

    if (v00 >= (uint32_t)s_rdp.dmemVertexCount ||
        v01 >= (uint32_t)s_rdp.dmemVertexCount ||
        v02 >= (uint32_t)s_rdp.dmemVertexCount ||
        v10 >= (uint32_t)s_rdp.dmemVertexCount ||
        v11 >= (uint32_t)s_rdp.dmemVertexCount ||
        v12 >= (uint32_t)s_rdp.dmemVertexCount) {
        static int s_tri2_inv_log = 0;
        if (s_tri2_inv_log++ < 50) {
            __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                "Cmd_Tri2: INVALID vertex indices %u,%u,%u,%u,%u,%u (dmemVertexCount=%d) w0=0x%08X w1=0x%08X",
                v00, v01, v02, v10, v11, v12, s_rdp.dmemVertexCount, cmd.w0, cmd.w1);
        }
        return;
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v00];
        BKVertex* vt1 = &s_rdp.dmem[v01];
        BKVertex* vt2 = &s_rdp.dmem[v02];
        {
            BkaClipVtx cv[3], cclip[4];
            ComputeClip(vt0, &cv[0].x, &cv[0].y, &cv[0].z, &cv[0].w);
            ComputeClip(vt1, &cv[1].x, &cv[1].y, &cv[1].z, &cv[1].w);
            ComputeClip(vt2, &cv[2].x, &cv[2].y, &cv[2].z, &cv[2].w);

            const float EPSW = 64.0f;   // near-plane w in clip space (N64 near-plane in view is typically 50-200)
            bool allIn = cv[0].w > EPSW && cv[1].w > EPSW && cv[2].w > EPSW;
            bool anyIn = cv[0].w > EPSW || cv[1].w > EPSW || cv[2].w > EPSW;

            if (!anyIn) return;   // fully behind camera

            if (!allIn) {
                // Near-plane clip. Real N64 hardware emits the visible
                // portion of a triangle that crosses w=0; skipping the
                // whole triangle was throwing away ~60% of the geometry.
                int nClip = BkaClipNear(cv, EPSW, cclip);
                if (nClip < 3) return;

                float cx[4], cy[4];
                const float CLIP_COORD_LIMIT = (float)(FB_WIDTH * 4);
                for (int i = 0; i < nClip; i++) {
                    float iw = 1.0f / cclip[i].w;
                    float tx = (cclip[i].x * iw + 1.0f) * 0.5f * (float)FB_WIDTH;
                    float ty = (1.0f - cclip[i].y * iw) * 0.5f * (float)FB_HEIGHT;
                    // Clamping preserves topology (winding / side) but keeps
                    // the scanline math from overflowing on near-plane
                    // vertices where 1/w is ~100.
                    if (tx < -CLIP_COORD_LIMIT) tx = -CLIP_COORD_LIMIT;
                    if (tx >  CLIP_COORD_LIMIT) tx =  CLIP_COORD_LIMIT;
                    if (ty < -CLIP_COORD_LIMIT) ty = -CLIP_COORD_LIMIT;
                    if (ty >  CLIP_COORD_LIMIT) ty =  CLIP_COORD_LIMIT;
                    cx[i] = tx;
                    cy[i] = ty;
                }
                BKVertex* csrc = (cv[0].w > EPSW) ? vt0 : ((cv[1].w > EPSW) ? vt1 : vt2);
                uint8_t cr = csrc->r, cg = csrc->g, cb = csrc->b, ca = csrc->a;

                static int s_clipcount = 0;
                if (s_clipcount++ < 20) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "TRI2-CLIP w=(%.2f %.2f %.2f) nClip=%d -> raster",
                        cv[0].w, cv[1].w, cv[2].w, nClip);
                }

                { static int s_cr = 0; if (s_cr++ < 20)
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "TRI2-DRAW n=%d color=(%d,%d,%d,%d) xy=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f)",
                        nClip, cr,cg,cb,ca,
                        cx[0],cy[0], cx[1],cy[1], cx[2],cy[2]); }
                {
                    static int s_bbox = 0;
                    if (s_bbox++ < 20)
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "BBOX n=%d x=(%.1f..%.1f) y=(%.1f..%.1f)",
                            nClip,
                            std::min({cx[0],cx[1],cx[2],cx[3]}), std::max({cx[0],cx[1],cx[2],cx[3]}),
                            std::min({cy[0],cy[1],cy[2],cy[3]}), std::max({cy[0],cy[1],cy[2],cy[3]}));
                }
                if (nClip == 3) {
                    RasterizeTriangle(cx[0],cy[0], cx[1],cy[1], cx[2],cy[2],
                        cr,cg,cb,ca, cr,cg,cb,ca, cr,cg,cb,ca);
                } else {
                    RasterizeTriangle(cx[0],cy[0], cx[1],cy[1], cx[2],cy[2],
                        cr,cg,cb,ca, cr,cg,cb,ca, cr,cg,cb,ca);
                    RasterizeTriangle(cx[0],cy[0], cx[2],cy[2], cx[3],cy[3],
                        cr,cg,cb,ca, cr,cg,cb,ca, cr,cg,cb,ca);
                }
                return;
            }
            // allIn: fall through to the existing TransformVertex path
        }

        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        {
            static int s_tri2_raster_log = 0;
            if (++s_tri2_raster_log % 200 == 1 || s_tri2_raster_log < 5) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "TRI2 -> raster #%d: screen=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f) fin=%d%d%d",
                    s_tri2_raster_log,
                    sx0, sy0, sx1, sy1, sx2, sy2,
                    std::isfinite(sx0), std::isfinite(sy0), std::isfinite(sx2));
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  PROJ  row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.projection[0][0], s_rdp.projection[0][1],
                    s_rdp.projection[0][2], s_rdp.projection[0][3],
                    s_rdp.projection[3][0], s_rdp.projection[3][1],
                    s_rdp.projection[3][2], s_rdp.projection[3][3]);
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "PROJFULL row1=(%.4f %.4f %.4f %.4f) row2=(%.4f %.4f %.4f %.4f)",
                    s_rdp.projection[1][0], s_rdp.projection[1][1],
                    s_rdp.projection[1][2], s_rdp.projection[1][3],
                    s_rdp.projection[2][0], s_rdp.projection[2][1],
                    s_rdp.projection[2][2], s_rdp.projection[2][3]);
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  MV    row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.modelview[0][0], s_rdp.modelview[0][1],
                    s_rdp.modelview[0][2], s_rdp.modelview[0][3],
                    s_rdp.modelview[3][0], s_rdp.modelview[3][1],
                    s_rdp.modelview[3][2], s_rdp.modelview[3][3]);
            }
        }
        { static int s_nc = 0; if (s_nc++ < 20)
            __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
                "TRI2-ALLIN color=(%d,%d,%d) screen=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f)",
                vt0->r, vt0->g, vt0->b,
                sx0, sy0, sx1, sy1, sx2, sy2); }
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a,
        vt0->s, vt0->t, vt1->s, vt1->t, vt2->s, vt2->t);
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v10];
        BKVertex* vt1 = &s_rdp.dmem[v11];
        BKVertex* vt2 = &s_rdp.dmem[v12];
        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        {
            static int s_tri2_raster_log = 0;
            if (++s_tri2_raster_log % 200 == 1 || s_tri2_raster_log < 5) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "TRI2 -> raster #%d: screen=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f) fin=%d%d%d",
                    s_tri2_raster_log,
                    sx0, sy0, sx1, sy1, sx2, sy2,
                    std::isfinite(sx0), std::isfinite(sy0), std::isfinite(sx2));
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  PROJ  row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.projection[0][0], s_rdp.projection[0][1],
                    s_rdp.projection[0][2], s_rdp.projection[0][3],
                    s_rdp.projection[3][0], s_rdp.projection[3][1],
                    s_rdp.projection[3][2], s_rdp.projection[3][3]);
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  MV    row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.modelview[0][0], s_rdp.modelview[0][1],
                    s_rdp.modelview[0][2], s_rdp.modelview[0][3],
                    s_rdp.modelview[3][0], s_rdp.modelview[3][1],
                    s_rdp.modelview[3][2], s_rdp.modelview[3][3]);
            }
        }
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a,
        vt0->s, vt0->t, vt1->s, vt1->t, vt2->s, vt2->t);
    }
}


// =======================================================================
// G_TRI1 (F3DEX2 variant, opcode 0xC4)
// w0 = [G_TRI1:8][v0:8][v1:8][v2:8]
// w1 = flag
// =======================================================================
static void Cmd_Tri1_F3DEX2(GfxCommand cmd) {
    g_bka_task_tri_count++;
    if (s_rdp.dmemVertexCount == 0) return;

    uint32_t v0 = (cmd.w0 >> 17) & 0x7F;
    uint32_t v1 = (cmd.w0 >> 9) & 0x7F;
    uint32_t v2 = (cmd.w0 >> 1) & 0x7F;

    if (v0 >= (uint32_t)s_rdp.dmemVertexCount ||
        v1 >= (uint32_t)s_rdp.dmemVertexCount ||
        v2 >= (uint32_t)s_rdp.dmemVertexCount) {
        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
            "Cmd_Tri1_F3DEX2: INVALID vertex indices %u,%u,%u (dmemVertexCount=%d) w0=0x%08X",
            v0, v1, v2, s_rdp.dmemVertexCount, cmd.w0);
        return;
    }

    BKVertex* vert0 = &s_rdp.dmem[v0];
    BKVertex* vert1 = &s_rdp.dmem[v1];
    BKVertex* vert2 = &s_rdp.dmem[v2];

    float sx0, sy0, sx1, sy1, sx2, sy2;
    TransformVertex(vert0, &sx0, &sy0);
    TransformVertex(vert1, &sx1, &sy1);
    TransformVertex(vert2, &sx2, &sy2);

    RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
        vert0->r, vert0->g, vert0->b, vert0->a,
        vert1->r, vert1->g, vert1->b, vert1->a,
        vert2->r, vert2->g, vert2->b, vert2->a,
        vert0->s, vert0->t, vert1->s, vert1->t, vert2->s, vert2->t);
}

// =======================================================================
// G_TRI2 (F3DEX2 variant, opcode 0x34)
// w0 = [G_TRI2:8][v0:8][v1:8][v2:8]   (first triangle)
// w1 = [flag:8][v3:8][v4:8][v5:8]     (second triangle, flag ignored)
// =======================================================================
static void Cmd_Tri2_F3DEX2(GfxCommand cmd) {
    g_bka_task_tri_count++;
    if (s_rdp.dmemVertexCount == 0) return;

    uint32_t v00 = (cmd.w0 >> 17) & 0x7F;
    uint32_t v01 = (cmd.w0 >> 9) & 0x7F;
    uint32_t v02 = (cmd.w0 >> 1) & 0x7F;
    uint32_t v10 = (cmd.w1 >> 17) & 0x7F;
    uint32_t v11 = (cmd.w1 >> 9) & 0x7F;
    uint32_t v12 = (cmd.w1 >> 1) & 0x7F;

    if (v00 >= (uint32_t)s_rdp.dmemVertexCount ||
        v01 >= (uint32_t)s_rdp.dmemVertexCount ||
        v02 >= (uint32_t)s_rdp.dmemVertexCount ||
        v10 >= (uint32_t)s_rdp.dmemVertexCount ||
        v11 >= (uint32_t)s_rdp.dmemVertexCount ||
        v12 >= (uint32_t)s_rdp.dmemVertexCount) {
        LOGW("Cmd_Tri2_F3DEX2: invalid vertex indices %u,%u,%u,%u,%u,%u",
             v00, v01, v02, v10, v11, v12);
        return;
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v00];
        BKVertex* vt1 = &s_rdp.dmem[v01];
        BKVertex* vt2 = &s_rdp.dmem[v02];
        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        {
            static int s_tri2_raster_log = 0;
            if (++s_tri2_raster_log % 200 == 1 || s_tri2_raster_log < 5) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "TRI2 -> raster #%d: screen=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f) fin=%d%d%d",
                    s_tri2_raster_log,
                    sx0, sy0, sx1, sy1, sx2, sy2,
                    std::isfinite(sx0), std::isfinite(sy0), std::isfinite(sx2));
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  PROJ  row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.projection[0][0], s_rdp.projection[0][1],
                    s_rdp.projection[0][2], s_rdp.projection[0][3],
                    s_rdp.projection[3][0], s_rdp.projection[3][1],
                    s_rdp.projection[3][2], s_rdp.projection[3][3]);
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  MV    row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.modelview[0][0], s_rdp.modelview[0][1],
                    s_rdp.modelview[0][2], s_rdp.modelview[0][3],
                    s_rdp.modelview[3][0], s_rdp.modelview[3][1],
                    s_rdp.modelview[3][2], s_rdp.modelview[3][3]);
            }
        }
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a,
        vt0->s, vt0->t, vt1->s, vt1->t, vt2->s, vt2->t);
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v10];
        BKVertex* vt1 = &s_rdp.dmem[v11];
        BKVertex* vt2 = &s_rdp.dmem[v12];
        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        {
            static int s_tri2_raster_log = 0;
            if (++s_tri2_raster_log % 200 == 1 || s_tri2_raster_log < 5) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "TRI2 -> raster #%d: screen=(%.1f,%.1f)(%.1f,%.1f)(%.1f,%.1f) fin=%d%d%d",
                    s_tri2_raster_log,
                    sx0, sy0, sx1, sy1, sx2, sy2,
                    std::isfinite(sx0), std::isfinite(sy0), std::isfinite(sx2));
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  PROJ  row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.projection[0][0], s_rdp.projection[0][1],
                    s_rdp.projection[0][2], s_rdp.projection[0][3],
                    s_rdp.projection[3][0], s_rdp.projection[3][1],
                    s_rdp.projection[3][2], s_rdp.projection[3][3]);
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "  MV    row0=(%.3f %.3f %.3f %.3f) row3=(%.3f %.3f %.3f %.3f)",
                    s_rdp.modelview[0][0], s_rdp.modelview[0][1],
                    s_rdp.modelview[0][2], s_rdp.modelview[0][3],
                    s_rdp.modelview[3][0], s_rdp.modelview[3][1],
                    s_rdp.modelview[3][2], s_rdp.modelview[3][3]);
            }
        }
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a,
        vt0->s, vt0->t, vt1->s, vt1->t, vt2->s, vt2->t);
    }
}

// =======================================================================
// G_MOVEMEM - Load matrix (opcode 0xDC)
// w0 = [opcode:8][length:8][offset:8][index:8]
// w1 = address of data in RDRAM
// =======================================================================
static void Cmd_MoveMem(GfxCommand cmd) {
    uint32_t length = (cmd.w0 >> 16) & 0xFF;
    uint32_t offset = (cmd.w0 >> 8) & 0xFF;
    uint32_t index  = cmd.w0 & 0xFF;
    uint32_t addr   = cmd.w1 & 0x0FFFFFFF;
    
    if (!gN64_RDRAM) return;
    
    // Matrix load: index 0x0E = G_MTX_MODELVIEW, 0x00 = G_MTX_PROJECTION
    // offset 0 = projection, offset 0 = modelview (upper bits differ)
    if (length == 8 && (index == 0x0E || index == 0x00)) {
        BKMatrix* target;
        // F3DEX2 G_MOVEMEM: index 0x0E = G_MTX_PROJECTION, 0x00 = G_MTX_MODELVIEW
        if (index == 0x0E) {
            target = &s_rdp.projection;
        } else {
            target = &s_rdp.modelview;
        }
        void *mtx_src = RDP_TranslateAddr(addr);
        if (mtx_src) Matrix_LoadFromN64(target, mtx_src);
    }
}

// =======================================================================
// G_MTX - Load matrix (opcode 0xBC)
// F3DEX2 format: w0 = [G_MTX:8][flag:8][param:16], w1 = matrix address
// For our initial implementation, we treat the matrix as modelview.
// =======================================================================
static void Cmd_MoveWord(GfxCommand cmd) {
    // F3DEX G_MOVEWORD: w0 = (0xBC << 24) | (index << 16) | offset
    uint32_t op     = (cmd.w0 >> 24) & 0xFF;
    uint32_t index, offset;
    if (op == 0xDB) {
        // F3DEX_GBI_2 (gDma1p): w0 = [op][index][offset_hi][offset_lo]
        index  = (cmd.w0 >> 16) & 0xFF;
        offset =  cmd.w0        & 0xFFFF;
    } else {
        // F3DEX_GBI (gImmp21): w0 = [op][offset_hi][offset_lo][index]
        index  =  cmd.w0        & 0xFF;
        offset = (cmd.w0 >> 8)  & 0xFFFF;
    }
    uint32_t data   =  cmd.w1;

    static int mw_log = 0;
    if (1) {
        LOGV(
            "Cmd_MoveWord index=0x%02X offset=0x%04X data=0x%08X", index, offset, data);
    }

    if (index == 0x06) { // G_MW_SEGMENT
        uint32_t segment = (offset / 4) & 0x0F;
        // Segment base must be a real N64 address.  Host-pointer low-32
        // values (0x70..0x7F) crash the game when used as segment bases;
        // the only safe values are physical RDRAM and KSEG0.
        uint32_t a = data;
        if (a == 0xFFFFFFFFu) {
            static int s_badseg = 0;
            if (s_badseg++ < 20)
                __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                    "Cmd_MoveWord SEGMENT seg=%u base=0x%08X INVALID — skipping",
                    segment, a);
            return;
        }
        s_rdp.segmentBase[segment] = (uintptr_t)a;

        static int seg_log = 0;
        if (seg_log++ < 20) {
            __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                "Cmd_MoveWord SEGMENT seg=%u base=0x%08X", segment, data);
        }
    }
}

// =======================================================================
// G_MTX - Load matrix (opcode 0x01)
// =======================================================================
static void Matrix_Multiply(BKMatrix result, const BKMatrix a, const BKMatrix b) {
    BKMatrix temp;
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            temp[i][j] = 0;
            for (int k = 0; k < 4; k++) {
                temp[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    memcpy(result, temp, sizeof(BKMatrix));
}

// F3DEX (non-2) matrix flag bits — Banjo-Kazooie
#ifndef G_MTX_PROJECTION
#define G_MTX_PROJECTION  0x01
#endif
#ifndef G_MTX_LOAD
#define G_MTX_LOAD        0x02
#endif
#ifndef G_MTX_PUSH
#define G_MTX_PUSH        0x04
#endif

#ifndef G_MTX_PROJECTION
#define G_MTX_PROJECTION  0x01
#endif
#ifndef G_MTX_LOAD
#define G_MTX_LOAD        0x02
#endif
#ifndef G_MTX_PUSH
#define G_MTX_PUSH        0x04
#endif

#ifndef G_MTX_PROJECTION
#define G_MTX_PROJECTION  0x01
#endif
#ifndef G_MTX_LOAD
#define G_MTX_LOAD        0x02
#endif
#ifndef G_MTX_PUSH
#define G_MTX_PUSH        0x04
#endif

static void Cmd_Mtx(GfxCommand cmd) {
    uint32_t flag = (cmd.w0 >> 16) & 0xFF;
    // Real F3DEX2 G_MTX only uses bits 0-2 (PROJECTION=0x01, LOAD=0x02,
    // PUSH=0x04).  Any higher bits set means the command was misdecoded;
    // without this guard, spurious G_MTX writes with flag=0x0B overwrite
    // the projection matrix with zeros loaded from garbage addresses.
    if (flag & 0xF8) {
        static int s_badmtx = 0;
        if (s_badmtx++ < 10)
            __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                "Cmd_Mtx: bad flag=0x%02X w1=0x%08X — skipping", flag, cmd.w1);
        return;
    }
    void *mtx_src = RDP_TranslateAddr(cmd.w1);
    if (!mtx_src) {
        static int null_log = 0;
        if (null_log++ < 6) {
            __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                "Cmd_Mtx NULL raw=0x%08X flag=0x%02X", cmd.w1, flag);
        }
        return;
    }

    // DIAGNOSTIC: always dump full 64 bytes for PROJECTION matrices
    if ((flag & 0x04) != 0) {
        static int s_proj_dump = 0;
        if (s_proj_dump++ < 3) {
            const uint8_t* mb = (const uint8_t*)mtx_src;
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                 "PROJBYTES raw=0x%08X src=%p: "
                "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X "
                "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X "
                "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X "
                "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
                cmd.w1, mtx_src,
                mb[0],mb[1],mb[2],mb[3],mb[4],mb[5],mb[6],mb[7],
                mb[8],mb[9],mb[10],mb[11],mb[12],mb[13],mb[14],mb[15],
                mb[16],mb[17],mb[18],mb[19],mb[20],mb[21],mb[22],mb[23],
                mb[24],mb[25],mb[26],mb[27],mb[28],mb[29],mb[30],mb[31],
                mb[32],mb[33],mb[34],mb[35],mb[36],mb[37],mb[38],mb[39],
                mb[40],mb[41],mb[42],mb[43],mb[44],mb[45],mb[46],mb[47],
                mb[48],mb[49],mb[50],mb[51],mb[52],mb[53],mb[54],mb[55],
                mb[56],mb[57],mb[58],mb[59],mb[60],mb[61],mb[62],mb[63]);
        }
    }

    // DIAGNOSTIC: dump segment table and the raw bytes at src
    static int mtx_diag = 0;
    if (mtx_diag++ < 8) {
        uint32_t seg = (cmd.w1 >> 24) & 0x0F;
        uint32_t off = cmd.w1 & 0x00FFFFFF;
        const uint8_t* mb = (const uint8_t*)mtx_src;
        LOGV(
"MTXDIAG w1=0x%08X seg=%u off=0x%06X segBase[%u]=0x%lX src=%p",
            cmd.w1, seg, off, seg,
            (unsigned long)s_rdp.segmentBase[seg], mtx_src);
        LOGV(
             "MTXBYTES @%p: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X  "
            "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
            mtx_src,
            mb[0],mb[1],mb[2],mb[3],mb[4],mb[5],mb[6],mb[7],
            mb[8],mb[9],mb[10],mb[11],mb[12],mb[13],mb[14],mb[15],
            mb[16],mb[17],mb[18],mb[19],mb[20],mb[21],mb[22],mb[23],
            mb[24],mb[25],mb[26],mb[27],mb[28],mb[29],mb[30],mb[31]);
    }

    if (s_mtx_dump_frame++ < 2) {
        const uint8_t* mb = (const uint8_t*)mtx_src;
        LOGV(
             "MTXSRC @%p: "
            "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X  "
            "%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
            mtx_src,
            mb[0],mb[1],mb[2],mb[3],mb[4],mb[5],mb[6],mb[7],
            mb[8],mb[9],mb[10],mb[11],mb[12],mb[13],mb[14],mb[15],
            mb[16],mb[17],mb[18],mb[19],mb[20],mb[21],mb[22],mb[23],
            mb[24],mb[25],mb[26],mb[27],mb[28],mb[29],mb[30],mb[31]);
    }

    static int s_mtx_dual = 0;
    if (s_mtx_dual++ < 8) {
        const uint8_t* p8 = (const uint8_t*)s_current_cmd;
        if (p8) {
            uint32_t w0_le = *(const uint32_t*)(p8 + 0);
            uint32_t w1_le = *(const uint32_t*)(p8 + 4);
            uint32_t w0_be = ((uint32_t)p8[8] << 24) | ((uint32_t)p8[9] << 16) |
                             ((uint32_t)p8[10] << 8) | (uint32_t)p8[11];
            uint32_t w1_be = ((uint32_t)p8[12] << 24) | ((uint32_t)p8[13] << 16) |
                             ((uint32_t)p8[14] << 8) | (uint32_t)p8[15];
            LOGV(
"MTXDUAL LE: w0=0x%08X w1=0x%08X | BE: w0=0x%08X w1=0x%08X",
                w0_le, w1_le, w0_be, w1_be);
        }
    }

    BKMatrix newMatrix;
    Matrix_LoadFromN64(&newMatrix, mtx_src);
//     { static int s_w0 = 0; if (s_w0++ < 12) { const uint8_t* raw = (const uint8_t*)s_current_cmd; LOGV("MTXW0 cur=%p raw=%02X%02X%02X%02X %02X%02X%02X%02X decoded_w0=0x%08X flag=0x%02X", (void*)raw, raw?raw[0]:0,raw?raw[1]:0,raw?raw[2]:0,raw?raw[3]:0,raw?raw[4]:0,raw?raw[5]:0,raw?raw[6]:0,raw?raw[7]:0, cmd.w0, flag); } }

    if (s_mtx_log_frame++ < 0) {
        __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
            "Cmd_Mtx flag=0x%02X raw=0x%08X src=%p diag=[%.4f %.4f %.4f %.4f]",
            flag, cmd.w1, mtx_src,
            newMatrix[0][0], newMatrix[1][1],
            newMatrix[2][2], newMatrix[3][3]);
    }

    { static int s_act = 0; if (s_act++ < 5000) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
        "MTXACT flag=0x%02X src=0x%08X new[0][0]=%.4f new[3][2]=%.4f | PROJ=%d LOAD=%d PUSH=%d",
        flag, cmd.w1, newMatrix[0][0], newMatrix[3][2],
        (flag & G_MTX_PROJECTION)?1:0, (flag & G_MTX_LOAD)?1:0, (flag & G_MTX_PUSH)?1:0); }

    if (flag & G_MTX_PROJECTION) {
        // Projection matrix slot
        if (flag & G_MTX_LOAD) {
            memcpy(s_rdp.projection, newMatrix, sizeof(BKMatrix));
            { static int s_d = 0; if (s_d++ < 3) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "PROJ-AFTER-LOAD r0=(%.4f %.4f %.4f %.4f) r3=(%.4f %.4f %.4f %.4f)",
                s_rdp.projection[0][0], s_rdp.projection[0][1], s_rdp.projection[0][2], s_rdp.projection[0][3],
                s_rdp.projection[3][0], s_rdp.projection[3][1], s_rdp.projection[3][2], s_rdp.projection[3][3]); }
        } else {
            BKMatrix tmp;
            Matrix_Multiply(tmp, newMatrix, s_rdp.projection); // new × existing
            memcpy(s_rdp.projection, tmp, sizeof(BKMatrix));
        }
    } else {
        // Modelview matrix slot
        if (flag & G_MTX_PUSH) {
            // RT64: PUSH saves current top, doesn't itself multiply.
            if (s_rdp.modelviewStackDepth < 16) {
                memcpy(s_rdp.modelviewStack[s_rdp.modelviewStackDepth],
                       s_rdp.modelview, sizeof(BKMatrix));
                s_rdp.modelviewStackDepth++;
            }
        }
        if (flag & G_MTX_LOAD) {
            memcpy(s_rdp.modelview, newMatrix, sizeof(BKMatrix));
        } else {
            BKMatrix tmp;
            Matrix_Multiply(tmp, newMatrix, s_rdp.modelview); // new × existing
            memcpy(s_rdp.modelview, tmp, sizeof(BKMatrix));
        }
    }

    // RT64 recomputes viewProj after every matrix op.
    { static int s_d2 = 0; if (s_d2++ < 3) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
        "PROJ-BEFORE-VP r0=(%.4f %.4f %.4f %.4f) r3=(%.4f %.4f %.4f %.4f) flag=0x%02X",
        s_rdp.projection[0][0], s_rdp.projection[0][1], s_rdp.projection[0][2], s_rdp.projection[0][3],
        s_rdp.projection[3][0], s_rdp.projection[3][1], s_rdp.projection[3][2], s_rdp.projection[3][3], flag); }
    Matrix_Multiply(s_rdp.viewProj, s_rdp.modelview, s_rdp.projection);
}

// =======================================================================
// G_FILLRECT - Solid color rectangle fill
// =======================================================================
static void Cmd_FillRect(GfxCommand cmd) {
    {
        static int s_fr = 0;
        if (s_fr++ < 40) {
            uint32_t x0 = (cmd.w0 >> 12) & 0xFFF;
            uint32_t y0 = cmd.w0 & 0xFFF;
            uint32_t x1 = (cmd.w1 >> 12) & 0xFFF;
            uint32_t y1 = cmd.w1 & 0xFFF;
            __android_log_print(ANDROID_LOG_ERROR, "BKA-FILLRECT",
                "FILLRECT x0=%u y0=%u x1=%u y1=%u w=%u h=%u",
                x0, y0, x1, y1,
                (x1 > x0) ? (x1 - x0 + 1) : 0,
                (y1 > y0) ? (y1 - y0 + 1) : 0);
        }
    }
    { static int s_fr = 0; if (s_fr++ < 10 || (s_fr % 200) == 0)
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "FILLRECT-ENTRY #%d w0=0x%08X w1=0x%08X", s_fr, cmd.w0, cmd.w1); }
    int32_t ulx = (int32_t)((cmd.w1 >> 14) & 0x3FF);
    int32_t uly = (int32_t)((cmd.w1 >> 2) & 0x3FF);
    int32_t lrx = (int32_t)((cmd.w0 >> 14) & 0x3FF);
    int32_t lry = (int32_t)((cmd.w0 >> 2) & 0x3FF);
    
    // Recompiled BK emits coordinates in pixels, not N64 .2 fixed point.
    ulx = std::max(0, ulx); uly = std::max(0, uly);
    lrx = std::min(lrx, FB_WIDTH); lry = std::min(lry, FB_HEIGHT);
    if (ulx >= lrx || uly >= lry) return;

    /* Fix BB: skip full-screen clears that appear AFTER geometry in the
     * same task.  B-K's recomp emits the frame's clear at the end of the
     * DL rather than the start, so we were wiping the frame we'd just
     * drawn.  Clear-before-geometry still works (frame init). */
    {
        bool fullscreen = (ulx <= 0 && uly <= 0 && lrx >= FB_WIDTH && lry >= FB_HEIGHT);
        /* Fix BB: reference the file-scope static directly.  The previous
         * patch shadowed it with an `extern` that bound to zero at link
         * time, so the check never fired and never skipped anything. */
        if (fullscreen && g_bka_task_tri_count > 0) {
            static int s_bb_skip = 0;
            if (s_bb_skip++ < 20)
                __android_log_print(ANDROID_LOG_ERROR, "BKA-RAST",
                    "FILL-SKIP full-screen clear after %d tris this task",
                    g_bka_task_tri_count);
            return;
        }
    }
    
    { static int s_fr = 0; if (s_fr++ < 100) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX", "FILLPRE fillRGB=(%d,%d,%d) ulx=%d uly=%d lrx=%d lry=%d w0=%08X w1=%08X", s_rdp.fillR, s_rdp.fillG, s_rdp.fillB, (int)ulx, (int)uly, (int)lrx, (int)lry, cmd.w0, cmd.w1); }
    uint16_t color = RGBA8_TO_RGB565(s_rdp.fillR, s_rdp.fillG, s_rdp.fillB);
    int activeFb = getActiveFramebuffer();
    uint16_t* fb = (uint16_t*)(gN64_RDRAM + g_active_fb_offset);
    { static int s_wr = 0; if (s_wr++ < 3)
        __android_log_print(ANDROID_LOG_ERROR, "BKA-WRITE",
            "FILL-WRITE rdr=%p ofs=0x%X fb=%p", (void*)gN64_RDRAM, g_active_fb_offset, (void*)fb); }
    {
        static int s_dbg = 0;
        if (s_dbg++ < 5 || (s_dbg % 100) == 0)
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "FILLRECT-DBG ulx=%d uly=%d lrx=%d lry=%d "
                "fillRGB=(%d,%d,%d) color=0x%04X fb=%p",
                ulx, uly, lrx, lry,
                s_rdp.fillR, s_rdp.fillG, s_rdp.fillB, color, (void*)fb);
    }
    for (int32_t y = uly; y < lry; y++)
        for (int32_t x = ulx; x < lrx; x++)
            *(volatile uint16_t *)&fb[y * FB_WIDTH + x] = color;
}

// =======================================================================
// G_TEXRECT - Textured rectangle
// =======================================================================
static void Cmd_TexRect(GfxCommand cmd) {
    { static int s_tr = 0; if (s_tr++ < 10 || (s_tr % 200) == 0)
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "TEXRECT-ENTRY #%d w0=0x%08X w1=0x%08X", s_tr, cmd.w0, cmd.w1); }
    int32_t xh = (int32_t)((cmd.w0 >> 12) & 0xFFF);
    int32_t yh = (int32_t)(cmd.w0 & 0xFFF);
    int32_t xl = (int32_t)((cmd.w1 >> 12) & 0xFFF);
    int32_t yl = (int32_t)(cmd.w1 & 0xFFF);
    int tile = (cmd.w1 >> 24) & 0x7;
    
    // Coordinates in pixels directly (no .2 fixed-point).
    if (xl < 0) xl = 0; if (yl < 0) yl = 0;
    if (xh > FB_WIDTH) xh = FB_WIDTH; if (yh > FB_HEIGHT) yh = FB_HEIGHT;
    if (xl >= xh || yl >= yh) return;
    if (tile < 0 || tile >= 8) return;
    
    auto& tdesc = s_rdp.tiles[tile];
    int32_t texW = (tdesc.sh >> 2) + 1, texH = (tdesc.th >> 2) + 1;
    if (texW <= 0) texW = 1; if (texH <= 0) texH = 1;
    
    int32_t rectW = xh - xl, rectH = yh - yl;
    if (rectW <= 0 || rectH <= 0) return;
    
    int32_t sBase = (tdesc.sl >> 5), tBase = (tdesc.tl >> 5);
    int activeFb = getActiveFramebuffer();
    uint16_t* fb = (uint16_t*)(gN64_RDRAM + g_active_fb_offset);
    uint8_t texel[4];
    
    for (int32_t dy = 0; dy < rectH; dy++) {
        for (int32_t dx = 0; dx < rectW; dx++) {
            int32_t s = sBase + (dx * texW) / rectW;
            int32_t t = tBase + (dy * texH) / rectH;
            RDP_FetchTexel(tile, s << 5, t << 5, texel);
            
            uint8_t r = (uint8_t)(((uint16_t)texel[0] * s_rdp.primR) / 255);
            uint8_t g = (uint8_t)(((uint16_t)texel[1] * s_rdp.primG) / 255);
            uint8_t b = (uint8_t)(((uint16_t)texel[2] * s_rdp.primB) / 255);
            uint8_t a = (uint8_t)(((uint16_t)texel[3] * s_rdp.primA) / 255);
            if (a < 8) continue;
            
            int32_t px = xl + dx, py = yl + dy;
            if (px >= 0 && px < FB_WIDTH && py >= 0 && py < FB_HEIGHT)
                fb[py * FB_WIDTH + px] = RGBA8_TO_RGB565(r, g, b);
        }
    }
}

// =======================================================================
// G_DL - Jump to display list
// =======================================================================
static void Cmd_DL(GfxCommand cmd, GfxCommand** outCmd, size_t* outRemaining) {
    uint32_t addr = cmd.w1;
    *outCmd = (GfxCommand*)RDP_TranslateAddr(addr);
    *outRemaining = 0xFFFFFFFF;
}

static void* RSP_ResolveGfxAddress(uint32_t addr) {
    uint32_t seg = (addr >> 28) & 0x0F;
    uint32_t offset = addr & 0x0FFFFFFF;
    if (seg != 0 && seg < 16 && s_rdp.segmentBase[seg] != 0) {
        return (uint8_t*)s_rdp.segmentBase[seg] + offset;
    }
    return RDP_TranslateAddr(addr);
}

// =======================================================================
// Main Dispatch
// =======================================================================

// Probe a sub-DL's encoding by reading its first N commands under both
// byte orders and counting which interpretation yields more valid F3DEX
// opcodes.  Returns 0=unknown, 1=LE, 2=BE.
static int bka_probe_dl_encoding(uint8_t* ptr) {
    if (!ptr) return 0;
    int le = 0, be = 0, le_bad = 0, be_bad = 0;
    for (int i = 0; i < 32; i++) {
        uint8_t* p = ptr + i * 8;
        if (!bka_is_readable(p + 8)) break;
        uint32_t w_le = *(uint32_t*)p;
        uint32_t w_be = __builtin_bswap32(w_le);
        uint8_t op_le = (uint8_t)(w_le >> 24);
        uint8_t op_be = (uint8_t)(w_be >> 24);
        if (op_le != 0x00) { if (bka_is_f3dex_opcode(op_le)) le++; else le_bad++; }
        if (op_be != 0x00) { if (bka_is_f3dex_opcode(op_be)) be++; else be_bad++; }
        if (i >= 7 && be_bad == 0 && be >= 8) return 2;
        if (i >= 7 && le_bad == 0 && le >= 8) return 1;
    }
    int _res = 0;
    if (be_bad == 0 && le_bad > 0) _res = 2;
    else if (le_bad == 0 && be_bad > 0) _res = 1;
    else if (be > le + 1) _res = 2;
    else if (le > be + 1) _res = 1;
    { static int _pc = 0; if (_pc++ < 60) __android_log_print(ANDROID_LOG_ERROR,
        "BKA_GFX", "PROBE-VOTE ptr=%p le=%d le_bad=%d be=%d be_bad=%d -> %d",
        (void*)ptr, le, le_bad, be, be_bad, _res); }
    return _res;
}

static int s_rspCallCount = 0;
static uint32_t s_opcount[256] = {0};
static uint32_t s_op_total = 0;


/* Fix L: robust stride detector.  Samples 3 consecutive 16-byte slots;
 * if ALL three have zero bytes 8-15, it's a padded (16-byte) DL.
 * Otherwise unpadded (8-byte).  The prior single-slot check false-
 * positived when two adjacent commands both had w1 == 0. */
/* Fix M: does the target actually look like a DL, or is it data?
 * Sample 8 slots, count how many have a whitelisted opcode byte at
 * position [0] (BE) or [3] (LE).  Real DLs score 7-8; data tables 3-4. */
static int bka_looks_like_dl(const uint8_t* p, int stride) {
    int valid = 0;
    for (int k = 0; k < 8; k++) {
        const uint8_t* s = p + (size_t)k * stride;
        if (bka_is_f3dex_opcode(s[0]) || bka_is_f3dex_opcode(s[3])) valid++;
    }
    return valid;
}

static inline int bka_detect_stride(const uint8_t* p) {
    /* Fix W: sample 8 slots at each candidate stride, count how many
     * contain a valid F3DEX2 opcode in either encoding.  Pick the
     * stride with more hits.  The prior zero-padding heuristic fails
     * on B-K's top-level DLs: bytes 8-15 of each 16-byte entry hold a
     * non-zero pointer + type field, not zero padding.  That made the
     * detector return 8 for the top level, so half the "commands"
     * walked were metadata words like 005BE460 -> op=0x60 (garbage). */
    int valid8 = 0, valid16 = 0;
    for (int k = 0; k < 8; k++) {
        uint32_t w = *(const uint32_t*)(p + k*8);
        uint8_t le_op = (uint8_t)(w >> 24);
        uint8_t be_op = (uint8_t)(w & 0xFF);
        if (bka_is_f3dex_opcode(le_op) || bka_is_f3dex_opcode(be_op)) valid8++;
    }
    for (int k = 0; k < 8; k++) {
        uint32_t w = *(const uint32_t*)(p + k*16);
        uint8_t le_op = (uint8_t)(w >> 24);
        uint8_t be_op = (uint8_t)(w & 0xFF);
        if (bka_is_f3dex_opcode(le_op) || bka_is_f3dex_opcode(be_op)) valid16++;
    }
    static int s_wlog = 0;
    if (s_wlog++ < 20) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA-STRIDE",
            "DETECT ptr=%p valid8=%d/8 valid16=%d/8 -> stride=%d",
            (void*)p, valid8, valid16, (valid16 >= valid8) ? 16 : 8);
    }
    return (valid16 >= valid8) ? 16 : 8;
}

void RSP_ProcessGfxTask(OSTask* tp) {
    { static int s_ent = 0; if (s_ent++ < 30) {
        uint8_t* dp = tp ? (uint8_t*)tp->t.data_ptr : nullptr;
        __android_log_print(ANDROID_LOG_ERROR, "BKA-DL",
            "ENTER #%d task=%p data_ptr=%p first8=%02X%02X%02X%02X %02X%02X%02X%02X",
            s_ent, (void*)tp, (void*)dp,
            dp?dp[0]:0,dp?dp[1]:0,dp?dp[2]:0,dp?dp[3]:0,
            dp?dp[4]:0,dp?dp[5]:0,dp?dp[6]:0,dp?dp[7]:0); } }
    if (bka_canary_post != 0xBEEFCAFEBABE5678ull) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "CANARY-OVERFLOW post=%016llX (s_rdp overflowed)",
            (unsigned long long)bka_canary_post);
        bka_canary_post = 0xBEEFCAFEBABE5678ull;
    }
    if (s_rdp.dmemVertexCount < 0 || s_rdp.dmemVertexCount > DMEM_VERTEX_COUNT) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "DMEM-COUNT-BAD: %d (should be 0..256)", s_rdp.dmemVertexCount);
        s_rdp.dmemVertexCount = DMEM_VERTEX_COUNT;
    }
    /* Diagnostic: dump FULL top-level task buffer to logcat, once. */
    {
        static int s_fulldump = 0;
        if (s_fulldump++ < 1 && tp && tp->t.data_ptr && tp->t.data_size > 0) {
            const uint8_t* d = (const uint8_t*)tp->t.data_ptr;
            uint32_t sz = tp->t.data_size;
            if (sz > 4096) sz = 4096;
            for (uint32_t off = 0; off < sz; off += 16) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA-FULLTASK",
                    "+%04X: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
                    off,
                    d[off],  d[off+1],d[off+2],d[off+3],d[off+4],d[off+5],d[off+6],d[off+7],
                    d[off+8],d[off+9],d[off+10],d[off+11],d[off+12],d[off+13],d[off+14],d[off+15]);
            }
        }
    }
    /* Diagnostic: dump first 128 bytes of the top-level DL, decoded
     * BOTH ways, so we can finally pin the wrapper format. */
    {
        static int s_tl_dump = 0;
        if (s_tl_dump++ < 3 && tp && tp->t.data_ptr) {
            const uint8_t* d = (const uint8_t*)tp->t.data_ptr;
            for (int row = 0; row < 16; row++) {
                const uint8_t* r = d + row * 8;
                uint32_t le = (uint32_t)(r[0] | (r[1]<<8) | (r[2]<<16) | (r[3]<<24));
                uint32_t be = (uint32_t)((r[0]<<24) | (r[1]<<16) | (r[2]<<8) | r[3]);
                __android_log_print(ANDROID_LOG_ERROR, "BKA-TLD",
                    "t#%d +%03X: %02X%02X%02X%02X %02X%02X%02X%02X  LE_op=%02X BE_op=%02X",
                    s_rspCallCount, row * 8,
                    r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],
                    (uint8_t)(le >> 24), (uint8_t)(be >> 24));
            }
        }
    }
    s_rspCallCount++;
    /* Fix U: increment frame gen at task ENTRY, not exit.  The exit
     * increments are after possible early returns (drift, G_ENDDL,
     * post-pop unwind) so gen stayed at 0 and the video upload gate
     * skipped every frame except its 500ms stale fallback. */
    g_bka_frame_gen++;
    g_bka_task_tri_count = 0;
    g_bka_task_pops = 0;
    g_bka_task_max_depth = 0;

    // Probe known RDRAM offsets where the DL thinks vertex data lives
    static int s_probe = 0;
    if (s_probe++ < 1 && gN64_RDRAM) {
        const uint8_t* rdram = gN64_RDRAM;
        LOGV(
            "RDRAMPROBE @0x79153F: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
            rdram[0x79153F],rdram[0x791540],rdram[0x791541],rdram[0x791542],
            rdram[0x791543],rdram[0x791544],rdram[0x791545],rdram[0x791546],
            rdram[0x791547],rdram[0x791548],rdram[0x791549],rdram[0x79154A],
            rdram[0x79154B],rdram[0x79154C],rdram[0x79154D],rdram[0x79154E]);
        LOGV(
            "RDRAMPROBE @0xF9153F: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
            rdram[0xF9153F],rdram[0xF91540],rdram[0xF91541],rdram[0xF91542],
            rdram[0xF91543],rdram[0xF91544],rdram[0xF91545],rdram[0xF91546],
            rdram[0xF91547],rdram[0xF91548],rdram[0xF91549],rdram[0xF9154A],
            rdram[0xF9154B],rdram[0xF9154C],rdram[0xF9154D],rdram[0xF9154E]);
        LOGV(
            "RDRAMPROBE @0x3E45C0: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
            rdram[0x3E45C0],rdram[0x3E45C1],rdram[0x3E45C2],rdram[0x3E45C3],
            rdram[0x3E45C4],rdram[0x3E45C5],rdram[0x3E45C6],rdram[0x3E45C7],
            rdram[0x3E45C8],rdram[0x3E45C9],rdram[0x3E45CA],rdram[0x3E45CB],
            rdram[0x3E45CC],rdram[0x3E45CD],rdram[0x3E45CE],rdram[0x3E45CF]);
    }

    uint8_t* rsp_rdram = gN64_RDRAM;  // avoid unused warning
    (void)rsp_rdram;
    s_mtx_log_frame = 0;
    s_mtx_dump_frame = 0;
    if (true) { // BKA_MOD: log every call
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "RSP_ProcessGfxTask CALL #%d: tp=%p type=%d data=%p size=%u dmemVertexCount=%d",
            s_rspCallCount, tp, tp ? tp->t.type : -1, tp ? tp->t.data_ptr : nullptr,
            tp ? tp->t.data_size : 0, s_rdp.dmemVertexCount);
    }
    {
        static int s_topdump = 0;
        if (s_topdump++ < 20 && tp && tp->t.data_ptr) {
            const uint8_t* d = (const uint8_t*)tp->t.data_ptr;
            __android_log_print(ANDROID_LOG_ERROR, "BKA-PROBE",
                "TOPDL ptr=%p bytes: %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X | %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
                tp->t.data_ptr,
                d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7],
                d[8],d[9],d[10],d[11],d[12],d[13],d[14],d[15],
                d[16],d[17],d[18],d[19],d[20],d[21],d[22],d[23],
                d[24],d[25],d[26],d[27],d[28],d[29],d[30],d[31]);
        }
    }

    {
        static int s_taskbytes = 0;
        if (tp && tp->t.data_ptr && s_taskbytes < 2) {
            s_taskbytes++;
            const uint8_t* d = (const uint8_t*)tp->t.data_ptr;
            for (int row = 0; row < 32; row++) {
                const uint8_t* r = d + row * 8;
                unsigned le = (unsigned)(r[0] | (r[1]<<8) | (r[2]<<16) | (r[3]<<24));
                unsigned be = (unsigned)((r[0]<<24) | (r[1]<<16) | (r[2]<<8) | r[3]);
                unsigned le2 = (unsigned)(r[4] | (r[5]<<8) | (r[6]<<16) | (r[7]<<24));
                unsigned be2 = (unsigned)((r[4]<<24) | (r[5]<<16) | (r[6]<<8) | r[7]);
                __android_log_print(ANDROID_LOG_ERROR, "BKA-FULLDL",
                    "t#%d +%03X: %02X%02X%02X%02X %02X%02X%02X%02X  w0_LE=%08X w0_BE=%08X  w1_LE=%08X w1_BE=%08X",
                    s_rspCallCount, row * 8,
                    r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],
                    le, be, le2, be2);
            }
        }
    }

    if (!tp || !tp->t.data_ptr || tp->t.data_size == 0) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "early return: tp=%p data=%p size=%u",
            tp, tp ? tp->t.data_ptr : nullptr, tp ? tp->t.data_size : 0);
        return;
    }

    // Hex dump removed to reduce log overhead.

    RDP_InitState();

    // ---- DL_DUMP_ADDED ----
    {
        const uint8_t* d = (const uint8_t*)tp->t.data_ptr;
        uint32_t sz = tp->t.data_size;
        uint32_t lim = sz < 512 ? sz : 512;
        for (uint32_t off = 0; off < lim; off += 32) {
            uint32_t o2 = off + 16;
            /* DLRAW disabled */;
        }
    }
    // ---- end DL_DUMP_ADDED ----

    // Diagnostic: dump first 16 bytes of task data
    {
        const unsigned char *dp = (const unsigned char*)tp->t.data_ptr;
        for (int off = 0; off < 32; off += 16) {
            LOGV(
                "RSP task data[%02d]: %02x %02x %02x %02x %02x %02x %02x %02x  %02x %02x %02x %02x %02x %02x %02x %02x",
                off,
                dp[off+0], dp[off+1], dp[off+2], dp[off+3],
                dp[off+4], dp[off+5], dp[off+6], dp[off+7],
                dp[off+8], dp[off+9], dp[off+10], dp[off+11],
                dp[off+12], dp[off+13], dp[off+14], dp[off+15]);
        }
    }

    // Only clear framebuffers on first call (static flag)
    static bool s_firstFrame = true;
    if (s_firstFrame) {
        memset(gFramebuffers[0], 0, sizeof(gFramebuffers[0]));
        memset(gFramebuffers[1], 0, sizeof(gFramebuffers[1]));
        s_firstFrame = false;
        __android_log_print(ANDROID_LOG_INFO, "BKA_GFX", "Framebuffers cleared (first frame)");
    }


    struct DListFrame {
        uint8_t *ptr;
        uint8_t *end;
    };

    DListFrame stack[64];
    int depth = 0;
    size_t current_stride = 8;
    size_t stack_stride[64];
    uintptr_t stack_dl_base[64];
    int stack_enc[64];          /* per-frame: 0=unknown, 1=LE, 2=BE */
    int cur_dl_enc = 0;         /* revert E1: unknown, will be probed */
    bool s_seen_gdl_at_depth0 = false;   /* Fix Q: wrapper detection */
    bool s_just_popped = false;          /* Fix R: set by G_ENDDL pop, cleared on dispatch */
    uintptr_t visited_dl_addrs[256];
    int visited_dl_count = 0;
    uint8_t *cur = (uint8_t*)tp->t.data_ptr;
    uint8_t *cur_end = cur + tp->t.data_size;

    const size_t MAX_TOTAL_CMDS = 20000;   /* real RSP tasks are <2000 cmds */
    const size_t MAX_DL_CMDS = 5000;
    size_t total = 0;
    size_t dl_cmds = 0;
    int zero_run = 0;
    int unknown_opcode_run = 0;
    int cmds_since_progress = 0;
    size_t gdl_jumps = 0;
    const size_t MAX_GDL_JUMPS = 200;
    int consecutive_bad_gdl = 0;
    struct timespec start_ts, now_ts;
    clock_gettime(CLOCK_MONOTONIC, &start_ts);
    bool log_after_jump = false;
    int jump_log_count = 0;

    /* Ring buffer of last accepted commands for drift diagnosis. */
    struct { uint8_t* ptr; uint32_t w0, w1; uint8_t op; int enc; size_t stride; int depth; } s_lastcmds[32];
    int s_lastcmd_idx = 0;
    memset(s_lastcmds, 0, sizeof(s_lastcmds));
    while (cur + current_stride <= cur_end) {
        if (++total > MAX_TOTAL_CMDS) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "runaway display list: exceeded %u total commands", (unsigned)MAX_TOTAL_CMDS);
            break;
        }

        if (total >= 36 && total <= 60) {
            LOGV(
                 "LOOP iter=%zu cur=%p cur_end=%p depth=%d stride=%zu",
                total, cur, cur_end, depth, current_stride);
        }

        if (++dl_cmds > MAX_DL_CMDS) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "runaway display list: exceeded %u commands in current DL", (unsigned)MAX_DL_CMDS);
            break;
        }

        // Yield to other threads every 4 commands and enforce time budget
        if ((total & 0x01) == 0) {
            sched_yield();
            if ((total & 0x0F) == 0) {
                clock_gettime(CLOCK_MONOTONIC, &now_ts);
                long long elapsed_ms = (now_ts.tv_sec - start_ts.tv_sec) * 1000 + (now_ts.tv_nsec - start_ts.tv_nsec) / 1000000;
                if (elapsed_ms > 2000) {
                    __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                        "RSP time budget exceeded at cmd %zu (%lld ms), breaking", total-1, elapsed_ms);
                    break;
                }
            }
        }

        GfxCommand c = {0};
        memcpy(&c, cur, 8);
        s_current_cmd = cur;
        {
            static int s_last_enc = -1;
            static int s_enc_flips = 0;
            if (s_last_enc != -1 && s_last_enc != cur_dl_enc && s_enc_flips++ < 20) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "ENCFLIP at cur=%p total=%zu depth=%d %d -> %d bytes=%02X%02X%02X%02X",
                    (void*)cur, total, depth, s_last_enc, cur_dl_enc,
                    cur[0],cur[1],cur[2],cur[3]);
            }
            s_last_enc = cur_dl_enc;
        }

        /* Per-DL encoding detection.  Once a DL is detected as BE, every
         * command in it must be byte-swapped -- not just the ones whose low
         * byte happens to fall in [0xB0, 0xCF].  RDP setup opcodes
         * (G_RDPSETOTHERMODE=0xE7, G_SETCOMBINE=0xFC, ...) live above 0xCF
         * and would otherwise be misread as a stale G_VTX.  Sticky per DL;
         * reset to unknown on G_DL jump. */
        {
            uint8_t hi = (uint8_t)(c.w0 >> 24);
            uint8_t lo = (uint8_t)(c.w0 & 0xFF);
            if (cur_dl_enc == 2) {
                c.w0 = __builtin_bswap32(c.w0);
                c.w1 = __builtin_bswap32(c.w1);
            } else if (cur_dl_enc == 0) {
                // Use the full F3DEX opcode table, not just [0xB0,0xCF].
                // Opcodes 0xFC (SETCOMBINE), 0xE7 (RDPSETOTHERMODE), etc.
                // are outside that range but still legitimate BE opcodes.
                bool hi_is_g = bka_is_f3dex_opcode(hi);
                bool lo_is_g = bka_is_f3dex_opcode(lo);
                if (hi == 0x00 && lo != 0x00 && lo_is_g) {
                    /* LE reads as NOP (padding) but BE reads as a real opcode.
                     * Banjo-Kazooie never starts a sub-DL with NOP padding,
                     * so this is a BE-formatted DL. */
                    c.w0 = __builtin_bswap32(c.w0);
                    c.w1 = __builtin_bswap32(c.w1);
                    cur_dl_enc = 2;
                    static int s_nop_be = 0;
                    if ((s_nop_be++ % 500) == 0)
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "DLENC NOP->BE @%p bytes %02X%02X%02X%02X -> op=0x%02X",
                            cur, cur[0],cur[1],cur[2],cur[3],
                            (uint8_t)(c.w0 >> 24));
                } else if (lo == 0x00 && hi != 0x00 && hi_is_g) {
                    /* Mirror: BE reads as NOP, LE is real. */
                    cur_dl_enc = 1;
                } else                 if (hi_is_g && lo_is_g) {
                    /* Ambiguous: both byte[0] and byte[3] are valid F3DEX
                     * opcodes.  Examples:
                     *   06 00 00 BC: LE = gSPSegment(0,0), BE = G_DL
                     *   FC 62 FE 04: LE = G_VTX,          BE = G_SETCOMBINE
                     * Cannot distinguish by opcode alone.  Default to LE
                     * (ARM-native writes go through recompiled code that
                     * stores u32 as LE), and rely on the NOP-detection rule
                     * above to catch BE-formatted DLs (they always start
                     * with a byte[0] opcode and byte[3]=0x00). */
                    cur_dl_enc = 1;
                    static int s_amb = 0;
                    if ((s_amb++ % 500) == 0)
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "DLENC AMBIG->LE @%p bytes %02X%02X%02X%02X",
                            cur, cur[0],cur[1],cur[2],cur[3]);
                } else if (lo_is_g && !hi_is_g) {
                    c.w0 = __builtin_bswap32(c.w0);
                    c.w1 = __builtin_bswap32(c.w1);
                    cur_dl_enc = 2;
                    static int s_be_log = 0;
                    if ((s_be_log++ % 500) == 0)
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "DLENC BE @%p first bytes %02X%02X%02X%02X -> op=0x%02X",
                            cur, cur[0],cur[1],cur[2],cur[3],
                            (uint8_t)(c.w0 >> 24));
                } else if (hi_is_g && !lo_is_g) {
                    cur_dl_enc = 1;
                }
            }
        }
                /* Fix X: removed Fix L's padding sanity check.  B-K's recomp
         * layout is 8 bytes command + 8 bytes payload (host pointer /
         * metadata), NOT 8 bytes command + 8 bytes zero padding.  The
         * check was bailing on every valid command, dropping the walker
         * down to 1-3 commands per task. */
        /* Fix O: RGBA fill-pattern detector.  Bytes 4-7 of a real command
         * are a w1 pointer/param.  If they are a repeating byte pattern
         * (0x787878xx, 0x464646xx, 0x3C3C3Cxx), we are reading texture
         * data as commands.  Count as drift without dispatching. */
        {
            uint8_t b4 = (c.w1 >> 24) & 0xFF;
            uint8_t b5 = (c.w1 >> 16) & 0xFF;
            uint8_t b6 = (c.w1 >>  8) & 0xFF;
            if (b4 == b5 && b5 == b6 && b4 != 0 && b4 != 0xFF) {
                unknown_opcode_run += 3;
                if (unknown_opcode_run >= 8) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "walker: fill-pattern at cur=%p depth=%d w0=%08X w1=%08X -- drifting",
                        (void*)cur, depth, c.w0, c.w1);
                    return;
                }
                cur += current_stride;
                continue;
            }
        }
        g_bka_dl_cur = cur;
        uint8_t opcode = GFX_OPCODE(c);
        /* Fix R: after popping out of a G_DL, verify the parent has a
         * valid command next.  If not, the parent DL has ended -- the
         * walker did not return to a real command sequence.  Unwind or
         * terminate cleanly, do NOT drift into the metadata tail. */
        if (s_just_popped && !bka_is_f3dex_opcode(opcode)) {
            static int s_rterm = 0;
            if (s_rterm++ < 30)
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "walker: post-pop non-command at cur=%p depth=%d op=0x%02X -- unwinding",
                    (void*)cur, depth, opcode);
            if (depth > 0) {
                depth--;
                cur = stack[depth].ptr;
                cur_end = stack[depth].end;
                current_stride = stack_stride[depth];
                s_dl_base = stack_dl_base[depth];
                cur_dl_enc = stack_enc[depth];
                dl_cmds = 0;
                zero_run = 0;
                s_just_popped = false;
                continue;
            }
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "walker: top-level wrapper ended cleanly at cur=%p", (void*)cur);
            break;
        }
        s_just_popped = false;
                s_opcount[opcode]++;
                if ((++s_op_total % 500) == 0) {
                    char obuf[2048]; int on = 0;
                    for (int k = 0; k < 256 && on < (int)sizeof(obuf) - 16; k++)
                        if (s_opcount[k]) on += snprintf(obuf + on, sizeof(obuf) - on, "%02X:%u ", k, s_opcount[k]);
                    __android_log_print(ANDROID_LOG_ERROR, "BKA-OPC", "seen=%u %s", s_op_total, obuf);
                }
        {
            static int s_enc_dump = 0;
            if ((s_enc_dump++ % 2000) == 0) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                     "ENCDUMP @%p enc=%d w0=0x%08X w1=0x%08X op=0x%02X depth=%d first4=%02X%02X%02X%02X",
                    cur, cur_dl_enc, c.w0, c.w1, opcode, depth,
                    cur[0], cur[1], cur[2], cur[3]);
            }
        }
        {
            if ((total % 500) == 0 || total <= 5) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                     "CMD t#%zu @%p raw=%02X%02X%02X%02X %02X%02X%02X%02X w0=0x%08X w1=0x%08X op=0x%02X enc=%d depth=%d",
                    total, cur, cur[0],cur[1],cur[2],cur[3],cur[4],cur[5],cur[6],cur[7],
                    c.w0, c.w1, opcode, cur_dl_enc, depth);
            }
        }
        if (bka_is_f3dex_opcode(opcode)) unknown_opcode_run = 0;
        else unknown_opcode_run++;
        if (opcode == 0x04 && total <= 5) {
            const uint8_t *raw = cur;
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "RAW Vtx bytes: %02x %02x %02x %02x %02x %02x %02x %02x",
                raw[0], raw[1], raw[2], raw[3],
                raw[4], raw[5], raw[6], raw[7]);
        }

        // Fix L: top-level stride via multi-slot detector (once, not per loop)
        current_stride = 16;   /* Fix Y1: top-level is always 8+8 */

        if (total <= 100) {
            if (log_after_jump) jump_log_count++;
            /* CMDX disabled */;
        }

        // Any recognized opcode counts as progress.  Only sequences of
        // unrecognized bytes indicate drift; a DL that opens with 50
        // setup commands (texture / combiner / tile) is completely normal.
        if (bka_is_f3dex_opcode(opcode)) {
            cmds_since_progress = 0;
        } else {
            cmds_since_progress++;
        }
        s_lastcmds[s_lastcmd_idx & 31].ptr = cur;
        s_lastcmds[s_lastcmd_idx & 31].w0 = c.w0;
        s_lastcmds[s_lastcmd_idx & 31].w1 = c.w1;
        s_lastcmds[s_lastcmd_idx & 31].op = opcode;
        s_lastcmds[s_lastcmd_idx & 31].enc = cur_dl_enc;
        s_lastcmds[s_lastcmd_idx & 31].stride = current_stride;
        s_lastcmds[s_lastcmd_idx & 31].depth = depth;
        s_lastcmd_idx++;
        cur += current_stride;

        if (c.w0 != 0 || c.w1 != 0) zero_run = 0;
        if (c.w0 == 0 && c.w1 == 0) {
            zero_run = (c.w0 == 0 && c.w1 == 0) ? (zero_run + 1) : 0;
            if (zero_run >= 2) {
                if (depth > 0) {
                    // Skip zero padding to find actual commands in nested DL
                    uint8_t* probe = cur;
                    int skipped = 0;
                    while (probe + 8 <= cur_end && (probe[0] == 0 && probe[1] == 0 && probe[2] == 0 && probe[3] == 0)) {
                        probe += current_stride;
                        skipped++;
                    }
                    if (probe + 8 <= cur_end) {
                        // Found a non-zero command; jump to it
                        cur = probe;
                        zero_run = 0;
                        dl_cmds = 0;
                        continue;
                    } else {
                        // No non-zero commands found; pop stack
                        depth--;
                        cur = stack[depth].ptr;
                        cur_end = stack[depth].end;
                        current_stride = stack_stride[depth];
                        s_dl_base = stack_dl_base[depth];
                        cur_dl_enc = stack_enc[depth];
                        dl_cmds = 0;
                        zero_run = 0;
                        continue;
                    }
                } else {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "zero-run break at cmd %zu, depth=%d", total - 1, depth);
                    break;
                }
            }
        } else {
            zero_run = 0;
        }

        // Nested display lists in Banjo-Kazooie often omit ENDDL and are
        // followed by vertex/index data. We now use the task data size
        // as the boundary, so no early stop is needed.

                switch (opcode) {
            case 0xAF: // G_LOAD_UCODE - not needed for software RDP
            case 0xB3: // G_RDPHALF_2
            case 0xB5: // G_LINE3D
            case 0xBD: // G_POPMTX - accepted, not implemented
            case 0x00:
            case 0xC0:
            case 0xE8:
            case 0xE7:
            case 0xE9:
            case 0xE6:
            case 0xE1:
            case 0xF1:
            case 0xF0:
            case 0x02:
            case 0xDA:            case 0xBE:
            case 0xBA:
            case 0xB9:
            case 0xB7:
            case 0xB6:
            case 0xED:
            case 0xFF:
                break;
            case 0x58: // G_SETTILESIZE? no-op for now
            case 0xE0: // Unknown but appears frequently; treat as no-op
            case 0x90: // Unknown
            case 0x88: // Unknown
            case 0x70: // Unknown
                break;

            case 0xF7: Cmd_SetFillColor(c); break;
            case 0xFA: Cmd_SetPrimColor(c); break;
            case 0xFB: Cmd_SetEnvColor(c); break;
            case 0xE2: Cmd_SetOtherModeL(c); break;
            case 0xE3: Cmd_SetOtherModeH(c); break;
            case 0xFC: Cmd_SetCombine(c); break;
            case 0xD7: Cmd_Texture(c); break;
            case 0xBB: Cmd_Texture(c); break;   // F3DEX (non-2) G_TEXTURE
            case 0xF5: Cmd_SetTile(c); break;
            case 0xF2: Cmd_SetTileSize(c); break;
            case 0xFD: Cmd_SetTImg(c); break;
            case 0xF3: Cmd_LoadBlock(c); break;
            case 0xF4: Cmd_LoadTile(c); break;
            case 0xF6: Cmd_FillRect(c); break;
            case 0xE4: case 0xE5: Cmd_TexRect(c); break;

            case 0x01: Cmd_Mtx(c); break;
            case 0x04:
                {
                    /* Guard: a misdecoded byte can produce a "G_VTX" whose w1
                     * is a flag/length field (top 16 bits all set) rather than
                     * a real segment address. Real N64 addresses never start
                     * with 0xFF. Count these as unknown opcodes so the walker
                     * bails instead of looping on garbage. */
                    if (c.w1 >= 0xF0000000u) {
                        unknown_opcode_run += 3;
                        opcode = 0xFF;   // force the drift counter below to increment
                        if (unknown_opcode_run >= 16) {
                            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                                "walker: spurious G_VTX addr=0x%08X at cur=%p depth=%d — bailing",
                                c.w1, (void*)cur, depth);
                            return;
                        }
                        break;
                    }
                    {
                        static int s_ctx = 0;
                        if (s_ctx++ < 0) {
                            uint8_t* p = (uint8_t*)cur;
                            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                                "GVTX-CTX cur=%p\n"
                                "  +0 : %02X%02X%02X%02X %02X%02X%02X%02X\n"
                                "  +8 : %02X%02X%02X%02X %02X%02X%02X%02X\n"
                                "  +16: %02X%02X%02X%02X %02X%02X%02X%02X\n"
                                "  +24: %02X%02X%02X%02X %02X%02X%02X%02X",
                                (void*)cur,
                                p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],
                                p[8],p[9],p[10],p[11],p[12],p[13],p[14],p[15],
                                p[16],p[17],p[18],p[19],p[20],p[21],p[22],p[23],
                                p[24],p[25],p[26],p[27],p[28],p[29],p[30],p[31]);
                        }
                    }
                    static int vtx_log_count = 0;
                    if (++vtx_log_count <= 3) {
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "G_VTX@%p w0=0x%08X w1=0x%08X next8=%02X%02X%02X%02X %02X%02X%02X%02X",
                            cur, c.w0, c.w1,
                            cur[8],cur[9],cur[10],cur[11],
                            cur[12],cur[13],cur[14],cur[15]);
                        /* SYNC disabled */ (void)0; __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "SYNC cur=%p bytes_cur=%02X%02X%02X%02X %02X%02X%02X%02X "
                            "LE_w0=0x%08X LE_w1=0x%08X BE_w0=0x%08X BE_w1=0x%08X "
                            "c.w0=0x%08X c.w1=0x%08X",
                            cur,
                            cur[0],cur[1],cur[2],cur[3],cur[4],cur[5],cur[6],cur[7],
                            (unsigned)(cur[0] | (cur[1]<<8) | (cur[2]<<16) | (cur[3]<<24)),
                            (unsigned)(cur[4] | (cur[5]<<8) | (cur[6]<<16) | (cur[7]<<24)),
                            (unsigned)((cur[0]<<24) | (cur[1]<<16) | (cur[2]<<8) | cur[3]),
                            (unsigned)((cur[4]<<24) | (cur[5]<<16) | (cur[6]<<8) | cur[7]),
                            c.w0, c.w1);
                    }
                    if (c.w1 >= 0x01000000) {
                        static int s_raw = 0;
                        if (s_raw++ < 6) {
                            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                                "VTXRAW32 @%p = %02X%02X%02X%02X %02X%02X%02X%02X | %02X%02X%02X%02X %02X%02X%02X%02X | prev8: %02X%02X%02X%02X %02X%02X%02X%02X",
                                cur,
                                cur[0],cur[1],cur[2],cur[3],cur[4],cur[5],cur[6],cur[7],
                                cur[8],cur[9],cur[10],cur[11],cur[12],cur[13],cur[14],cur[15],
                                cur[-8],cur[-7],cur[-6],cur[-5],cur[-4],cur[-3],cur[-2],cur[-1]);
                            // Scan RDRAM for LE-encoded 0xFFF9153F = bytes 3F 15 F9 FF.
                            if (gN64_RDRAM) {
                                const uint8_t pat[4] = {0x3F, 0x15, 0xF9, 0xFF};
                                int found = 0;
                                for (uint32_t off = 0; off + 4 <= 0x04000000u && found < 8; off += 4) {
                                    if (gN64_RDRAM[off]     == pat[0] &&
                                        gN64_RDRAM[off + 1] == pat[1] &&
                                        gN64_RDRAM[off + 2] == pat[2] &&
                                        gN64_RDRAM[off + 3] == pat[3]) {
                                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                                            "PATFIND fff9153f @ rdram+0x%06X", off);
                                        found++;
                                    }
                                }
                                static int s_pf = 0;
                                if (found == 0 && s_pf++ < 2) {
                                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                                        "PATFIND fff9153f: not present in RDRAM");
                                }
                            }
                            // Dump the 40 preceding 8-byte commands in the DL containing this G_VTX.
                            {
                                static int s_dumpprev = 0;
                                if (s_dumpprev++ < 2) {
                                    uint8_t* base = cur - 40 * 8;
                                    for (int k = 0; k < 40; k++) {
                                        uint8_t* e = base + k * 8;
                                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                                            "DLPREV[%02d] %02X%02X%02X%02X %02X%02X%02X%02X",
                                            k,
                                            e[0], e[1], e[2], e[3],
                                            e[4], e[5], e[6], e[7]);
                                    }
                                }
                            }
                        }
                    }
                }
                Cmd_Vtx(c);
                break;
            case 0xBF:
            case 0xB1:
            case 0xC4:
            case 0x34:
                LOGV(
                    "DISPATCH TRI opcode=0x%02X", opcode);
                {
                    static int tri_log_count = 0;
                    if (++tri_log_count <= 10) {
                        __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                            "GEOMETRY: op=0x%02X (tri) w0=0x%08X w1=0x%08X total=%zu depth=%d",
                            opcode, c.w0, c.w1, total-1, depth);
                    }
                }
                if (opcode == 0xBF) Cmd_Tri1(c);
                else if (opcode == 0xB1) Cmd_Tri2(c);
                else if (opcode == 0xC4) Cmd_Tri2_F3DEX2(c);
                else if (opcode == 0x34) Cmd_Tri1_F3DEX2(c);
                break;
            case 0x03: Cmd_MoveMem(c); break;
            case 0xDB: Cmd_MoveWord(c); break;
            case 0xBC: Cmd_MoveWord(c); break;

            case 0x06: {
                uint32_t raw_addr = c.w1;
                /* STRICT G_DL resolution: real G_DL targets are either
                 * registered in the address map, or inside RDRAM.  Any other
                 * target (e.g. an arbitrary heap page that happens to be
                 * mapped) means the walker has drifted into non-DL memory. */
                void *dl_ptr = bka_lookup_addr_mapping(raw_addr);
                if (!dl_ptr) { dl_ptr = bka_lookup_addr_by_low32(raw_addr); }
                if (!dl_ptr) {
                    uint8_t* tmp = RDP_TranslateAddr(raw_addr);
                    if (tmp) {
                        uintptr_t p  = (uintptr_t)tmp;
                        uintptr_t r0 = (uintptr_t)gN64_RDRAM;
                        uintptr_t r1 = r0 + 0x04000000;
                        if (p >= r0 && p < r1) dl_ptr = tmp;
                    }
                }

                static int debug_gdl_count = 0;
                if (++debug_gdl_count <= 20) {
                    void* map_result = bka_lookup_addr_mapping(raw_addr);
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "G_DL DEBUG: raw=0x%08X map_lookup=%p translate=%p",
                        raw_addr, map_result, dl_ptr);
                    if (dl_ptr && bka_is_mapped(dl_ptr)) {
                        uint8_t* dump = (uint8_t*)dl_ptr;
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "G_DL DL bytes: %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X",
                            dump[0], dump[1], dump[2], dump[3], dump[4], dump[5], dump[6], dump[7],
                            dump[8], dump[9], dump[10], dump[11], dump[12], dump[13], dump[14], dump[15]);
                    } else if (dl_ptr) {
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "G_DL DL ptr %p is not in a mapped region", dl_ptr);
                    }
                }
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "G_DL RECOGNIZED cur=%p w0=0x%08X w1=0x%08X", cur, c.w0, c.w1);
                { static int s_stage1 = 0; if (s_stage1++ < 10) LOGV("G_DL S1 dl_ptr=%p", dl_ptr); }
                static int dl_log_count = 0;
                if (++dl_log_count <= 20) {
                    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                        "G_DL: addr=0x%08X resolved=%p", raw_addr, dl_ptr);
                }
                if (!dl_ptr || !bka_is_mapped(dl_ptr)) {
                    static int s_nomap = 0;
                    if (s_nomap++ < 50) {
                        void* m = bka_lookup_addr_mapping(raw_addr);
                        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                            "G_DL: refusing addr=0x%08X (dl_ptr=%p map_lookup=%p)",
                            raw_addr, dl_ptr, m);
                    }
                    if (++consecutive_bad_gdl > 8) {
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "walker: %d consecutive failed G_DLs — bailing (drift past DL end)",
                            consecutive_bad_gdl);
                        return;
                    }
                    break;
                }
                consecutive_bad_gdl = 0;
                // NOTE: Do not skip lists with zero first words. They are not truly empty;
                // the address resolver may see zeros due to segment mapping.

                // Loop detection: refuse only if the target is currently ON the
                // active stack (a genuine recursion).  Re-entering a DL after its
                // G_ENDDL has popped it is legitimate.
                bool already_on_stack = false;
                for (int i = 0; i < depth; i++) {
                    if (stack[i].ptr && (uintptr_t)stack[i].ptr == (uintptr_t)dl_ptr) {
                        already_on_stack = true;
                        break;
                    }
                }
                if (already_on_stack) {
                    __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                        "G_DL recursion detected at addr=0x%08X, breaking", raw_addr);
                    break;
                }
                { static int s_stage2 = 0; if (s_stage2++ < 10) LOGV("G_DL S2 depth=%d dl_ptr=%p", depth, dl_ptr); }
                if (++gdl_jumps > MAX_GDL_JUMPS) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "walker: %zu G_DL jumps in one task — bailing (DL tree too deep, "
                        "drifted past real content)", gdl_jumps);
                    return;
                }
                static int dl_jump_log_count = 0;
                {
                    static int s_jump_dump = 0;
                    if ((s_jump_dump++ % 40) == 0) {
                        uint8_t* b = (uint8_t*)dl_ptr;
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "G_DL JUMP depth=%d target=0x%08X first32=%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
                            depth, raw_addr,
                            b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],
                            b[8],b[9],b[10],b[11],b[12],b[13],b[14],b[15],
                            b[16],b[17],b[18],b[19],b[20],b[21],b[22],b[23],
                            b[24],b[25],b[26],b[27],b[28],b[29],b[30],b[31]);
                    }
                }
                if (depth == 0) s_seen_gdl_at_depth0 = true;   /* Fix Q */
                s_dl_base = (uintptr_t)dl_ptr;
                /* disabled: { static int s_w = 0; if (s_w++ < 3) { bka_install_watch(); mprotect((void*)((uintptr_t)dl_ptr & ~0xFFFULL), 0x1000, PROT_READ); } } */
                if (++dl_jump_log_count <= 50) {
                    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                        "G_DL JUMP to addr=0x%08X resolved=%p cur_end=%p depth=%d",
                        raw_addr, dl_ptr, cur_end, depth);
                }
                // Diagnostic: dump first 16 bytes at resolved pointer
                if (dl_jump_log_count <= 3) {
                    uint8_t* dump = (uint8_t*)dl_ptr;
                    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                        "DL bytes at %p: %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X",
                        dl_ptr, dump[0], dump[1], dump[2], dump[3], dump[4], dump[5], dump[6], dump[7],
                        dump[8], dump[9], dump[10], dump[11], dump[12], dump[13], dump[14], dump[15]);
                }
                if (depth >= 63) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "G_DL: max depth reached");
                    break;
                }

                // Save the OUTER DL's position/end BEFORE we overwrite cur_end
                // with the nested DL's end.
                stack[depth].ptr = cur;
                stack[depth].end = cur_end;      // outer cur_end preserved
                stack_stride[depth] = current_stride;
                stack_dl_base[depth] = s_dl_base;
                stack_enc[depth] = cur_dl_enc;
                depth++;
                if (depth > g_bka_task_max_depth) g_bka_task_max_depth = depth;
                /* Inherit parent encoding — Banjo's sub-DLs are almost always
                 * same-encoding as their parent.  Resetting to 0 causes
                 * ambiguous-first-command DLs (e.g. a leading G_SETCOMBINE
                 * bytes 'FC 62 FE 04' which decode as valid G_VTX in LE) to be
                 * misdetected as LE, producing phantom seg-1 vertex loads. */
                {
                    uint32_t _w0 = *(uint32_t*)dl_ptr;

                    uint32_t _w4 = *((uint32_t*)dl_ptr + 1);

                    if (_w0 == 0 && _w4 == 0) {

                        static int s_dead = 0;

                        if (s_dead++ < 5) __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",

                            "G_DL SKIP: dead target 0x%08X (first 8 bytes zero)", raw_addr);

                        break;

                    }

                    int probed = bka_probe_dl_encoding((uint8_t*)dl_ptr);
                    int parent_enc = (depth > 0) ? stack_enc[depth - 1] : 0;
                    if (probed != 0) {
                        cur_dl_enc = probed;
                    } else if (parent_enc != 0) {
                        cur_dl_enc = parent_enc;
                    } else {
                        cur_dl_enc = 1;
                    }
                    static int s_enc_probe = 0;
                    if (s_enc_probe++ < 40) {
                        uint8_t* b = (uint8_t*)dl_ptr;
                        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                            "G_DL ENC-PROBE target=0x%08X bytes=%02X%02X%02X%02X chosen=%d parent=%d",
                            raw_addr, b[0],b[1],b[2],b[3], cur_dl_enc, stack_enc[depth - 1]);
                    }
                    {
                        static int s_probe_detail = 0;
                        if (s_probe_detail++ < 60) {
                            uint8_t* b = (uint8_t*)dl_ptr;
                            char hb[3*32 + 4]; int n = 0;
                            for (int k = 0; k < 32; k++)
                                n += snprintf(hb+n, sizeof(hb)-n, " %02X", b[k]);
                            __android_log_print(ANDROID_LOG_ERROR, "BKA-PROBE",
                                "GDL target=0x%08X probed=%d parent=%d chosen=%d bytes%s",
                                raw_addr, probed, parent_enc, cur_dl_enc, hb);
                        }
                    }
                }

                // Now safe to update cur_end for the nested DL.
                // Cap to 16 KB past the entry point — real sub-DLs are
                // bounded and walkers that span megabytes are drifting
                // through unrelated memory.
                {
                    uintptr_t hard_cap = (uintptr_t)dl_ptr + 0x4000;
                    uintptr_t mapped_end = bka_get_mapped_end(dl_ptr);
                    if (mapped_end != 0 && mapped_end < hard_cap &&
                        mapped_end > (uintptr_t)dl_ptr) {
                        cur_end = (uint8_t*)mapped_end;
                    } else {
                        cur_end = (uint8_t*)hard_cap;
                    }
                }

                cur = (uint8_t*)dl_ptr;
                /* Fix L: per-sub-DL stride detection via multi-slot sampler. */
                {
                    const uint8_t* _p = (const uint8_t*)dl_ptr;
                    current_stride = 8;   /* Fix Y2: sub-DL is 8-byte packed, no payload */
                    static int s_jlog = 0;
                    if (s_jlog++ < 40) {
                        __android_log_print(ANDROID_LOG_ERROR, "BKA-STRIDE",
                            "GDL target=0x%08X b8_15=[%08X %08X] b24_31=[%08X %08X] b40_47=[%08X %08X] -> stride=%zu",
                            raw_addr,
                            *(const uint32_t*)(_p+8),  *(const uint32_t*)(_p+12),
                            *(const uint32_t*)(_p+24), *(const uint32_t*)(_p+28),
                            *(const uint32_t*)(_p+40), *(const uint32_t*)(_p+44),
                            current_stride);
                    }
                }
                /* Fix M: refuse targets that don't score as a DL.  Prevents
                 * the walker from entering vertex/palette/pointer tables
                 * that happen to sit behind a G_DL word in the recomp buffer. */
                {
                    int score = bka_looks_like_dl((const uint8_t*)dl_ptr, (int)current_stride);
                    {
                        static int s_scorelog = 0;
                        if (s_scorelog++ < 60) {
                            const uint8_t* _p = (const uint8_t*)dl_ptr;
                            __android_log_print(ANDROID_LOG_ERROR, "BKA-STRIDE",
                                "GDL caller=%p target=0x%08X stride=%zu score=%d/8 first16=%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
                                (void*)cur, raw_addr, current_stride, score,
                                _p[0],_p[1],_p[2],_p[3],_p[4],_p[5],_p[6],_p[7],
                                _p[8],_p[9],_p[10],_p[11],_p[12],_p[13],_p[14],_p[15]);
                        }
                    }
                    if (score < 7) {
                        static int s_refuse = 0;
                        if (s_refuse++ < 30) {
                            const uint8_t* _p = (const uint8_t*)dl_ptr;
                            __android_log_print(ANDROID_LOG_ERROR, "BKA-STRIDE",
                                "GDL target=0x%08X REFUSED as data (score=%d/8) first16=%02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X %02X%02X%02X%02X",
                                raw_addr, score,
                                _p[0],_p[1],_p[2],_p[3],_p[4],_p[5],_p[6],_p[7],
                                _p[8],_p[9],_p[10],_p[11],_p[12],_p[13],_p[14],_p[15]);
                        }
                        if (++consecutive_bad_gdl > 8) {
                            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                                "walker: %d consecutive refused G_DLs -- bailing",
                                consecutive_bad_gdl);
                            return;
                        }
                        break;
                    }
                }
                // Use a safe upper bound based on MAX_DL_CMDS to avoid
                // running off into non-DL data if this nested list lacks ENDDL.
                // Set cur_end to the actual mapped region end, not a huge upper bound.
                uintptr_t nested_end = bka_get_mapped_end(dl_ptr);
                if (nested_end > (uintptr_t)dl_ptr) {
                    cur_end = (uint8_t*)nested_end;
                } else {
                    cur_end = cur + (MAX_DL_CMDS * current_stride);
                }
                dl_cmds = 0;
                zero_run = 0;
                log_after_jump = true;
                jump_log_count = 0;

                break;
            }

            case 0xB8: // F3DEX G_ENDDL - end of display list
                LOGV(
                    "G_ENDDL before pop: depth=%d cur=%p cur_end=%p",
                    depth, cur, cur_end);
                if (depth > 0) {
                    depth--;
                    cur = stack[depth].ptr;
                    cur_end = stack[depth].end;
                    current_stride = stack_stride[depth];
                        s_dl_base = stack_dl_base[depth];
                    cur_dl_enc = stack_enc[depth];
                    dl_cmds = 0;
                    zero_run = 0;
                    LOGV(
                        "G_ENDDL after pop: depth=%d cur=%p cur_end=%p",
                        depth, cur, cur_end);
                } else {
                    /* Top-level ENDDL — this RSP task's DL is finished. */
                    LOGV("G_ENDDL top-level, vertices=%d",
                         s_rdp.dmemVertexCount);
                    return;
                }
                break;

            case 0xDF:
                if (depth > 0) {
                    depth--;
                    cur = stack[depth].ptr;
                    cur_end = stack[depth].end;
                    current_stride = stack_stride[depth];
                        s_dl_base = stack_dl_base[depth];
                    cur_dl_enc = stack_enc[depth];
                    dl_cmds = 0;
                    zero_run = 0;
                } else {
                    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                        "ENDDL top-level, vertices=%d", s_rdp.dmemVertexCount);
                    return;
                }
                break;

            case 0x14:
            case 0x1C:

            case 0x40:
                Cmd_LoadTLUT(c);
                break;

            case 0x4E: // Unknown but appears frequently; treat as no-op for now
                break;

            case 0xA4:
            case 0xB0:
                Cmd_LoadBlock(c);
                break;

            case 0x98:
            case 0xA1:
                Cmd_SetTImg(c);
                break;

            case 0x84:
                Cmd_SetOtherModeL(c);
                break;

            case 0x60:
                Cmd_SetOtherModeH(c);
                break;
case 0xDC:
                Cmd_MoveMem(c);
                break;
            case 0x16: // G_TEXRECTFLIP - textured rectangle flip
            case 0x1D: // G_TEXRECT - textured rectangle
                Cmd_TexRect(c);
                break;
            case 0x30: // G_LOADUCODE - load microcode (no-op for software RDP)
            case 0x39: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x3A: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0x41: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x45: // G_SETTILE - set tile (handled by 0xF5)
            case 0x50: // G_SETSCISSOR - set scissor box (can be no-op)
            case 0x57: // G_SETOTHERMODE_L - set other mode L (handled by 0xE2)
            case 0x63: // G_SETCOMBINE - set combine mode (handled by 0xFC)
            case 0x65: // G_SETOTHERMODE_H - set other mode H (handled by 0xE3)
            case 0x6B: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x71: // G_SETTILE - set tile (handled by 0xF5)
            case 0x72: // G_SETTILE - set tile (handled by 0xF5)
            case 0x7D: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x80: // G_RDPHALF_1 - RDP half command
            case 0x81: // G_RDPHALF_2 - RDP half command
            case 0x8C: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x8D: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0x91: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x95: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x99: // G_SETOTHERMODE_L - set other mode L (handled by 0xE2)
            case 0xA6: // G_LOADTLUT - load texture lookup table (handled by 0x40)
            case 0xA7: // G_SETTILE - set tile (handled by 0xF5)
            case 0xA9: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xAD: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xB2: // G_SETTILE - set tile (handled by 0xF5)
            case 0xB4: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0xC6: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0xC8: // G_SETTILE - set tile (handled by 0xF5)
            case 0xCB: // G_RDPHALF_1 - RDP half command
            case 0xCC: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0xDE: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xF8: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0xF9: // G_SETTILE - set tile (handled by 0xF5)
                break;
            case 0x12: // G_LOADUCODE - load microcode (no-op)
            case 0x20: // G_RDPHALF_1 - RDP half command
            case 0x21: // G_RDPHALF_2 - RDP half command
            case 0x36: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x0A: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xD4: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0xDD: // G_SETTIMG - set texture image (handled by 0xFD)
                break;
            case 0x05: // G_TEXTURE - enable texture
            case 0x11: // G_RDPHALF_1 - RDP half command
            case 0x22: // G_RDPHALF_2 - RDP half command
            case 0x2B: // G_SETTIMG - set texture image
            case 0x3C: // G_SETTILESIZE - set tile size
            case 0x48: // G_SETTIMG - set texture image
            case 0x4B: // G_LOADBLOCK - load texture block
            case 0x4C: // G_SETTILE - set tile
            case 0x54: // G_SETSCISSOR - set scissor box
            case 0x62: // G_SETTILESIZE - set tile size
            case 0x6A: // G_SETTIMG - set texture image
            case 0x6C: // G_SETTILE - set tile
            case 0x73: // G_SETTIMG - set texture image
            case 0x87: // G_LOADBLOCK - load texture block
            case 0x96: // G_SETTILESIZE - set tile size
            case 0x9A: // G_SETTIMG - set texture image
            case 0x9D: // G_SETTILE - set tile
            case 0xAB: // G_SETTIMG - set texture image
            case 0xD0: // G_LOADBLOCK - load texture block
            case 0xEB: // G_SETTIMG - set texture image
                break;
default:
                // Fix E4: +2 (2438 adds 1 -> 3 per unknown)
                unknown_opcode_run += 2;
                break;
        }

        if (cmds_since_progress > 200 && total > 200) {
            // Sub-DLs in Banjo's compiled output frequently omit G_ENDDL.
            // When the walker stops making progress at depth > 0, treat it
            // as an implicit end-of-list: pop back to the parent and keep
            // walking.  Only bail when we are already at the top level —
            // that's true drift.
            if (depth > 0 && g_bka_task_pops < 16) {
                g_bka_task_pops++;
                static int s_implicit_pop = 0;
                if (s_implicit_pop++ < 20) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "walker: implicit end-of-DL at depth=%d cur=%p — popping (pop %d)",
                        depth, (void*)cur, g_bka_task_pops);
                }
                depth--;
                cur = stack[depth].ptr;  // Fix A: was + stack_stride, skipped a command
                cur_end = stack[depth].end;
                current_stride = stack_stride[depth];
                s_dl_base = stack_dl_base[depth];
                cur_dl_enc = stack_enc[depth];
                dl_cmds = 0;
                zero_run = 0;
                cmds_since_progress = 0;
                continue;
            }
            // Either at top level, or too many pops — treat as real drift.
            if (depth > 0 && g_bka_task_pops >= 16) {
                static int s_toomany = 0;
                if (s_toomany++ < 10) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "walker: too many implicit pops (%d) at depth=%d — bailing",
                        g_bka_task_pops, depth);
                }
                return;
            }
            if (s_rspCallCount <= 30 || (s_rspCallCount % 50) == 0) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "TASK-SUMMARY #%d cmds=%zu tris=%d depth=%d end=NOPROG",
                    s_rspCallCount, total, g_bka_task_tri_count, depth);
            }
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "walker: 30 commands with no progress at cur=%p depth=%d total=%zu — bailing (top level)",
                (void*)cur, depth, total);
            g_bka_frame_gen++;
            return;
        }
        if (unknown_opcode_run >= 8) {
            if (s_rspCallCount <= 30 || (s_rspCallCount % 50) == 0) {
                __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                    "TASK-SUMMARY #%d cmds=%zu tris=%d depth=%d end=DRIFT",
                    s_rspCallCount, total, g_bka_task_tri_count, depth);
            }
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "walker: %d consecutive unknown opcodes at cur=%p depth=%d — returning",
                unknown_opcode_run, cur, depth);
            /* Once-only drift diagnosis: dump last 8 accepted commands
             * (ptr, w0, w1, op, enc) plus 32 raw bytes at each. */
            {
                static int s_drift_dump = 0;
                if (s_drift_dump++ < 4) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA-DRIFT",
                        "DRIFT-SUMMARY cur=%p depth=%d dlBase=%p stride=%zu",
                        (void*)cur, depth, (void*)s_dl_base, current_stride);
                    for (int k = 31; k >= 0; k--) {
                        int i = (s_lastcmd_idx - 1 - k) & 31;
                        if (!s_lastcmds[i].ptr) continue;
                        const uint8_t* p = s_lastcmds[i].ptr;
                        __android_log_print(ANDROID_LOG_ERROR, "BKA-DRIFT",
                            "LAST[-%d] ptr=%p depth=%d stride=%zu op=0x%02X enc=%d w0=%08X w1=%08X next8=%02X%02X%02X%02X %02X%02X%02X%02X",
                            k, (void*)p, s_lastcmds[i].depth, s_lastcmds[i].stride,
                            s_lastcmds[i].op, s_lastcmds[i].enc,
                            s_lastcmds[i].w0, s_lastcmds[i].w1,
                            p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7]);
                    }
                    /* Also dump the raw 128 bytes ending at cur */
                    const uint8_t* p = (const uint8_t*)cur;
                    char hb[3*128 + 8]; int n = 0;
                    for (int k = -128; k < 0; k++)
                        n += snprintf(hb+n, sizeof(hb)-n, " %02X", p[k]);
                    __android_log_print(ANDROID_LOG_ERROR, "BKA-DRIFT",
                        "RAW128BACK ending@%p bytes%s", (void*)cur, hb);
                }
            }
            return;
        }
    }
    if (s_rspCallCount <= 30 || (s_rspCallCount % 50) == 0) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "TASK-SUMMARY #%d cmds=%zu tris=%d end=COMPLETE",
            s_rspCallCount, total, g_bka_task_tri_count);
    }
    g_bka_frame_gen++;
    {
        static int s_hist = 0;
        if (s_hist++ == 60) {   // dump once, after 60 tasks
            char buf[512]; int n = 0;
            n += snprintf(buf+n, sizeof(buf)-n, "MTXFLAGS:");
            for (int i = 0; i < 16; i++) {
                if (g_mtx_flag_hist[i])
                    n += snprintf(buf+n, sizeof(buf)-n, " %02X=%d", i, g_mtx_flag_hist[i]);
            }
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX", "%s", buf);
        }
    }
    { static int s_ptask = 0; if (++s_ptask <= 30) {
        char obuf[2048]; int on = 0;
        for (int k = 0; k < 256; k++)
            if (s_opcount[k]) on += snprintf(obuf + on, sizeof(obuf) - on, "%02X:%u ", k, s_opcount[k]);
        __android_log_print(ANDROID_LOG_ERROR, "BKA-OPC", "task#%d %s", s_ptask, obuf);
        memset(s_opcount, 0, sizeof(s_opcount));
        s_op_total = 0;
    } }
}


// force rebuild: vertex preservation
// force rebuild stride16 no bswap
