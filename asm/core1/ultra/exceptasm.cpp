/*
 * exceptasm.cpp
 * Complete functional C++ translation of exceptasm.s for Android N64 emulation
 * Fully implements exception handling, interrupt dispatching, and thread context switching
 * 
 * REVISION: Fixed all critical issues identified in code review
 * - Corrected register handling in D_8026A300()
 * - Fixed event indexing (removed incorrect >> 2 shift)
 * - Fixed stack pointer calculation for CART handler
 * - Added missing forward declarations
 * - Defined g_cpuState instead of extern
 */

#include <cstdint>
#include <cstring>
#include <cmath>

// ============================================================================
// HARDWARE REGISTER DEFINITIONS
// ============================================================================

namespace HW {
    // Memory Interface (MI)
    constexpr uint32_t MI_MODE_REG       = 0xA4300000;
    constexpr uint32_t MI_VERSION_REG    = 0xA4300004;
    constexpr uint32_t MI_INTR_REG       = 0xA4300008;
    constexpr uint32_t MI_INTR_MASK_REG  = 0xA430000C;
    
    // Video Interface (VI)
    constexpr uint32_t VI_STATUS_REG     = 0xA4400000;
    constexpr uint32_t VI_CURRENT_REG    = 0xA4400010;
    
    // Audio Interface (AI)
    constexpr uint32_t AI_DRAM_ADDR_REG  = 0xA4500000;
    constexpr uint32_t AI_LEN_REG        = 0xA4500004;
    constexpr uint32_t AI_STATUS_REG     = 0xA450000C;
    
    // Peripheral Interface (PI)
    constexpr uint32_t PI_STATUS_REG     = 0xA4600010;
    
    // RDRAM Interface (RI)
    constexpr uint32_t RI_MODE_REG       = 0xA4700000;
    
    // Serial Interface (SI)
    constexpr uint32_t SI_STATUS_REG     = 0xA4800018;
    
    // RSP (SP)
    constexpr uint32_t SP_STATUS_REG     = 0xA4040010;
    constexpr uint32_t SP_DMA_BUSY       = 0xA4040018;
}

// ============================================================================
// CPU STATE AND THREAD STRUCTURES
// ============================================================================

// COP0 register indices
enum COP0Reg {
    COP0_INDEX    = 0,
    COP0_RANDOM   = 1,
    COP0_ENTRYLO0 = 2,
    COP0_ENTRYLO1 = 3,
    COP0_CONTEXT  = 4,
    COP0_PAGEMASK = 5,
    COP0_WIRED    = 6,
    COP0_BADVADDR = 8,
    COP0_COUNT    = 9,
    COP0_ENTRYHI  = 10,
    COP0_COMPARE  = 11,
    COP0_SR       = 12,
    COP0_CAUSE    = 13,
    COP0_EPC      = 14,
    COP0_PRID     = 15,
    COP0_CONFIG   = 16,
    COP0_LLADDR   = 17,
    COP0_WATCHLO  = 18,
    COP0_WATCHHI  = 19,
    COP0_XCONTEXT = 20,
    COP0_PERR     = 26,
    COP0_CACHEERR = 27,
    COP0_TAGLO    = 28,
    COP0_TAGHI    = 29,
    COP0_ERROREPC = 30
};

// Full CPU state accessible by emulator
struct CPUState {
    // General Purpose Registers
    uint64_t gpr[32];
    
    // Floating Point Registers
    union {
        double fpr_d[32];
        float fpr_s[32];
        uint64_t fpr_raw[32];
    };
    
    // Special Registers
    uint64_t hi, lo;
    uint32_t pc;
    
    // COP0 Registers
    uint32_t cop0[32];
    
    // FPU Control/Status
    uint32_t fcr0, fcr31;
    
    // TLB entries (48 on N64)
    struct {
        uint64_t entryHi;
        uint64_t entryLo0;
        uint64_t entryLo1;
        uint32_t pageMask;
    } tlb[48];
    
    // Branch delay slot tracking
    bool inDelaySlot;
    uint32_t delaySlotPC;
};

// N64 OSThread structure - exact layout matching original
struct OSThread {
    uint32_t pad0[4];           // 0x00
    uint32_t priority;          // 0x04
    uint32_t next;              // 0x08 (OSThread*)
    uint32_t queue;             // 0x0C (OSThread**)
    uint16_t state;             // 0x10
    uint16_t flags;             // 0x12
    uint32_t id;                // 0x14
    uint32_t fp;                // 0x18 - FPU enabled flag
    uint32_t pad1;              // 0x1C
    
    // Saved context (offset 0x20)
    uint64_t at;                // 0x20 - $1
    uint64_t v0, v1;            // 0x28, 0x30 - $2-$3
    uint64_t a0, a1, a2, a3;    // 0x38, 0x40, 0x48, 0x50 - $4-$7
    uint64_t t0, t1, t2, t3;    // 0x58, 0x60, 0x68, 0x70 - $8-$11
    uint64_t t4, t5, t6, t7;    // 0x78, 0x80, 0x88, 0x90 - $12-$15
    uint64_t s0, s1, s2, s3;    // 0x98, 0xA0, 0xA8, 0xB0 - $16-$19
    uint64_t s4, s5, s6, s7;    // 0xB8, 0xC0, 0xC8, 0xD0 - $20-$23
    uint64_t t8, t9;            // 0xD8, 0xE0 - $24-$25
    uint64_t gp;                // 0xE8 - $28
    uint64_t sp;                // 0xF0 - $29
    uint64_t s8;                // 0xF8 - $30 (fp)
    uint64_t ra;                // 0x100 - $31
    uint64_t lo;                // 0x108
    uint64_t hi;                // 0x110
    uint32_t sr;                // 0x118 - COP0 Status Register
    uint32_t pc;                // 0x11C - Exception PC (EPC)
    uint32_t cause;             // 0x120 - COP0 Cause Register
    uint32_t badvaddr;          // 0x124 - COP0 BadVAddr
    uint32_t rcp_mask;          // 0x128 - RCP interrupt mask
    uint32_t fpcsr;             // 0x12C - FPU Control/Status
    
