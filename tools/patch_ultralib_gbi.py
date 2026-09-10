#!/usr/bin/env python3
"""Register 64-bit host pointers, and fix arm64-hostile type sizes."""
import re
import sys

PATH = 'lib/ultralib/include/PR/gbi.h'

with open(PATH) as f:
    lines = f.readlines()

text = ''.join(lines)

# ---------------------------------------------------------------
# 1. Register host pointers before the DL truncates them to 32 bits.
# ---------------------------------------------------------------
if 'BKA_REG_DL_ADDR' not in text:
    # Find the line that defines gDma0p — anchor on the bare signature
    anchor_idx = None
    for i, line in enumerate(lines):
        if '#define' in line and 'gDma0p(pkt, c, s, l)' in line:
            anchor_idx = i
            break

    if anchor_idx is None:
        sys.stderr.write("ERROR: could not find '#define gDma0p(pkt, c, s, l)'\n")
        sys.exit(1)

    helper_lines = [
        '/*\n',
        ' * bka: 64-bit host pointer recovery. Every address the recomp writes into\n',
        ' * a DL gets truncated to 32 bits. Register the full pointer under its low\n',
        ' * 32 bits so RDP_TranslateAddr can recover it at decode time.\n',
        ' */\n',
        'extern void bka_add_addr_mapping_c(unsigned int key, void *ptr);\n',
        '#define BKA_REG_DL_ADDR(s) do {                                   \\\n',
        '        unsigned long long __bka_a = (unsigned long long)(s);     \\\n',
        '        if (__bka_a != 0) {                                       \\\n',
        '            bka_add_addr_mapping_c((unsigned int)__bka_a,         \\\n',
        '                                   (void *)__bka_a);              \\\n',
        '        }                                                         \\\n',
        '    } while (0)\n',
        '\n',
    ]
    lines = lines[:anchor_idx] + helper_lines + lines[anchor_idx:]


def inject_after_gfx_line(lines, macro_name, param):
    """Insert BKA_REG_DL_ADDR(param) right after the 'Gfx *_g = ...' line."""
    start = None
    for i, line in enumerate(lines):
        if '#define' in line and macro_name + '(' in line:
            start = i
            break
    if start is None:
        sys.stderr.write(f"WARN: {macro_name} macro not found\n")
        return lines

    insert_at = None
    for i in range(start, min(start + 12, len(lines))):
        if 'Gfx *_g' in lines[i] and '(Gfx *)' in lines[i]:
            insert_at = i + 1
            break
    if insert_at is None:
        sys.stderr.write(f"WARN: 'Gfx *_g' line not found in {macro_name}\n")
        return lines

    lines.insert(insert_at, f'        BKA_REG_DL_ADDR({param});                \\\n')
    return lines


if 'BKA_REG_DL_ADDR' not in text:
    lines = inject_after_gfx_line(lines, 'gDma1p', 's')
    lines = inject_after_gfx_line(lines, 'gDma2p', 'adrs')

text = ''.join(lines)

# ---------------------------------------------------------------
# 2. Fix Mtx size: N64 long = 4 bytes, arm64 long = 8 bytes.
# ---------------------------------------------------------------
if 'int32_t Mtx_t' not in text:
    m = re.search(r'typedef\s+long\s+Mtx_t\[4\]\[4\];', text)
    if m:
        text = text[:m.start()] + \
            'typedef int32_t Mtx_t[4][4];  /* arm64: N64 Mtx is 64 bytes */' + \
            text[m.end():]
        print("Mtx_t patched")
    else:
        print("WARN: Mtx_t definition not found")
else:
    print("Mtx_t already patched")

with open(PATH, 'w') as f:
    f.write(text)

print("gbi.h patched")
