#!/usr/bin/env python3
"""
SourceHarmonizer v75.60
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

Drop this file at:  runtime/prepare_source.py
It runs before the CMake/ninja build and patches decomp-files/src in-place.

v75.60 changes vs v75.59:
  - Added header pass H0: patches ultratypes.h to wrap all primitive typedefs
    (s8/u8/s16/u16/s32/u32/s64/u64/f32/f64) in #ifndef guards so the file can
    be included normally without duplicate-typedef errors from NDK stdint.h.
  - CMakeLists no longer needs -D_ULTRATYPES_H_, -D_GBI_H_, or -include gbi.h.
    Those band-aids are what caused the "unknown type name 's32'" cascade.
"""

import re
from pathlib import Path

_C_KEYWORDS = {
    'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
    'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
    'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef',
    'register', 'auto', 'void', 'int', 'char', 'short', 'long', 'float',
    'double', 'unsigned', 'signed', 'bool',
}
_STD_C = {
    'main', 'main_no_args',
    'memcpy', 'memset', 'memmove', 'strlen', 'strcpy', 'strcmp', 'strcat',
    'sprintf', 'printf', 'fprintf', 'malloc', 'free', 'realloc', 'calloc',
    'sin', 'cos', 'sinf', 'cosf', 'sqrt', 'sqrtf', 'abs', 'fabs', 'fabsf',
    'atan2', 'atan2f', 'pow', 'powf', 'ceil', 'ceilf', 'floor', 'floorf',
}
_SDK_PREFIXES = (
    'os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon',
)
_STORAGE_QUALS = {
    'static', 'extern', 'inline', 'const', 'volatile', '__attribute__',
    '__restrict', 'restrict', 'register',
}
_CTRL_KW_SET = {
    'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
    'break', 'continue', 'case', 'default', 'goto', 'typedef',
}

# ─────────────────────────────────────────────────────────────────────────────
# Pass 0 — Compatibility preamble
# ─────────────────────────────────────────────────────────────────────────────

PREAMBLE_MARKER = "/* SH-v75.50-preamble */"

PREAMBLE = """\
{marker}
/* SourceHarmonizer v75.60 — Android/NDK compatibility preamble             */
/* All definitions are guarded with #ifndef — never overrides decomp headers */

/* F3DEX_GBI_2: enables G_TRI2 and all F3DEX2 GBI opcodes in gbi.h.         */
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#include <stddef.h>       /* size_t, ptrdiff_t, NULL                         */
#include <string.h>       /* memcpy — used by Pass 1 array-init replacements */

/* bool / _Bool compatibility.
   DO NOT #include <stdbool.h> here — that would define `bool` as `_Bool`,
   and then decomp-files/include/bool.h's `typedef int bool` would expand to
   `typedef int _Bool`, which Clang rejects ("cannot combine with previous
   'int' declaration specifier").
   Instead we set __bool_true_false_are_defined — the exact guard that both
   the C99 stdbool.h and the decomp's own bool.h check before doing anything.
   This tells bool.h "bool is already handled, skip the typedef" without
   actually pulling in stdbool.h or redefining bool ourselves.            */
#ifndef __bool_true_false_are_defined
#  define __bool_true_false_are_defined 1
#  ifndef bool
#    define bool  _Bool
#  endif
#  ifndef true
#    define true  1
#  endif
#  ifndef false
#    define false 0
#  endif
#endif

/* Android system headers sometimes define min/max/abs as macros that clash  */
/* with the decomp's own definitions.  Undefine them before re-defining.     */
#ifdef min
#  undef min
#endif
#ifdef max
#  undef max
#endif
#ifdef abs
#  undef abs
#endif

/* BOOL: single-argument boolean-cast macro used throughout game logic.      */
#ifndef BOOL
#  define BOOL(x) (!!(x))
#endif

/* Boolean constants */
#ifndef TRUE
#  define TRUE  1
#endif
#ifndef FALSE
#  define FALSE 0
#endif

/* Common N64 decomp utility macros */
#ifndef ABS
#  define ABS(x)           ((x) < 0 ? -(x) : (x))
#endif
#ifndef MIN
#  define MIN(a, b)        ((a) < (b) ? (a) : (b))
#endif
#ifndef MAX
#  define MAX(a, b)        ((a) > (b) ? (a) : (b))
#endif
#ifndef CLAMP
#  define CLAMP(x, lo, hi) ((x) < (lo) ? (lo) : (x) > (hi) ? (hi) : (x))
#endif
#ifndef ARRAY_COUNT
#  define ARRAY_COUNT(x)   (sizeof(x) / sizeof((x)[0]))
#endif
/* ── End SourceHarmonizer v75.60 preamble ─────────────────────────────── */

""".format(marker=PREAMBLE_MARKER)