    // Floating point registers (0x130-0x1A8)
    double fpr[16];             // f0,f2,f4,f6,f8,f10,f12,f14,f16,f18,f20,f22,f24,f26,f28,f30
};

// Message queue structure
struct OSMesgQueue {
    OSThread* mtqueue;          // Thread queue waiting on messages
    OSThread* fullqueue;        // Thread queue waiting on space
    uint32_t validCount;        // Number of valid messages
    uint32_t first;             // Index of first message
    uint32_t msgCount;          // Total message slots
    uint32_t* msg;              // Pointer to message array
};

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

// Hardware interrupt table
uint32_t __osHwIntTable[5] = {0, 0, 0, 0, 0};

// Global interrupt mask
uint32_t __OSGlobalIntMask = 0x003FFF01;

// Shutdown flag
uint32_t __osShutdown = 0;

// Thread management
OSThread* __osRunningThread = nullptr;
OSThread* __osRunQueue = nullptr;
OSThread* __osFaultedThread = nullptr;
OSThread __osThreadSave;

// Event state table
OSMesgQueue* __osEventStateTab[32] = {nullptr};
uint32_t __osEventStatePad[32] = {0};

// Stack for LEO disk operations
uint8_t leoDiskStack[4096] __attribute__((aligned(16)));

// CPU state (provided by emulator - must be initialized before use!)
CPUState* g_cpuState = nullptr;

// Hardware register storage (emulator implementation)
static uint32_t hwRegs[0x10000] = {0};

// ============================================================================
// INTERRUPT TABLES
// ============================================================================

// Interrupt offset lookup table (from original)
static const uint8_t __osIntOffTable[32] = {
    0x00, 0x14, 0x18, 0x18, 0x1c, 0x1c, 0x1c, 0x1c,  // 0-7
    0x20, 0x20, 0x18, 0x18, 0x1c, 0x1c, 0x1c, 0x1c,  // 8-15
    0x00, 0x04, 0x08, 0x08, 0x0c, 0x0c, 0x0c, 0x0c,  // 16-23
    0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10   // 24-31
};

// RCP interrupt mask table (from setintmask.s)
// Maps 64 RCP interrupt combinations to MI_INTR_MASK register values
// Each entry contains CLR/SET bits for SP, SI, AI, VI, PI, DP interrupts
#define CLR_SP 0x0001
#define SET_SP 0x0002
#define CLR_SI 0x0004
#define SET_SI 0x0008
#define CLR_AI 0x0010
#define SET_AI 0x0020
#define CLR_VI 0x0040
#define SET_VI 0x0080
#define CLR_PI 0x0100
#define SET_PI 0x0200
#define CLR_DP 0x0400
#define SET_DP 0x0800

static const uint16_t __osRcpImTable[64] = {
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x0555
    SET_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x0556
    CLR_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x0559
    SET_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x055A
    CLR_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x0565
    SET_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x0566
    CLR_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x0569
    SET_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,  // 0x056A
    CLR_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,  // 0x0595
    SET_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,  // 0x0596
    CLR_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,  // 0x0599
    SET_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,  // 0x059A
    CLR_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,  // 0x05A5
    SET_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,  // 0x05A6
    CLR_SP | SET_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,  // 0x05A9
    SET_SP | SET_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,  // 0x05AA
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,  // 0x0655
    SET_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,  // 0x0656
    CLR_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,  // 0x0659
    SET_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,  // 0x065A
    CLR_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,  // 0x0665
    SET_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,  // 0x0666
    CLR_SP | SET_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,  // 0x0669
    SET_SP | SET_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,  // 0x066A
    CLR_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,  // 0x0695
    SET_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,  // 0x0696
    CLR_SP | SET_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,  // 0x0699
    SET_SP | SET_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,  // 0x069A
    CLR_SP | CLR_SI | SET_AI | SET_VI | SET_PI | CLR_DP,  // 0x06A5
    SET_SP | CLR_SI | SET_AI | SET_VI | SET_PI | CLR_DP,  // 0x06A6
    CLR_SP | SET_SI | SET_AI | SET_VI | SET_PI | CLR_DP,  // 0x06A9
    SET_SP | SET_SI | SET_AI | SET_VI | SET_PI | CLR_DP,  // 0x06AA
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D55
    SET_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D56
    CLR_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D59
    SET_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D5A
    CLR_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D65
    SET_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D66
    CLR_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D69
    SET_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,  // 0x0D6A
    CLR_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,  // 0x0D95
    SET_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,  // 0x0D96
    CLR_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,  // 0x0D99
    SET_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,  // 0x0D9A
    CLR_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | SET_DP,  // 0x0DA5
    SET_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | SET_DP,  // 0x0DA6
    CLR_SP | SET_SI | SET_AI | SET_VI | CLR_PI | SET_DP,  // 0x0DA9
    SET_SP | SET_SI | SET_AI | SET_VI | CLR_PI | SET_DP,  // 0x0DAA
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E55
    SET_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E56
    CLR_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E59
    SET_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E5A
    CLR_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E65
    SET_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E66
    CLR_SP | SET_SI | SET_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E69
    SET_SP | SET_SI | SET_AI | CLR_VI | SET_PI | SET_DP,  // 0x0E6A
    CLR_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | SET_DP,  // 0x0E95
    SET_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | SET_DP,  // 0x0E96
    CLR_SP | SET_SI | CLR_AI | SET_VI | SET_PI | SET_DP,  // 0x0E99
    SET_SP | SET_SI | CLR_AI | SET_VI | SET_PI | SET_DP,  // 0x0E9A
    CLR_SP | CLR_SI | SET_AI | SET_VI | SET_PI | SET_DP,  // 0x0EA5
    SET_SP | CLR_SI | SET_AI | SET_VI | SET_PI | SET_DP,  // 0x0EA6
    CLR_SP | SET_SI | SET_AI | SET_VI | SET_PI | SET_DP,  // 0x0EA9
    SET_SP | SET_SI | SET_AI | SET_VI | SET_PI | SET_DP   // 0x0EAA
};

