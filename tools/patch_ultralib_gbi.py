#!/usr/bin/env python3
"""Register 64-bit host pointers, and fix arm64-hostile type sizes."""
import re
import sys

PATH = 'lib/ultralib/include/PR/gbi.h'

with open(PATH) as f:
    lines = f.readlines()
text = ''.join(lines)

# 1. Insert extern declarations before gDma0p.
if 'bka_log_gdma_ra' not in text:
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
        'extern void bka_log_gdma_ra(void* ra, unsigned long long v);\n',
        '\n',
    ]
    lines = lines[:anchor_idx] + helper_lines + lines[anchor_idx:]
    text = ''.join(lines)

# 2. Replace gDma1p/gDma2p bodies if not already done.
def find_macro(lines, name):
    start = None
    for i, line in enumerate(lines):
        if '#define' in line and name + '(' in line:
            start = i
            break
    if start is None:
        return None, None
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
    return start, end

GUARD = ('bka_log_gdma_ra((void*)__builtin_return_address(0), __bka_a); if ((__bka_a >> 24) == 1) __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX", "SEG1EMIT ra=%p a=0x%llx l=%u p=%u", __builtin_return_address(0), __bka_a, (unsigned)(l), (unsigned)(p)); '
         'if (__bka_a != 0) { '
         'bka_add_addr_mapping_c((unsigned int)__bka_a, (void *)__bka_a); '
         'if ((unsigned int)__bka_a == 0xFFF9153F || (unsigned int)__bka_a == 0xFFFF153F '
         '|| ((unsigned int)__bka_a & 0xFF000000u) == 0xFF000000u) '
         'bka_trace_ff_val(__bka_a); }')

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

if 'bka_log_gdma_ra((void*)__builtin_return_address(0), __bka_a)' not in text:
    for name, body in [('gDma1p', gdma1p_body), ('gDma2p', gdma2p_body)]:
        start, end = find_macro(lines, name)
        if start is None or end is None:
            sys.stderr.write("WARN: %s macro not found\n" % name)
            continue
        lines = lines[:start] + body + lines[end + 1:]
    text = ''.join(lines)

# 3. Mtx size.
if 'int32_t Mtx_t' not in text:
    m = re.search(r'typedef\s+long\s+Mtx_t\[4\]\[4\];', text)
    if m:
        text = text[:m.start()] + 'typedef int32_t Mtx_t[4][4];  /* arm64: N64 Mtx is 64 bytes */' + text[m.end():]
        print("Mtx_t patched")

with open(PATH, 'w') as f:
    f.write(text)

n_trace = text.count('bka_trace_ff_val(__bka_a)')
n_log   = text.count('bka_log_gdma_ra((void*)')
n_decl  = text.count('extern void bka_log_gdma_ra')
print("trace calls:", n_trace, "log calls:", n_log, "decls:", n_decl)
assert n_trace == 2, "gDma1p/gDma2p trace not injected"
assert n_log   == 2, "gDma1p/gDma2p gdma-ra log not injected"
assert n_decl  == 1, "extern decl not injected"
print("gbi.h patched")