# ─────────────────────────────────────────────────────────────────────────────
# Pass 0a — Fix #include <ultra64.h> → #include "ultra64.h"
# ─────────────────────────────────────────────────────────────────────────────

def _fix_ultra64_include(content: str) -> str:
    return re.sub(r'#include\s*<ultra64\.h>', '#include "ultra64.h"', content)

# ─────────────────────────────────────────────────────────────────────────────
# Pass 1 — Generic array-init-from-symbol fix
# ─────────────────────────────────────────────────────────────────────────────

_ARRAY_INIT_PAT = re.compile(
    r'^([ \t]*)'
    r'((?:(?:struct|union|enum)\s+)?'
    r'[A-Za-z_]\w*(?:\s*\*)*)\s+'
    r'([A-Za-z_]\w*)'
    r'\[(\d+)\]\s*=\s*'
    r'([A-Za-z_]\w*)\s*;',
    re.MULTILINE
)

def _fix_array_inits(content: str) -> str:
    def _repl(m: re.Match) -> str:
        indent, typ, var, _size, sym = (
            m.group(1), m.group(2).strip(), m.group(3), m.group(4), m.group(5)
        )
        return (
            f"{indent}{typ} {var}[{_size}];\n"
            f"{indent}memcpy({var}, {sym}, sizeof({var}));"
        )
    return _ARRAY_INIT_PAT.sub(_repl, content)

# ─────────────────────────────────────────────────────────────────────────────
# Pass 2 — Static conflict fixer
# ─────────────────────────────────────────────────────────────────────────────

def _strip_comments(text: str) -> str:
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
    return text

def _find_static_defs(clean: str) -> dict:
    pat = re.compile(
        r'\bstatic\b([^;{}]*?\b([A-Za-z_]\w*)\s*\([^{}]*?\))\s*\{',
        re.DOTALL
    )
    out = {}
    for m in pat.finditer(clean):
        name = m.group(2)
        if name not in _C_KEYWORDS and name not in out:
            out[name] = m.group(1).strip()
    return out

def _has_typed_fwd_decl(clean: str, name: str) -> bool:
    pat = re.compile(
        r'^([ \t]*(?:[^\n]*?))\b' + re.escape(name) + r'\s*\([^{}]*?\)\s*;',
        re.MULTILINE
    )
    for m in pat.finditer(clean):
        prefix = m.group(1)
        if re.search(r'[=!&|^~+\-/%<>?]', prefix):
            continue
        if '(' in prefix:
            continue
        tokens = re.findall(r'[A-Za-z_]\w*', prefix)
        type_tokens = [t for t in tokens
                       if t not in _STORAGE_QUALS and t not in _CTRL_KW_SET]
        if type_tokens:
            return True
    return False