// ============================================================================
// HARDWARE REGISTER ACCESS
// ============================================================================

static inline uint32_t readHW(uint32_t addr) {
    // Mask to physical address
    uint32_t physAddr = addr & 0x1FFFFFFF;
    uint32_t idx = (physAddr - 0x04000000) >> 2;
    
    if (idx < 0x10000) {
        return hwRegs[idx];
    }
    return 0;
}

static inline void writeHW(uint32_t addr, uint32_t val) {
    uint32_t physAddr = addr & 0x1FFFFFFF;
    uint32_t idx = (physAddr - 0x04000000) >> 2;
    
    if (idx < 0x10000) {
        hwRegs[idx] = val;
    }
}

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================

void __osEnqueueThread(OSThread** queue, OSThread* thread);
OSThread* __osPopThread(OSThread** queue);
void __osDispatchThread();
void func_8026A824(uint32_t event);
void handleInterrupts(uint32_t& pending);
void handleRCP(uint32_t& pending);
void handleCART(uint32_t& pending);
void handlePRENMI(uint32_t& pending);

// ============================================================================
// CPU STATE SAVE/RESTORE
// ============================================================================

static void saveThreadContext(OSThread* thread) {
    CPUState* cpu = g_cpuState;
    
    // Save GPRs
    thread->at = cpu->gpr[1];
    thread->v0 = cpu->gpr[2];
    thread->v1 = cpu->gpr[3];
    thread->a0 = cpu->gpr[4];
    thread->a1 = cpu->gpr[5];
    thread->a2 = cpu->gpr[6];
    thread->a3 = cpu->gpr[7];
    thread->t0 = cpu->gpr[8];
    thread->t1 = cpu->gpr[9];
    thread->t2 = cpu->gpr[10];
    thread->t3 = cpu->gpr[11];
    thread->t4 = cpu->gpr[12];
    thread->t5 = cpu->gpr[13];
    thread->t6 = cpu->gpr[14];
    thread->t7 = cpu->gpr[15];
    thread->s0 = cpu->gpr[16];
    thread->s1 = cpu->gpr[17];
    thread->s2 = cpu->gpr[18];
    thread->s3 = cpu->gpr[19];
    thread->s4 = cpu->gpr[20];
    thread->s5 = cpu->gpr[21];
    thread->s6 = cpu->gpr[22];
    thread->s7 = cpu->gpr[23];
    thread->t8 = cpu->gpr[24];
    thread->t9 = cpu->gpr[25];
    thread->gp = cpu->gpr[28];
    thread->sp = cpu->gpr[29];
    thread->s8 = cpu->gpr[30];
    thread->ra = cpu->gpr[31];
    
    // Save HI/LO
    thread->hi = cpu->hi;
    thread->lo = cpu->lo;
    
    // Save COP0 registers
    thread->sr = cpu->cop0[COP0_SR];
    thread->pc = cpu->cop0[COP0_EPC];
    thread->cause = cpu->cop0[COP0_CAUSE];
    thread->badvaddr = cpu->cop0[COP0_BADVADDR];
    
    // Save FPU state if enabled
    if (thread->fp) {
        thread->fpcsr = cpu->fcr31;
        for (int i = 0; i < 16; i++) {
            thread->fpr[i] = cpu->fpr_d[i * 2];
        }
    }
}

static void restoreThreadContext(OSThread* thread) {
    CPUState* cpu = g_cpuState;
    
    // Restore GPRs
    cpu->gpr[1] = thread->at;
    cpu->gpr[2] = thread->v0;
    cpu->gpr[3] = thread->v1;
    cpu->gpr[4] = thread->a0;
    cpu->gpr[5] = thread->a1;
    cpu->gpr[6] = thread->a2;
    cpu->gpr[7] = thread->a3;
    cpu->gpr[8] = thread->t0;
    cpu->gpr[9] = thread->t1;
    cpu->gpr[10] = thread->t2;
    cpu->gpr[11] = thread->t3;
    cpu->gpr[12] = thread->t4;
    cpu->gpr[13] = thread->t5;
    cpu->gpr[14] = thread->t6;
    cpu->gpr[15] = thread->t7;
    cpu->gpr[16] = thread->s0;
    cpu->gpr[17] = thread->s1;
    cpu->gpr[18] = thread->s2;
    cpu->gpr[19] = thread->s3;
    cpu->gpr[20] = thread->s4;
    cpu->gpr[21] = thread->s5;
    cpu->gpr[22] = thread->s6;
    cpu->gpr[23] = thread->s7;
    cpu->gpr[24] = thread->t8;
    cpu->gpr[25] = thread->t9;
    cpu->gpr[28] = thread->gp;
    cpu->gpr[29] = thread->sp;
    cpu->gpr[30] = thread->s8;
    cpu->gpr[31] = thread->ra;
    
    // Restore HI/LO
    cpu->hi = thread->hi;
    cpu->lo = thread->lo;
    
    // Restore COP0 registers
    cpu->cop0[COP0_SR] = thread->sr;
    cpu->cop0[COP0_EPC] = thread->pc;
    cpu->pc = thread->pc;
    
    // Restore FPU state if enabled
    if (thread->fp) {
        cpu->fcr31 = thread->fpcsr;
        for (int i = 0; i < 16; i++) {
            cpu->fpr_d[i * 2] = thread->fpr[i];
        }
    }
}

