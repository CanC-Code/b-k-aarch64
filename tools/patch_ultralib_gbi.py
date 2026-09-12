#!/usr/bin/env python3
"""Register 64-bit host pointers, and fix arm64-hostile type sizes."""
import re
import sys

PATH = 'lib/ultralib/include/PR/gbi.h'

with open(PATH) as f:
    lines = f.readlines()
text = ''.join(lines)

# 1. Insert extern declarations before gDma0p.
if 'bka_trace_ff_val' not in text:
    anchor_idx = None
    for i, line in enumerate(lines):
        if '#define' in line and 'gDma0p(pkt, c, s, l)' in line:
            anchor_idx = i
            break
    if anchor_idx is None:
        sys.stderr.write("ERROR: gDma0p anchor not found\n")
        sys.exit(1)
    helper_lines = [
        '/* bka: 64-bit host pointer recovery. */\n',
        'extern void bka_add_addr_mapping_c(unsigned int key, void *ptr);\n',
        'extern void bka_trace_ff_val(unsigned long long v);\n',
        '\n',
    ]
    lines = lines[:anchor_idx] + helper_lines + lines[anchor_idx:]
    text = ''.join(lines)

# 2. Replace gDma1p/gDma2p bodies with guarded versions that call the trace.
def replace_macro(lines, name):
    start = None
    for i, line in enumerate(lines):
        if '#define' in line and name + '(' in line:
            start = i
            break
    if start is None:
        return lines
    end = None
    depth = 0
    seen = False
    for i in range(start, min(start + 20, len(lines))):
        if '{' in lines[i]:
            depth += lines[i].count('{')
            seen = True
        if '}' in lines[i] and seen:
            depth -= lines[i].count('}')
            if depth <= 0:
                end = i
                break
    if end is None:
        return lines
    return lines[:start], end

GUARD = ('if (__bka_a != 0) { bka_add_addr_mapping_c((unsigned int)__bka_a, (void *)__bka_a); '
         'if ((__bka_a & 0xFF000000ULL) == 0xFF000000ULL) bka_trace_ff_val(__bka_a); }')

gdma1p_body = [
    '#define    gDma1p(pkt, c, s, l, p)    \\\n',
    '{                                          \\\n',
    '        Gfx *_g = (Gfx *)(pkt);            \\\n',
    '        unsigned long long __bka_a = (unsigned long long)(s);  \\\n',
    '        ' + GUARD + '  \\\n',
    '        _g->words.w0 = (_SHIFTL((c), 24, 8) | _SHIFTL((p), 16, 8) | _SHIFTL((l), 0, 16));  \\\n',
    '        _g->words.w1 = (unsigned int)__bka_a;  \\\n',
    '}\n',
]

gdma2p_body = [
    '#define gDma2p(pkt, c, adrs, len, idx, ofs)\\\n',
    '{                                          \\\n',
    '        Gfx *_g = (Gfx *)(pkt);            \\\n',
    '        unsigned long long __bka_a = (unsigned long long)(adrs);  \\\n',
    '        ' + GUARD + '  \\\n',
    '        _g->words.w0 = (_SHIFTL((c),24,8)|_SHIFTL(((len)-1)/8,19,5)|_SHIFTL((ofs)/8,8,8)|_SHIFTL((idx),0,8));  \\\n',
    '        _g->words.w1 = (unsigned int)__bka_a;  \\\n',
    '}\n',
]

if 'bka_trace_ff_val(__bka_a)' not in text:
    for name, body in [('gDma1p', gdma1p_body), ('gDma2p', gdma2p_body)]:
        r = replace_macro(lines, name)
        if isinstance(r, tuple):
            head, end = r
            lines = head + body + lines[end + 1:]
        else:
            lines = r
    text = ''.join(lines)

# 3. Mtx size: 4x4 s32 on arm64.
if 'int32_t Mtx_t' not in text:
    m = re.search(r'typedef\s+long\s+Mtx_t\[4\]\[4\];', text)
    if m:
        text = text[:m.start()] + 'typedef int32_t Mtx_t[4][4];  /* arm64: N64 Mtx is 64 bytes */' + text[m.end():]
        print("Mtx_t patched")

with open(PATH, 'w') as f:
    f.write(text)

n_trace = text.count('bka_trace_ff_val(__bka_a)')
n_decl  = text.count('extern void bka_trace_ff_val')
print("trace calls:", n_trace, "decls:", n_decl)
assert n_trace == 2, "gDma1p/gDma2p trace not injected"
assert n_decl  == 1, "extern decl not injected"
print("gbi.h patched")