def _fix_static_conflicts(content: str) -> str:
    clean = _strip_comments(content)
    static_defs = _find_static_defs(clean)
    if not static_defs:
        return content

    modified = content
    needs_inject = []

    for fname, sig in static_defs.items():
        fwd_pat = re.compile(
            r'^([ \t]*)(?!static\b)(\b\S[^\n]*?\b'
            + re.escape(fname) + r'\s*\([^)]*\)\s*;)',
            re.MULTILINE
        )
        patched = fwd_pat.sub(lambda m: f"{m.group(1)}static {m.group(2)}", modified)
        if patched != modified:
            modified = patched
            continue

        if _has_typed_fwd_decl(clean, fname):
            continue

        call_pat = re.compile(r'\b' + re.escape(fname) + r'\s*\(')
        def_pat  = re.compile(
            r'\bstatic\b[^;{}]*?\b' + re.escape(fname) + r'\s*\([^{}]*?\)\s*\{',
            re.DOTALL
        )
        cm = call_pat.search(clean)
        dm = def_pat.search(clean)
        if cm and dm and cm.start() < dm.start():
            needs_inject.append(f"static {sig};")

    if needs_inject:
        block = (
            "// --- SH static forward declarations ---\n"
            + "\n".join(needs_inject) + "\n"
            + "// --- SH static forward declarations end ---\n\n"
        )
        last_inc = None
        for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
            last_inc = m
        pos = last_inc.end() if last_inc else 0
        modified = modified[:pos] + block + modified[pos:]

    return modified

# ─────────────────────────────────────────────────────────────────────────────
# Pass 3 — IDO static-local normalisation
# ─────────────────────────────────────────────────────────────────────────────

_CTRL_KW_PAT = re.compile(
    r'^([ \t]+)static\s+'
    r'(return|if|else|while|for|do|switch|break|continue|goto|case|default|sizeof)\b',
    re.MULTILINE
)
_P3A = re.compile(
    r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
    re.MULTILINE
)
_P3A2 = re.compile(
    r'^([ \t]+)static\s+([A-Za-z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
    re.MULTILINE
)
_P3B = re.compile(
    r'^([ \t]+)static\s+([A-Za-z_]\w*)\s*=\s*'
    r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
    re.MULTILINE
)
_P3C = re.compile(
    r'^([ \t]+)static\s+([^=\n;{}]+?)\b([A-Za-z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
    re.MULTILINE
)

def _fix_static_locals(content: str) -> str:
    content = _CTRL_KW_PAT.sub(lambda m: f"{m.group(1)}{m.group(2)}", content)
    content = _P3A.sub(
        lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}", content
    )
    content = _P3A2.sub(
        lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
        content
    )
    content = _P3B.sub(
        lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};", content
    )
    def _rule_c(m: re.Match) -> str:
        rhs = m.group(4).strip()
        if '(' not in rhs:
            return m.group(0)
        indent, typ, var = m.group(1), m.group(2), m.group(3)
        return f"{indent}static {typ}{var}; {var} = {rhs};"
    content = _P3C.sub(_rule_c, content)
    return content

# ─────────────────────────────────────────────────────────────────────────────
# Pass 4 — Weak symbol injection
# ─────────────────────────────────────────────────────────────────────────────

_DEF_PAT_CACHE: dict = {}

_FWD_DECL_PAT = re.compile(
    r'(?<![;{}])\b([A-Za-z_]\w*)\s*\([^{}]*?\)\s*;', re.DOTALL
)

def _find_fwd_declared(clean: str) -> set:
    names: set = set()
    for m in _FWD_DECL_PAT.finditer(clean):
        name = m.group(1)
        if name in _C_KEYWORDS:
            continue
        prefix = clean[:m.start()]
        cut = max(prefix.rfind(';'), prefix.rfind('{'), prefix.rfind('}'))
        seg = prefix[cut + 1:] if cut != -1 else prefix
        tokens = set(re.findall(r'[A-Za-z_]\w*', seg))
        if not tokens or 'typedef' in tokens:
            continue
        names.add(name)
    return names

def _build_def_pat(fname: str) -> re.Pattern:
    return re.compile(
        r'^([ \t]*)([A-Za-z_0-9\s\*]*?\b)('
        + re.escape(fname)
        + r'\s*\([^{};]*?\)\s*\{)',
        re.MULTILINE | re.DOTALL
    )