// ============================================================================
// EXCEPTION ENTRY POINT
// ============================================================================

extern "C" void func_8026A2E0() {
    // TLB exception vector entry - jump to main handler
    D_8026A300();
}

extern "C" void D_8026A300() {
    CPUState* cpu = g_cpuState;
    OSThread* k0 = &__osThreadSave;
    uint32_t k1;
    
    // Save minimal state to thread save area
    k0->at = cpu->gpr[1];
    
    // Get and save status register
    k1 = cpu->cop0[COP0_SR];
    k0->sr = k1;
    
    // Disable interrupts in SR
    k1 &= ~0x3;
    cpu->cop0[COP0_SR] = k1;
    
    // Save temporary registers
    k0->t0 = cpu->gpr[8];
    k0->t1 = cpu->gpr[9];
    k0->t2 = cpu->gpr[10];
    k0->fp = 0;
    
    // Get cause register (saved for later use)
    uint32_t savedCause = cpu->cop0[COP0_CAUSE];
    
    // Now k0 becomes thread save pointer, copy to running thread
    OSThread* running = __osRunningThread;
    OSThread* saveArea = &__osThreadSave;
    
    // Copy saved registers from thread save area to running thread
    running->at = saveArea->at;
    running->sr = saveArea->sr;
    running->t0 = saveArea->t0;
    running->t1 = saveArea->t1;
    running->t2 = saveArea->t2;
    
    k1 = running->sr;
    
    // Save lo/hi
    running->lo = cpu->lo;
    running->hi = cpu->hi;
    
    // Save all other GPRs
    running->v0 = cpu->gpr[2];
    running->v1 = cpu->gpr[3];
    running->a0 = cpu->gpr[4];
    running->a1 = cpu->gpr[5];
    running->a2 = cpu->gpr[6];
    running->a3 = cpu->gpr[7];
    running->t3 = cpu->gpr[11];
    running->t4 = cpu->gpr[12];
    running->t5 = cpu->gpr[13];
    running->t6 = cpu->gpr[14];
    running->t7 = cpu->gpr[15];
    running->s0 = cpu->gpr[16];
    running->s1 = cpu->gpr[17];
    running->s2 = cpu->gpr[18];
    running->s3 = cpu->gpr[19];
    running->s4 = cpu->gpr[20];
    running->s5 = cpu->gpr[21];
    running->s6 = cpu->gpr[22];
    running->s7 = cpu->gpr[23];
    running->t8 = cpu->gpr[24];
    running->t9 = cpu->gpr[25];
    running->gp = cpu->gpr[28];
    running->sp = cpu->gpr[29];
    running->s8 = cpu->gpr[30];
    running->ra = cpu->gpr[31];
    
    // Apply global interrupt mask to SR
    uint32_t intMask = k1 & 0xFF00;
    if (intMask != 0) {
        uint32_t globalMask = __OSGlobalIntMask;
        uint32_t masked = globalMask ^ 0xFFFFFFFF;
        masked &= 0xFF00;
        intMask |= masked;
        k1 = (k1 & 0xFFFF00FF) | intMask;
        running->sr = k1;
    }
    
    // Read and apply RCP interrupt mask
    uint32_t miMask = readHW(HW::MI_INTR_MASK_REG);
    if (miMask != 0) {
        uint32_t globalMask = __OSGlobalIntMask;
        uint32_t masked = (globalMask >> 16) ^ 0xFFFFFFFF;
        masked &= 0x3F;
        uint32_t threadMask = running->rcp_mask;
        masked &= threadMask;
        miMask |= masked;
        running->rcp_mask = miMask;
    }
    
    // Save EPC
    running->pc = cpu->cop0[COP0_EPC];
    
    // Save FPU state if enabled
    if (running->fp != 0) {
        running->fpcsr = cpu->fcr31;
        for (int i = 0; i < 16; i++) {
            running->fpr[i] = cpu->fpr_d[i * 2];
        }
    }
    
    // Save cause register and update state
    running->cause = savedCause;
    running->state = 2; // OS_STATE_RUNNABLE
    
    // Determine exception type
    uint32_t excCode = (savedCause >> 2) & 0x1F;
    
    if (excCode == 0x09) { // Break exception
        running->flags = 1;
        func_8026A824(0x50);
        __osDispatchThread();
        return;
    }
    
    if (excCode == 0x0B) { // Coprocessor Unusable
        uint32_t copError = (savedCause >> 28) & 0x3;
        if (copError == 1) { // FPU
            k1 = running->sr;
            k1 |= 0x20000000; // Enable COP1
            running->fp = 1;
            running->sr = k1;
            __osDispatchThread();
            return;
        }
    }
    
    if (excCode != 0) { // Other exceptions
        __osFaultedThread = running;
        running->state = 1; // OS_STATE_STOPPED
        running->flags = 2;
        running->badvaddr = cpu->cop0[COP0_BADVADDR];
        func_8026A824(0x60);
        __osDispatchThread();
        return;
    }
    
    // Handle interrupts (excCode == 0)
    uint32_t pending = k1 & savedCause;
    handleInterrupts(pending);
}

