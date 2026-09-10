#!/usr/bin/env python3
"""Register 64-bit host pointers, and fix arm64-hostile type sizes."""
import re
import sys

PATH = 'lib/ultralib/include/PR/gbi.h'

with open(PATH) as f:
    lines = f.readlines()

text = ''.join(lines)

# ---------------------------------------------------------------
# 1. Insert helper macro + extern declaration before gDma0p
# ---------------------------------------------------------------
if 'BKA_REG_DL_ADDR' not in text:
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
        ' * bka: 64-bit host pointer recovery.\n',
        ' */\n',
        'extern void bka_add_addr_mapping_c(unsigned int key, void *ptr);\n',
        '\n',
    ]
    lines = lines[:anchor_idx] + helper_lines + lines[anchor_idx:]

# ---------------------------------------------------------------
# 2. Replace the body of gDma1p so `s` is evaluated exactly once.
# ---------------------------------------------------------------
def replace_macro_body(lines, macro_name, param_name):
    """Replace a multiline macro with a single-eval version that registers
    the address before truncating it."""
    # Find the start of the macro
    start = None
    for i, line in enumerate(lines):
        if '#define' in line and macro_name + '(' in line:
            start = i
            break
    if start is None:
        sys.stderr.write(f"WARN: {macro_name} not found\n")
        return lines

    # Find the closing brace of the macro (last line before a blank line
    # or another #define).  The macro is a multiline `{ ... }` block.
    end = None
    depth = 0
    seen_brace = False
    for i in range(start, min(start + 20, len(lines))):
        if '{' in lines[i]:
            depth += lines[i].count('{')
            seen_brace = True
        if '}' in lines[i] and seen_brace:
            depth -= lines[i].count('}')
            if depth <= 0:
                end = i
                break
    if end is None:
        sys.stderr.write(f"WARN: could not find end of {macro_name}\n")
        return lines

    new_body = [
        f'#define    {macro_name}(pkt, c, s, l, p)    \\\n',
        '{                                          \\\n',
        '        Gfx *_g = (Gfx *)(pkt);            \\\n',
        '        unsigned long long __bka_a = (unsigned long long)(s);  \\\n',
        '        if (__bka_a != 0) bka_add_addr_mapping_c((unsigned int)__bka_a, (void *)__bka_a);  \\\n',
        '        _g->words.w0 = (_SHIFTL((c), 24, 8) | _SHIFTL((p), 16, 8) | _SHIFTL((l), 0, 16));  \\\n',
        '        _g->words.w1 = (unsigned int)__bka_a;  \\\n',
        '}\n',
    ]
    # Handle 2p signature separately
    if macro_name == 'gDma2p':
        new_body = [
            '#define gDma2p(pkt, c, adrs, len, idx, ofs)\\\n',
            '{                                          \\\n',
            '        Gfx *_g = (Gfx *)(pkt);            \\\n',
            '        unsigned long long __bka_a = (unsigned long long)(adrs);  \\\n',
            '        if (__bka_a != 0) bka_add_addr_mapping_c((unsigned int)__bka_a, (void *)__bka_a);  \\\n',
            '        _g->words.w0 = (_SHIFTL((c),24,8)|_SHIFTL(((len)-1)/8,19,5)|_SHIFTL((ofs)/8,8,8)|_SHIFTL((idx),0,8));  \\\n',
            '        _g->words.w1 = (unsigned int)__bka_a;  \\\n',
            '}\n',
        ]

    return lines[:start] + new_body + lines[end + 1:]


if 'BKA_REG_DL_ADDR' not in text and 'double-eval fixed' not in text:
    lines = replace_macro_body(lines, 'gDma1p', 's')
    lines = replace_macro_body(lines, 'gDma2p', 'adrs')

text = ''.join(lines)

# ---------------------------------------------------------------
# 3. Fix Mtx size.
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