def _inject_weak(content: str, fname: str) -> str:
    if fname not in _DEF_PAT_CACHE:
        _DEF_PAT_CACHE[fname] = _build_def_pat(fname)
    pat = _DEF_PAT_CACHE[fname]

    def _repl(m: re.Match) -> str:
        full, indent, before, rest = (
            m.group(0), m.group(1), m.group(2), m.group(3)
        )
        if '__attribute__((weak))' in full:
            return full
        if re.search(r'\bstatic\b', before):
            return full
        return f"{indent}__attribute__((weak)) {before.lstrip()}{rest}"

    return pat.sub(_repl, content)

_FUNC_SCAN_PAT = re.compile(r'\b([A-Za-z_]\w*)\s*\([^{;]*\)\s*\{')

def _inject_weak_symbols(content: str) -> str:
    clean = _strip_comments(content)
    static_names = set(_find_static_defs(clean).keys())
    fwd_names    = _find_fwd_declared(clean)
    excluded     = static_names | fwd_names

    seen: set = set()
    candidates = []

    for m in _FUNC_SCAN_PAT.finditer(clean):
        fname = m.group(1)
        if fname in _C_KEYWORDS or fname in _STD_C:
            continue
        if fname.startswith(_SDK_PREFIXES):
            continue
        if fname.isupper() or fname.startswith('__'):
            continue
        if fname in excluded:
            continue
        pre = clean[:m.start()]
        cut = max(pre.rfind(';'), pre.rfind('}'), pre.rfind('{'))
        seg = pre[cut + 1:] if cut != -1 else pre
        ctx = set(re.findall(r'[A-Za-z_]\w*', seg))
        if ctx & {'static', 'inline', 'typedef'}:
            continue
        if fname not in seen:
            seen.add(fname)
            candidates.append(fname)

    for fname in candidates:
        content = _inject_weak(content, fname)
    return content

# ─────────────────────────────────────────────────────────────────────────────
# Pass 0b — Use-before-definition forward declaration injection
# ─────────────────────────────────────────────────────────────────────────────

_FDEF_SCAN = re.compile(
    r'^([ \t]*)([A-Za-z_][\w\s\*]*?)\b([A-Za-z_]\w*)\s*(\([^)]*\))\s*\{',
    re.MULTILINE,
)
_CALL_SCAN = re.compile(r'(?<![A-Za-z_0-9])\b([A-Za-z_]\w*)\s*\(')
_NOT_RETURN = {
    'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
    'break', 'continue', 'case', 'default', 'goto', 'static', 'extern',
    'inline', 'typedef', 'register', 'auto', '__attribute__', '__restrict',
    'restrict',
}

def _inject_use_before_def_fwddecls(content: str) -> str:
    clean = _strip_comments(content)

    defs: dict[str, tuple[int, str, str]] = {}
    for m in _FDEF_SCAN.finditer(clean):
        indent = m.group(1)
        if indent:
            continue
        ret_raw = m.group(2).strip()
        name    = m.group(3)
        params  = m.group(4)
        pos     = m.start()

        if name in _NOT_RETURN or name.isupper() or name.startswith('__'):
            continue
        if name.startswith(_SDK_PREFIXES):
            continue
        if 'static' in ret_raw.split():
            continue
        ret = re.sub(r'\s+', ' ', ret_raw).strip()
        if not ret or ret in _NOT_RETURN:
            ret = 'void'

        if name not in defs:
            defs[name] = (pos, ret, params)

    if not defs:
        return content

    needed: list[str] = []
    seen_needed: set[str] = set()

    for m in _CALL_SCAN.finditer(clean):
        name = m.group(1)
        if name not in defs:
            continue
        def_pos, ret, params = defs[name]
        if m.start() >= def_pos:
            continue
        if name in seen_needed:
            continue
        seen_needed.add(name)
        needed.append(f'{ret} {name}{params};')

    if not needed:
        return content

    existing_fwds = set()
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\([^)]*\)\s*;', clean):
        existing_fwds.add(m.group(1))
    needed = [decl for decl in needed
              if decl.split('(')[0].split()[-1] not in existing_fwds]

    if not needed:
        return content

    block = (
        '/* SH: forward decls for use-before-definition */\n'
        + '\n'.join(needed)
        + '\n/* SH: end forward decls */\n\n'
    )

    audioinfo_def = re.search(r'typedef\s+struct\s+AudioInfo_s\s+\{.*?\};', content, re.DOTALL)
    if audioinfo_def:
        insert_at = audioinfo_def.end()
    else:
        end_marker = re.search(r'/\* ── End SourceHarmonizer.*?preamble.*?\*/\n', content)
        if end_marker:
            insert_at = end_marker.end()
        else:
            insert_at = 0

    return content[:insert_at] + block + content[insert_at:]