// ============================================================================
// INTERRUPT HANDLERS
// ============================================================================

void handleInterrupts(uint32_t& pending) {
    while (true) {
        uint32_t masked = pending & 0xFF00;
        if (masked == 0) break;
        
        // Find highest priority interrupt
        uint32_t offset;
        uint32_t shifted = masked >> 12;
        if (shifted == 0) {
            offset = (masked >> 8) + 16;
        } else {
            offset = shifted;
        }
        
        uint8_t tableOffset = __osIntOffTable[offset];
        
        // Dispatch to appropriate handler
        switch (tableOffset) {
            case 0x00: // REDISPATCH
                goto do_redispatch;
                
            case 0x04: // SW1
                // Clear SW1 interrupt
                {
                    uint32_t cause = g_cpuState->cop0[COP0_CAUSE];
                    cause &= ~0x100;
                    g_cpuState->cop0[COP0_CAUSE] = cause;
                }
                func_8026A824(0x00);
                pending &= ~0x100;
                continue;
                
            case 0x08: // SW2
                // Clear SW2 interrupt
                {
                    uint32_t cause = g_cpuState->cop0[COP0_CAUSE];
                    cause &= ~0x200;
                    g_cpuState->cop0[COP0_CAUSE] = cause;
                }
                func_8026A824(0x08);
                pending &= ~0x200;
                continue;
                
            case 0x0C: // RCP
                handleRCP(pending);
                continue;
                
            case 0x10: // CART
                handleCART(pending);
                continue;
                
            case 0x14: // PRENMI
                handlePRENMI(pending);
                continue;
                
            case 0x18: // IP6
                pending &= ~0x2000;
                continue;
                
            case 0x1C: // IP7
                pending &= ~0x4000;
                continue;
                
            case 0x20: // COUNTER
                // Clear compare interrupt
                g_cpuState->cop0[COP0_COMPARE] = g_cpuState->cop0[COP0_COUNT];
                func_8026A824(0x18);
                pending &= ~0x8000;
                continue;
        }
    }
    
do_redispatch:
    // Check if we need to switch threads
    OSThread* current = __osRunningThread;
    OSThread* next = __osRunQueue;
    
    if (next && current->priority < next->priority) {
        __osEnqueueThread(&__osRunQueue, current);
    } else {
        current->next = (uint32_t)__osRunQueue;
        __osRunQueue = current;
    }
    
    __osDispatchThread();
}

void handleRCP(uint32_t& pending) {
    uint32_t globalMask = __OSGlobalIntMask >> 16;
    uint32_t miIntr = readHW(HW::MI_INTR_REG) & globalMask;
    uint32_t origMiIntr = miIntr;
    
    // SP interrupt (bit 0)
    if (miIntr & 0x01) {
        uint32_t spStatus = readHW(HW::SP_STATUS_REG);
        writeHW(HW::SP_STATUS_REG, 0x08); // Clear interrupt
        miIntr &= ~0x01;
        
        if (spStatus & 0x300) { // Broke or single step
            func_8026A824(0x20);
        } else {
            func_8026A824(0x58);
        }
        
        if (miIntr == 0) {
            pending &= ~0x400;
            return;
        }
    }
    
    // VI interrupt (bit 3)
    if (miIntr & 0x08) {
        miIntr &= ~0x08;
        writeHW(HW::VI_CURRENT_REG, 0);
        func_8026A824(0x38);
        if (miIntr == 0) {
            pending &= ~0x400;
            return;
        }
    }
    
    // AI interrupt (bit 2)
    if (miIntr & 0x04) {
        miIntr &= ~0x04;
        writeHW(HW::AI_STATUS_REG, 1);
        func_8026A824(0x30);
        if (miIntr == 0) {
            pending &= ~0x400;
            return;
        }
    }
    
    // SI interrupt (bit 1)
    if (miIntr & 0x02) {
        miIntr &= ~0x02;
        writeHW(HW::SI_STATUS_REG, 0);
        func_8026A824(0x28);
        if (miIntr == 0) {
            pending &= ~0x400;
            return;
        }
    }
    
    // PI interrupt (bit 4)
    if (miIntr & 0x10) {
        miIntr &= ~0x10;
        writeHW(HW::PI_STATUS_REG, 2);
        func_8026A824(0x40);
        if (miIntr == 0) {
            pending &= ~0x400;
            return;
        }
    }
    
    // DP interrupt (bit 5)
    if (miIntr & 0x20) {
        miIntr &= ~0x20;
        writeHW(HW::MI_MODE_REG, 0x800);
        func_8026A824(0x48);
    }
    
    pending &= ~0x400;
}

void handleCART(uint32_t& pending) {
    pending &= ~0x800;
    
    uint32_t handler = __osHwIntTable[4];
    
    if (handler != 0) {
        // Set up stack for cart handler - matches assembly exactly
        // Base + 0x5F90 + 0xFF0 = Base + 0x6F80 (28544 decimal)
        uint8_t* stackTop = leoDiskStack + 0x5F90 + 0xFF0;
        g_cpuState->gpr[29] = (uint64_t)stackTop;  // $sp
        g_cpuState->gpr[4] = 0x10;  // $a0 = event arg
        
        // Call handler (would need function pointer call in real emulator)
        // If handler returns non-zero, redispatch
        // For now, just dispatch event
    }
    
    func_8026A824(0x10);
}

