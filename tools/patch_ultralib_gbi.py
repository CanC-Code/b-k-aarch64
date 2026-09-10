#!/usr/bin/env python3
"""Register 64-bit host pointers, and fix arm64-hostile type sizes."""
import re
import sys

PATH = 'lib/ultralib/include/PR/gbi.h'

with open(PATH) as f:
    text = f.read()

already = 'BKA_REG_DL_ADDR' in text

# ---------------------------------------------------------------
# 1. Register host pointers before the DL truncates them to 32 bits.
# ---------------------------------------------------------------
if not already:
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

    if anchor not in text:
        sys.stderr.write("ERROR: gDma0p anchor not found\n")
        sys.exit(1)
    text = text.replace(anchor, helper, 1)

    # Inject BKA_REG_DL_ADDR into gDma1p and gDma2p bodies
    def inject(text, macro_name, param):
        start = None
        for i, line in enumerate(text.split('\n')):
            if '#define' in line and macro_name + '(' in line and 'gs' + macro_name[1:] not in line:
                start = i
                break
        if start is None:
            sys.stderr.write(f"WARN: {macro_name} macro not found\n")
            return text
        lines = text.split('\n')
        for i in range(start, min(start + 12, len(lines))):
            if 'Gfx *_g' in lines[i] and '(Gfx *)' in lines[i]:
                lines.insert(i + 1, f'        BKA_REG_DL_ADDR({param});                \\\\')
                break
        return '\n'.join(lines)

    text = inject(text, 'gDma1p', 's')
    text = inject(text, 'gDma2p', 'adrs')
    print("host-pointer registration installed")

# ---------------------------------------------------------------
# 2. Fix Mtx size: N64 long = 4 bytes, arm64 long = 8 bytes.
#    Force 32-bit elements so Mtx stays 64 bytes.
# ---------------------------------------------------------------
mtx_new = 'typedef int32_t Mtx_t[4][4];  /* arm64: force 32-bit elements; N64 Mtx is 64 bytes */'
if 'int32_t Mtx_t' not in text:
    m = re.search(r'typedef\s+long\s+Mtx_t\[4\]\[4\];', text)
    if m:
        text = text[:m.start()] + mtx_new + text[m.end():]
        print("Mtx_t patched")
    else:
        print("WARN: Mtx_t definition not found")
else:
    print("Mtx_t already patched")

with open(PATH, 'w') as f:
    f.write(text)

print("gbi.h patched")