# ─────────────────────────────────────────────────────────────────────────────
# Pass 5 — Return type mismatch fix
# ─────────────────────────────────────────────────────────────────────────────

def _fix_return_type_mismatch(content: str, path: Path) -> str:
    if path.name != "depthbuffer.c":
        return content
    pat = re.compile(
        r'^([ \t]*)__attribute__\(\(weak\)\)\s+int\s+func_80253400\s*\([^)]*\)\s*\{',
        re.MULTILINE
    )
    return pat.sub(
        lambda m: f"{m.group(1)}__attribute__((weak)) bool func_80253400(){{",
        content
    )

# ─────────────────────────────────────────────────────────────────────────────
# Pass 6 — Missing includes for custom types
# ─────────────────────────────────────────────────────────────────────────────

def _inject_missing_includes(content: str, path: Path) -> str:
    if path.name != "anctrl.c":
        return content
    if "AnimCtrl" in content and "#include \"animctrl.h\"" not in content:
        last_inc = None
        for m in re.finditer(r'^#include\b[^\n]*\n', content, re.MULTILINE):
            last_inc = m
        pos = last_inc.end() if last_inc else 0
        content = content[:pos] + '#include "animctrl.h"\n' + content[pos:]
    return content

def _inject_missing_includes_generic(content: str, path: Path) -> str:
    type_to_header = {
        "ActorMarker": "prop.h",
        "AnimCtrl": "animctrl.h",
        "AudioInfo": "audio.h",
    }
    for typ, header in type_to_header.items():
        if re.search(rf'\b{typ}\b', content) and \
                f'#include "{header}"' not in content and \
                f'#include <{header}>' not in content:
            last_inc = None
            for m in re.finditer(r'^#include\b[^\n]*\n', content, re.MULTILINE):
                last_inc = m
            pos = last_inc.end() if last_inc else 0
            content = content[:pos] + f'#include "{header}"\n' + content[pos:]
    return content

# ─────────────────────────────────────────────────────────────────────────────
# Header pass H0 — Patch ultratypes.h to guard all primitive typedefs
#
# ultratypes.h defines the N64 primitive types:
#   s8/u8/s16/u16/s32/u32/s64/u64/f32/f64
# Without guards, including this after <stdint.h> or any NDK header that
# transitively defines the same underlying types causes "redefinition of
# typedef" errors in strict Clang mode.
#
# The fix: wrap every `typedef <base> <alias>;` line in #ifndef / #endif.
# This makes ultratypes.h idempotent and safe to include in any order.
#
# With this pass active, CMakeLists must NOT define -D_ULTRATYPES_H_,
# because suppressing the file entirely is what causes os_thread.h /
# os_message.h to fail with "unknown type name 's32'" etc.
# ─────────────────────────────────────────────────────────────────────────────

_ULTRATYPES_H_MARKER = "/* SH: ultratypes.h typedef guards */"

# The exact set of aliases ultratypes.h defines (order doesn't matter here).
_ULTRATYPES_ALIASES = {
    's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 'f32', 'f64',
}

# Match:  typedef <anything> <alias>;
# where <alias> is one of the known N64 primitive names.
_TYPEDEF_LINE_PAT = re.compile(
    r'^([ \t]*typedef\s+[^\n]+?\b('
    + '|'.join(re.escape(a) for a in _ULTRATYPES_ALIASES)
    + r')\s*;[ \t]*)$',
    re.MULTILINE
)