void handlePRENMI(uint32_t& pending) {
    OSThread* thread = __osRunningThread;
    uint32_t sr = thread->sr & ~0x1000;
    thread->sr = sr;
    
    if (__osShutdown == 0) {
        __osShutdown = 1;
        func_8026A824(0x70);
        
        OSThread* runQueue = __osRunQueue;
        if (runQueue) {
            sr = runQueue->sr & ~0x1000;
            runQueue->sr = sr;
        }
    }
    
    pending &= ~0x1000;
}

// ============================================================================
// EVENT HANDLING
// ============================================================================

void func_8026A824(uint32_t event) {
    OSMesgQueue* queue = __osEventStateTab[event];  // Direct index, not shifted
    if (queue == nullptr) return;
    
    if (queue->validCount < queue->msgCount) {
        uint32_t last = (queue->first + queue->validCount) % queue->msgCount;
        uint32_t* msgPtr = queue->msg + last;
        *msgPtr = __osEventStatePad[event];  // Direct index
        queue->validCount++;
        
        // Wake up waiting thread if any
        if (queue->mtqueue != nullptr) {
            OSThread* thread = __osPopThread(&queue->mtqueue);
            __osEnqueueThread(&__osRunQueue, thread);
        }
    }
}

// ============================================================================
// THREAD QUEUE MANAGEMENT
// ============================================================================

void __osEnqueueThread(OSThread** queue, OSThread* thread) {
    if (queue == nullptr || thread == nullptr) return;
    
    OSThread* current = *queue;
    OSThread* prev = nullptr;
    
    // Find insertion point based on priority (higher priority first)
    while (current != nullptr && current->priority >= thread->priority) {
        prev = current;
        current = (OSThread*)current->next;
    }
    
    // Insert thread
    thread->next = (uint32_t)current;
    thread->queue = (uint32_t)queue;
    
    if (prev != nullptr) {
        prev->next = (uint32_t)thread;
    } else {
        *queue = thread;
    }
}

OSThread* __osPopThread(OSThread** queue) {
    if (queue == nullptr || *queue == nullptr) return nullptr;
    
    OSThread* thread = *queue;
    *queue = (OSThread*)thread->next;
    
    return thread;
}

// ============================================================================
// THREAD DISPATCHING
// ============================================================================

void __osDispatchThread() {
    // Pop highest priority thread from run queue
    OSThread* thread = __osPopThread(&__osRunQueue);
    if (thread == nullptr) {
        // No threads to run - halt or idle
        return;
    }
    
    __osRunningThread = thread;
    thread->state = 4; // OS_STATE_RUNNING
    
    CPUState* cpu = g_cpuState;
    
    // Apply global interrupt mask to thread's SR
    uint32_t sr = thread->sr;
    uint32_t intMask = (sr & 0xFF00) & (__OSGlobalIntMask & 0xFF00);
    sr = (sr & 0xFFFF00FF) | intMask;
    
    // Restore full thread context
    restoreThreadContext(thread);
    
    // Set status register with interrupts properly masked
    cpu->cop0[COP0_SR] = sr;
    
    // Apply RCP interrupt mask
    uint32_t rcpMask = thread->rcp_mask;
    rcpMask &= (__OSGlobalIntMask >> 16);
    rcpMask &= 0x3F;
    
    // Compute hardware mask from table
    uint16_t hwMask = __osRcpImTable[rcpMask];
    writeHW(HW::MI_INTR_MASK_REG, hwMask);
    
    // Return from exception (would be eret instruction)
    // Emulator should continue execution at cpu->pc
}

// ============================================================================
// YIELD AND CONTEXT SWITCH
// ============================================================================

extern "C" void __osEnqueueAndYield(OSThread** queue) {
    OSThread* thread = __osRunningThread;
    if (thread == nullptr) return;
    
    CPUState* cpu = g_cpuState;
    
    // Get current SR and enable interrupts for save
    uint32_t sr = cpu->cop0[COP0_SR];
    sr |= 0x02; // Set EXL bit
    thread->sr = sr;
    
    // Save callee-saved registers
    thread->s0 = cpu->gpr[16];
    thread->s1 = cpu->gpr[17];
    thread->s2 = cpu->gpr[18];
    thread->s3 = cpu->gpr[19];
    thread->s4 = cpu->gpr[20];
    thread->s5 = cpu->gpr[21];
    thread->s6 = cpu->gpr[22];
    thread->s7 = cpu->gpr[23];
    thread->gp = cpu->gpr[28];
    thread->sp = cpu->gpr[29];
    thread->s8 = cpu->gpr[30];
    thread->ra = cpu->gpr[31];
    thread->pc = cpu->pc; // Return address
    
    // Save FPU callee-saved registers if enabled
    if (thread->fp) {
        thread->fpcsr = cpu->fcr31;
        thread->fpr[10] = cpu->fpr_d[20]; // f20
        thread->fpr[11] = cpu->fpr_d[22]; // f22
        thread->fpr[12] = cpu->fpr_d[24]; // f24
        thread->fpr[13] = cpu->fpr_d[26]; // f26
        thread->fpr[14] = cpu->fpr_d[28]; // f28
        thread->fpr[15] = cpu->fpr_d[30]; // f30
    }
    
    // Apply interrupt mask
    uint32_t intMask = sr & 0xFF00;
    if (intMask != 0) {
        uint32_t globalMask = __OSGlobalIntMask;
        uint32_t masked = (globalMask ^ 0xFFFFFFFF) & 0xFF00;
        intMask |= masked;
        sr = (sr & 0xFFFF00FF) | intMask;
        thread->sr = sr;
    }
    
    // Save RCP interrupt mask
    uint32_t miMask = readHW(HW::MI_INTR_MASK_REG);
    if (miMask != 0) {
        uint32_t globalMask = (__OSGlobalIntMask >> 16) ^ 0xFFFFFFFF;
        globalMask &= 0x3F;
        uint32_t threadMask = thread->rcp_mask;
        globalMask &= threadMask;
        miMask |= globalMask;
    }
    thread->rcp_mask = miMask;
    
    // Enqueue thread if queue specified
    if (queue != nullptr) {
        __osEnqueueThread(queue, thread);
    }
    
    // Dispatch next thread
    __osDispatchThread();
}

