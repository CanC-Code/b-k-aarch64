#!/usr/bin/env python3
"""Register 64-bit host pointers before they're truncated into N64 DL words."""
import sys

PATH = 'lib/ultralib/include/PR/gbi.h'

with open(PATH) as f:
    lines = f.readlines()

text = ''.join(lines)
if 'BKA_REG_DL_ADDR' in text:
    print("already patched")
    sys.exit(0)

# Find the line that defines gDma0p — anchor by its function signature only
anchor_idx = None
for i, line in enumerate(lines):
    if line.lstrip().startswith('#define') and 'gDma0p(pkt, c, s, l)' in line:
        anchor_idx = i
        break

if anchor_idx is None:
    sys.stderr.write("ERROR: could not find '#define gDma0p(pkt, c, s, l)'\n")
    sys.exit(1)

helper_lines = [
    '/*\n',
    ' * bka: 64-bit host pointer recovery. The N64 Gfx word is 32 bits, so\n',
    ' * every address the recomp writes into a DL gets truncated. Register\n',
    ' * the full 64-bit pointer under its low 32 bits so RDP_TranslateAddr\n',
    ' * can recover it at decode time.\n',
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
    """Insert BKA_REG_DL_ADDR(param) after the `Gfx *_g = ...` line in a macro."""
    start = None
    for i, line in enumerate(lines):
        if '#define' in line and macro_name + '(' in line:
            start = i
            break
    if start is None:
        raise SystemExit(f"macro {macro_name} not found")

    insert_at = None
    for i in range(start, min(start + 12, len(lines))):
        if 'Gfx *_g' in lines[i] and '(Gfx *)' in lines[i]:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit(f"'Gfx *_g' line not found in {macro_name}")

    lines.insert(insert_at, f'        BKA_REG_DL_ADDR({param});                \\\n')
    return lines


lines = inject_after_gfx_line(lines, 'gDma1p', 's')
lines = inject_after_gfx_line(lines, 'gDma2p', 'adrs')

with open(PATH, 'w') as f:
    f.writelines(lines)

print("gbi.h patched")