def _fix_ultratypes_h(decomp_root: Path) -> None:
    # ultratypes.h is typically at include/2.0L/PR/ultratypes.h
    # Some decomps place it directly under include/2.0L/ — try both.
    candidates = [
        decomp_root / "include" / "2.0L" / "PR" / "ultratypes.h",
        decomp_root / "include" / "2.0L" / "ultratypes.h",
        decomp_root / "include" / "ultratypes.h",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        print(f"  [WARN] ultratypes.h not found — H0 skipped (tried: "
              f"{', '.join(str(p) for p in candidates)})")
        return

    content = path.read_text(encoding='utf-8', errors='ignore')

    if _ULTRATYPES_H_MARKER in content:
        print(f"  [OK] ultratypes.h already patched")
        return

    def _guard_typedef(m: re.Match) -> str:
        line  = m.group(1).rstrip()
        alias = m.group(2)
        # Only guard if not already inside a #ifndef block for this alias.
        return (
            f"#ifndef _SH_{alias.upper()}_DEFINED\n"
            f"#define _SH_{alias.upper()}_DEFINED\n"
            f"{line}\n"
            f"#endif"
        )

    patched = _TYPEDEF_LINE_PAT.sub(_guard_typedef, content)

    if patched == content:
        print(f"  [WARN] ultratypes.h: no typedef lines matched — H0 patch skipped")
        return

    # Prepend the marker so idempotency check works on next run.
    patched = _ULTRATYPES_H_MARKER + "\n" + patched

    path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {path} — H0 done")

# ─────────────────────────────────────────────────────────────────────────────
# Header pass H1 — Fix ultra64.h include order
# ─────────────────────────────────────────────────────────────────────────────

_ULTRA64_H_MARKER = "/* SH: gbi.h injected before gu.h */"

_GBI_INJECTION = (
    "\n/* SH: gbi.h injected before gu.h */\n"
    "#ifndef F3DEX_GBI_2\n"
    "#define F3DEX_GBI_2\n"
    "#endif\n"
    "#include <PR/gbi.h>\n"
)

def _fix_ultra64_header(decomp_root: Path) -> None:
    path = decomp_root / "include" / "2.0L" / "ultra64.h"
    if not path.exists():
        print(f"  [FATAL] ultra64.h not found at: {path}")
        return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if _ULTRA64_H_MARKER in content:
        print(f"  [OK] ultra64.h already patched")
        return
    patterns = [
        r'([ \t]*#[ \t]*include[ \t]*[<"]PR/gu\.h[>"][ \t]*\n?)',
        r'([ \t]*#include[ \t]*[<"]PR/gu\.h[>"][^\n]*\n?)',
        r'(#\s*include\s*[<"]PR/gu\.h[>"])',
    ]
    patched = None
    for pat in patterns:
        result = re.sub(pat, _GBI_INJECTION + r'\1', content, count=1)
        if result != content:
            patched = result
            break
    if patched is None:
        patched = _GBI_INJECTION + '\n' + content
    path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {path} — H1 done")

# ─────────────────────────────────────────────────────────────────────────────
# Header pass H2 — Fix structs.h gbi.h include guard problem
# ─────────────────────────────────────────────────────────────────────────────

_STRUCTS_H_MARKER = "/* SH: F3DEX_GBI_2 + _GBI_H_ reset for ultra64.h */"

_STRUCTS_H_INJECTION = """\
/* SH: F3DEX_GBI_2 + _GBI_H_ reset for ultra64.h */
#ifndef F3DEX_GBI_2
#  define F3DEX_GBI_2
#endif
#ifdef _GBI_H_
#  undef _GBI_H_
#endif
"""

def _fix_structs_h(decomp_root: Path) -> None:
    path = decomp_root / "include" / "structs.h"
    if not path.exists():
        print(f"  [FATAL] structs.h not found at: {path}")
        return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if _STRUCTS_H_MARKER in content:
        print(f"  [OK] structs.h already patched")
        return
    patched = re.sub(
        r'(#include\s*[<"]ultra64\.h[>"])',
        _STRUCTS_H_INJECTION + r'\1',
        content, count=1
    )
    if patched == content:
        print(f"  [WARN] structs.h: ultra64.h include not found — patch skipped")
        return
    path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {path} — H2 done")

# ─────────────────────────────────────────────────────────────────────────────
# Header pass H3 — Patch gu.h to self-include gbi.h with F3DEX_GBI_2
# ─────────────────────────────────────────────────────────────────────────────

_GU_H_MARKER = "/* SH: gu.h self-includes gbi.h with F3DEX_GBI_2 */"

_GU_H_INJECTION = """\
/* SH: gu.h self-includes gbi.h with F3DEX_GBI_2 */
/* gu.h uses Gfx/Mtx/LookAt/Hilite from gbi.h but never includes it.        */
/* mbi.h pulls in gbi.h without F3DEX_GBI_2 first, setting _GBI_H_ guard.  */
/* We undef the guard and re-include with F3DEX_GBI_2 so types are defined. */
#ifndef F3DEX_GBI_2
#  define F3DEX_GBI_2
#endif
#ifdef _GBI_H_
#  undef _GBI_H_
#endif
#include <PR/gbi.h>
"""

def _fix_gu_h(decomp_root: Path) -> None:
    path = decomp_root / "include" / "2.0L" / "PR" / "gu.h"
    if not path.exists():
        print(f"  [FATAL] gu.h not found at: {path}")
        return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if _GU_H_MARKER in content:
        print(f"  [OK] gu.h already patched")
        return
    patched = re.sub(
        r'(#ifndef\s+\S+\s*\n#define\s+\S+\s*\n)',
        r'\1' + _GU_H_INJECTION,
        content, count=1
    )
    if patched == content:
        patched = re.sub(
            r'(#define\s+\S+\s*\n)',
            r'\1' + _GU_H_INJECTION,
            content, count=1
        )
    if patched == content:
        patched = _GU_H_INJECTION + content
    path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {path} — H3 done")

# ─────────────────────────────────────────────────────────────────────────────
# Header pass H4 — Patch abi.h for ADPCM_STATE and Acmd
# ─────────────────────────────────────────────────────────────────────────────

_ABI_H_MARKER = "/* SH: abi.h ADPCMFSIZE + Acmd fix */"

_ABI_H_INJECTION = """\
/* SH: abi.h ADPCMFSIZE + Acmd fix */
/* abi.h uses ADPCMFSIZE in typedef but may be included before it's defined. */
#ifndef ADPCMFSIZE
#  define ADPCMFSIZE 16
#endif
/* Acmd is defined in gbi.h via F3DEX_GBI_2 — forward declare if not yet.   */
#ifndef F3DEX_GBI_2
#  define F3DEX_GBI_2
#endif
#ifdef _GBI_H_
#  undef _GBI_H_
#endif
#include <PR/gbi.h>
"""

def _fix_abi_h(decomp_root: Path) -> None:
    path = decomp_root / "include" / "2.0L" / "PR" / "abi.h"
    if not path.exists():
        print(f"  [FATAL] abi.h not found at: {path}")
        return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if _ABI_H_MARKER in content:
        print(f"  [OK] abi.h already patched")
        return
    patched = re.sub(
        r'(#define\s+\S+\s*\n)',
        r'\1' + _ABI_H_INJECTION,
        content, count=1
    )
    if patched == content:
        patched = re.sub(
            r'(#ifndef\s+\S+\s*\n)',
            r'\1' + _ABI_H_INJECTION,
            content, count=1
        )
    if patched == content:
        patched = _ABI_H_INJECTION + content
    path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {path} — H4 done")

# ─────────────────────────────────────────────────────────────────────────────
# Header pass H5 — Patch libaudio.h for ADPCM_STATE, Acmd, Gfx
# ─────────────────────────────────────────────────────────────────────────────

_LIBAUDIO_H_MARKER = "/* SH: libaudio.h abi.h + gbi.h injection */"

_LIBAUDIO_H_INJECTION = """\
/* SH: libaudio.h abi.h + gbi.h injection */
/* libaudio.h uses ADPCM_STATE (abi.h) and Acmd/Gfx (gbi.h F3DEX_GBI_2).  */
#ifndef F3DEX_GBI_2
#  define F3DEX_GBI_2
#endif
#ifdef _GBI_H_
#  undef _GBI_H_
#endif
#include <PR/gbi.h>
#ifndef _ABI_H_
#  include <PR/abi.h>
#endif
"""

def _fix_libaudio_h(decomp_root: Path) -> None:
    candidates = [
        decomp_root / "include" / "2.0L" / "PR" / "libaudio.h",
        decomp_root / "include" / "2.0L" / "libaudio.h",
        decomp_root / "include" / "libaudio.h",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        print(f"  [WARN] libaudio.h not found — H5 skipped (tried: "
              f"{', '.join(str(p) for p in candidates)})")
        return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if _LIBAUDIO_H_MARKER in content:
        print(f"  [OK] libaudio.h already patched")
        return
    patched = re.sub(
        r'(#ifndef\s+\S+\s*\n#define\s+\S+\s*\n)',
        r'\1' + _LIBAUDIO_H_INJECTION,
        content, count=1
    )
    if patched == content:
        patched = re.sub(
            r'(#define\s+\S+\s*\n)',
            r'\1' + _LIBAUDIO_H_INJECTION,
            content, count=1
        )
    if patched == content:
        patched = _LIBAUDIO_H_INJECTION + content
    path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {path} — H5 done")

# ─────────────────────────────────────────────────────────────────────────────
# Per-file processor
# ─────────────────────────────────────────────────────────────────────────────

def process_c_file(path: Path) -> bool:
    try:
        original = path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"  [READ ERROR] {path}: {e}")
        return False

    content = original

    if PREAMBLE_MARKER not in content:
        content = PREAMBLE + content

    content = _fix_ultra64_include(content)
    content = _inject_use_before_def_fwddecls(content)
    content = _fix_array_inits(content)
    content = _fix_static_conflicts(content)
    content = _fix_static_locals(content)
    content = _inject_weak_symbols(content)
    content = _fix_return_type_mismatch(content, path)
    content = _inject_missing_includes(content, path)
    content = _inject_missing_includes_generic(content, path)

    if content == original:
        return False

    try:
        path.write_text(content, encoding='utf-8')
        print(f"  [MODIFIED] {path}")
        return True
    except Exception as e:
        print(f"  [WRITE ERROR] {path}: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    repo_root   = Path(__file__).resolve().parent.parent
    src_dir     = repo_root / "decomp-files" / "src"
    decomp_root = repo_root / "decomp-files"

    print(f"[>] SourceHarmonizer v75.60 — working from repo root: {repo_root}")
    print(f"    Source dir: {src_dir}")
    if not src_dir.exists():
        print(f"[!] Source directory not found: {src_dir}")
        return

    # Header passes — must run before .c file loop
    print("\nRunning header fixes...")
    _fix_ultratypes_h(decomp_root)     # H0 — NEW: guard s8/u8/s32/etc typedefs
    _fix_ultra64_header(decomp_root)   # H1
    _fix_structs_h(decomp_root)        # H2
    _fix_gu_h(decomp_root)             # H3
    _fix_abi_h(decomp_root)            # H4
    _fix_libaudio_h(decomp_root)       # H5

    print("\nProcessing .c files...")
    processed = 0
    modified  = 0
    errors    = 0

    for path in sorted(src_dir.rglob("*.c")):
        processed += 1
        try:
            if process_c_file(path):
                modified += 1
        except Exception as e:
            print(f"  [ERROR] {path.name}: {e}")
            errors += 1

    print(f"\n[+] v75.60 complete.")
    print(f"    Processed : {processed}")
    print(f"    Modified  : {modified}")
    if errors:
        print(f"    Errors    : {errors}")

if __name__ == "__main__":
    main()