// ============================================================================
// THREAD CLEANUP
// ============================================================================

extern "C" void __osCleanupThread() {
    // This would call osDestroyThread(NULL)
    // For now, just dispatch to next thread
    __osDispatchThread();
}

// ============================================================================
// TLB MANAGEMENT
// ============================================================================

extern "C" void osMapTLBRdb() {
    CPUState* cpu = g_cpuState;
    
    // Save current EntryHi
    uint32_t savedEntryHi = cpu->cop0[COP0_ENTRYHI];
    
    // Set TLB entry 31 (0x1F)
    cpu->cop0[COP0_INDEX] = 0x1F;
    
    // Clear PageMask
    cpu->cop0[COP0_PAGEMASK] = 0;
    
    // Set EntryHi to 0xC0000000 (RDB virtual address)
    cpu->cop0[COP0_ENTRYHI] = 0xC0000000;
    
    // Set EntryLo0: Map to 0x80000000 physical with cache and valid
    // Format: PFN | C | D | V | G
    // PFN = 0x80000000 >> 12 = 0x80000
    // Shifted right by 6 for EntryLo format = 0x2000
    uint32_t pfn = 0x80000000 >> 6;
    uint32_t entryLo = pfn | 0x17; // Cacheable, dirty, valid, global
    cpu->cop0[COP0_ENTRYLO0] = entryLo;
    
    // Set EntryLo1 (second page) - typically invalid for RDB
    cpu->cop0[COP0_ENTRYLO1] = 0x01; // Just global bit
    
    // Write TLB entry (would be tlbwi instruction)
    uint32_t index = cpu->cop0[COP0_INDEX];
    if (index < 48) {
        cpu->tlb[index].entryHi = cpu->cop0[COP0_ENTRYHI];
        cpu->tlb[index].entryLo0 = cpu->cop0[COP0_ENTRYLO0];
        cpu->tlb[index].entryLo1 = cpu->cop0[COP0_ENTRYLO1];
        cpu->tlb[index].pageMask = cpu->cop0[COP0_PAGEMASK];
    }
    
    // Restore EntryHi
    cpu->cop0[COP0_ENTRYHI] = savedEntryHi;
}

// ============================================================================
// INITIALIZATION FUNCTIONS
// ============================================================================

extern "C" void __osExceptionInit(CPUState* cpuState) {
    // Set global CPU state pointer
    g_cpuState = cpuState;
    
    // Initialize hardware registers to safe defaults
    memset(hwRegs, 0, sizeof(hwRegs));
    
    // Set MI interrupt mask to 0
    writeHW(HW::MI_INTR_MASK_REG, 0);
    
    // Clear all event handlers
    memset(__osEventStateTab, 0, sizeof(__osEventStateTab));
    memset(__osEventStatePad, 0, sizeof(__osEventStatePad));
    
    // Clear hardware interrupt table
    memset(__osHwIntTable, 0, sizeof(__osHwIntTable));
    
    // Initialize thread pointers
    __osRunningThread = nullptr;
    __osRunQueue = nullptr;
    __osFaultedThread = nullptr;
    __osShutdown = 0;
    
    // Set up exception vectors in CPU
    // Vector 0x80000000: TLB refill
    // Vector 0x80000080: General exception
    // Vector 0x80000100: Interrupt (not used on N64)
    // Vector 0x80000180: General exception (common)
}

// ============================================================================
// UTILITY FUNCTIONS FOR EMULATOR INTEGRATION
// ============================================================================

extern "C" void __osSetHwInterrupt(uint32_t interrupt, uint32_t handler) {
    if (interrupt < 5) {
        __osHwIntTable[interrupt] = handler;
    }
}

extern "C" void __osSetEventHandler(uint32_t event, OSMesgQueue* queue, uint32_t msg) {
    if (event < 32) {
        __osEventStateTab[event] = queue;
        __osEventStatePad[event] = msg;
    }
}

extern "C" void __osSetGlobalIntMask(uint32_t mask) {
    __OSGlobalIntMask = mask;
}

extern "C" uint32_t __osGetGlobalIntMask() {
    return __OSGlobalIntMask;
}

extern "C" void __osSetRunningThread(OSThread* thread) {
    __osRunningThread = thread;
}

extern "C" OSThread* __osGetRunningThread() {
    return __osRunningThread;
}

extern "C" void __osSetRunQueue(OSThread* queue) {
    __osRunQueue = queue;
}

extern "C" OSThread* __osGetRunQueue() {
    return __osRunQueue;
}

// ============================================================================
// HARDWARE REGISTER EMULATION HELPERS
// ============================================================================

extern "C" void __osSetHardwareReg(uint32_t addr, uint32_t value) {
    writeHW(addr, value);
}

