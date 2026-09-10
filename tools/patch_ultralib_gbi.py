#!/usr/bin/env python3
"""Register 64-bit host pointers before they're truncated into N64 DL words."""
import sys

PATH = 'lib/ultralib/include/PR/gbi.h'

with open(PATH) as f:
    t = f.read()

if 'BKA_REG_DL_ADDR' in t:
    print("already patched")
    sys.exit(0)

anchor = '/*\n * DMA macros\n */\n#define gDma0p(pkt, c, s, l)'
helper = '''/*
 * DMA macros
 *
 * bka: 64-bit host pointer recovery. Every address the recomp writes into
 * a DL gets truncated to 32 bits. Register the full pointer under its low
 * 32 bits so RDP_TranslateAddr can recover it at decode time.
 */
extern void bka_add_addr_mapping_c(unsigned int key, void *ptr);
#define BKA_REG_DL_ADDR(s) do {                                   \\
        unsigned long long __bka_a = (unsigned long long)(s);     \\
        if (__bka_a != 0) {                                       \\
            bka_add_addr_mapping_c((unsigned int)__bka_a,         \\
                                   (void *)__bka_a);              \\
        }                                                         \\
    } while (0)

#define gDma0p(pkt, c, s, l)'''

if anchor not in t:
    raise SystemExit("anchor not found")

t = t.replace(anchor, helper, 1)

old1 = '''#define    gDma1p(pkt, c, s, l, p)    \\
{                                          \\
        Gfx *_g = (Gfx *)(pkt);            \\
                                           \\
        _g->words.w0 = (_SHIFTL((c), 24, 8) | _SHIFTL((p), 16, 8) | \\
                        _SHIFTL((l), 0, 16));                               \\
        _g->words.w1 = (unsigned int)(s);  \\
}'''
new1 = '''#define    gDma1p(pkt, c, s, l, p)    \\
{                                          \\
        Gfx *_g = (Gfx *)(pkt);            \\
        BKA_REG_DL_ADDR(s);                \\
        _g->words.w0 = (_SHIFTL((c), 24, 8) | _SHIFTL((p), 16, 8) | \\
                        _SHIFTL((l), 0, 16));                               \\
        _g->words.w1 = (unsigned int)(s);  \\
}'''
if old1 not in t: raise SystemExit("gDma1p block missing")
t = t.replace(old1, new1, 1)

old2 = '''#define gDma2p(pkt, c, adrs, len, idx, ofs)\\
{                                          \\
        Gfx *_g = (Gfx *)(pkt);            \\
        _g->words.w0 = (_SHIFTL((c),24,8)|_SHIFTL(((len)-1)/8,19,5)|        \\
                        _SHIFTL((ofs)/8,8,8)|_SHIFTL((idx),0,8));   \\
        _g->words.w1 = (unsigned int)(adrs);\\
}'''
new2 = '''#define gDma2p(pkt, c, adrs, len, idx, ofs)\\
{                                          \\
        Gfx *_g = (Gfx *)(pkt);            \\
        BKA_REG_DL_ADDR(adrs);             \\
        _g->words.w0 = (_SHIFTL((c),24,8)|_SHIFTL(((len)-1)/8,19,5)|        \\
                        _SHIFTL((ofs)/8,8,8)|_SHIFTL((idx),0,8));   \\
        _g->words.w1 = (unsigned int)(adrs);\\
}'''
if old2 not in t: raise SystemExit("gDma2p block missing")
t = t.replace(old2, new2, 1)

with open(PATH, 'w') as f:
    f.write(t)

print("gbi.h patched")