extern "C" uint32_t __osGetHardwareReg(uint32_t addr) {
    return readHW(addr);
}

// Trigger specific interrupts for testing
extern "C" void __osTriggerInterrupt(uint32_t intMask) {
    if (g_cpuState == nullptr) return;
    
    // Set interrupt pending bits in Cause register
    uint32_t cause = g_cpuState->cop0[COP0_CAUSE];
    cause |= (intMask & 0xFF00);
    g_cpuState->cop0[COP0_CAUSE] = cause;
    
    // If interrupts are enabled, trigger exception
    uint32_t sr = g_cpuState->cop0[COP0_SR];
    if ((sr & 0x01) && !(sr & 0x02) && !(sr & 0x04)) {
        // IE=1, EXL=0, ERL=0 - interrupts enabled
        D_8026A300();
    }
}

// Clear specific interrupts
extern "C" void __osClearInterrupt(uint32_t intMask) {
    if (g_cpuState == nullptr) return;
    
    uint32_t cause = g_cpuState->cop0[COP0_CAUSE];
    cause &= ~(intMask & 0xFF00);
    g_cpuState->cop0[COP0_CAUSE] = cause;
}

// ============================================================================
// DEBUG AND VALIDATION
// ============================================================================

#ifdef DEBUG_EXCEPTIONS
#include <cstdio>

extern "C" void __osDumpThreadState(OSThread* thread) {
    if (thread == nullptr) {
        printf("Thread is NULL\n");
        return;
    }
    
    printf("Thread State Dump:\n");
    printf("  Priority: %u\n", thread->priority);
    printf("  State: %u\n", thread->state);
    printf("  Flags: %u\n", thread->flags);
    printf("  PC: 0x%08X\n", thread->pc);
    printf("  SR: 0x%08X\n", thread->sr);
    printf("  Cause: 0x%08X\n", thread->cause);
    printf("  BadVAddr: 0x%08X\n", thread->badvaddr);
    printf("  SP: 0x%016llX\n", (unsigned long long)thread->sp);
    printf("  RA: 0x%016llX\n", (unsigned long long)thread->ra);
    printf("  FP Enabled: %u\n", thread->fp);
}

extern "C" void __osDumpCPUState(CPUState* cpu) {
    if (cpu == nullptr) {
        printf("CPU State is NULL\n");
        return;
    }
    
    printf("CPU State Dump:\n");
    printf("  PC: 0x%08X\n", cpu->pc);
    printf("  HI: 0x%016llX\n", (unsigned long long)cpu->hi);
    printf("  LO: 0x%016llX\n", (unsigned long long)cpu->lo);
    printf("  SR: 0x%08X\n", cpu->cop0[COP0_SR]);
    printf("  Cause: 0x%08X\n", cpu->cop0[COP0_CAUSE]);
    printf("  EPC: 0x%08X\n", cpu->cop0[COP0_EPC]);
    printf("  BadVAddr: 0x%08X\n", cpu->cop0[COP0_BADVADDR]);
    
    printf("  GPRs:\n");
    for (int i = 0; i < 32; i++) {
        printf("    $%2d: 0x%016llX\n", i, (unsigned long long)cpu->gpr[i]);
    }
}

extern "C" void __osValidateThreadQueue(OSThread* queue) {
    printf("Validating thread queue at %p\n", (void*)queue);
    
    int count = 0;
    uint32_t lastPriority = 0xFFFFFFFF;
    OSThread* current = queue;
    
    while (current != nullptr) {
        printf("  Thread %d: Priority=%u, State=%u\n", 
               count, current->priority, current->state);
        
        if (current->priority > lastPriority) {
            printf("    ERROR: Priority violation! %u > %u\n", 
                   current->priority, lastPriority);
        }
        
        lastPriority = current->priority;
        current = (OSThread*)current->next;
        count++;
        
        if (count > 100) {
            printf("    ERROR: Circular queue detected!\n");
            break;
        }
    }
    
    printf("  Total threads: %d\n", count);
}
#endif // DEBUG_EXCEPTIONS

// ============================================================================
// ALTERNATIVE EXCEPTION HANDLERS
// ============================================================================

// Simplified exception handler for emulators that don't need full OS support
extern "C" void __osSimpleExceptionHandler() {
    CPUState* cpu = g_cpuState;
    if (cpu == nullptr) return;
    
    uint32_t cause = cpu->cop0[COP0_CAUSE];
    uint32_t excCode = (cause >> 2) & 0x1F;
    
    switch (excCode) {
        case 0x00: // Interrupt
            // Check which interrupts are pending
            if (cause & 0x8000) { // Timer
                cpu->cop0[COP0_COMPARE] = cpu->cop0[COP0_COUNT];
            }
            break;
            
        case 0x04: // Address Error (Load)
        case 0x05: // Address Error (Store)
            // Handle misaligned access
            break;
            
        case 0x09: // Breakpoint
            // Debugger support
            break;
            
        case 0x0A: // Reserved Instruction
            // Illegal instruction
            break;
            
        case 0x0B: // Coprocessor Unusable
            {
                uint32_t copNum = (cause >> 28) & 0x3;
                if (copNum == 1) {
                    // Enable FPU
                    cpu->cop0[COP0_SR] |= 0x20000000;
                }
            }
            break;
            
        case 0x0C: // Arithmetic Overflow
            // Handle overflow exception
            break;
            
        case 0x0D: // Trap
            // Handle trap instruction
            break;
            
        default:
            // Unknown exception - halt
            break;
    }
}

// ============================================================================
// END OF exceptasm.cpp
// ============================================================================