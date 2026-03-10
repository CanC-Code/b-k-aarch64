#!/usr/bin/env python3
"""
SourceHarmonizer v75.57
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

Drop this file at:  runtime/prepare_source.py
It runs before the CMake/ninja build and patches decomp-files/src in-place.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHANGE LOG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v75.57  Add _fix_structs_h (Header pass H2).
        Root cause identified: structs.h line 4 does #include <ultra64.h>.
        ultra64.h includes mbi.h which pulls in gbi.h WITHOUT F3DEX_GBI_2,
        setting gbi.h's include guard (_GBI_H_). Our H1 patch then injects
        #include <PR/gbi.h> before gu.h, but that include is a no-op because
        the guard already fired. Gfx/Mtx/LookAt/Hilite are never defined.
        Fix: patch structs.h to (a) define F3DEX_GBI_2 and (b) undef _GBI_H_
        immediately before its #include <ultra64.h>, forcing gbi.h to fully
        re-parse with F3DEX_GBI_2 active when gu.h is reached.

v75.56  Fix _fix_ultra64_header silent-fail bug: unconditional return in loop
        body meant regex misses went undetected. Added full debug dump of
        ultra64.h, multiple regex patterns, line-by-line fallback, and nuclear
        prepend fallback. Removed bad _fix_gbi_h/_fix_abi_h from v75.55.

v75.55  (bad) Added _fix_gbi_h and _fix_abi_h with incorrect struct stubs.
v75.54  Enhanced _fix_ultra64_header with debug output.
v75.53  Fix path resolution via __file__.
v75.52  Fix ultra64.h include order: inject F3DEX_GBI_2 + gbi.h before gu.h.
v75.51  Add ultra64.h → "ultra64.h" pass. Generalize missing includes.
v75.50  Add missing includes for custom types.
... (prior versions unchanged)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASSES (in order, per .c file)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 0  Compat preamble  — #define / #include block injected once per file
 0a Fix ultra64.h   — #include <ultra64.h> → #include "ultra64.h"
 0b Forward decls   — Inject forward decls for use-before-definition
 1  Array-init       — TYPE var[N] = SYMBOL; → decl + memcpy (GENERIC)
 2  Static conflicts — mismatched static/non-static forward declarations
 3  IDO static norms — strip/split illegal IDO C89 static-local patterns
 4  Weak symbols     — __attribute__((weak)) on non-static function defs
 5  Return type fix  — patch .c files to match header declarations
 6  Missing includes — inject #include for unknown types (e.g., AnimCtrl)

Header passes (run once before .c file loop):
 H1 ultra64.h order — inject F3DEX_GBI_2 + gbi.h before gu.h in ultra64.h
 H2 structs.h       — define F3DEX_GBI_2 + undef _GBI_H_ before ultra64.h
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
/* SourceHarmonizer v75.50 — Android/NDK compatibility preamble             */
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
/* Without this, BOOL(expr) in while/if conditions causes Clang parse errors */
/* when Android system headers have defined BOOL as a type instead of a      */
/* 1-argument macro.                                                          */
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
/* ── End SourceHarmonizer v75.50 preamble ─────────────────────────────── */

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
# Header pass H1 — Fix ultra64.h include order (gbi.h must precede gu.h)
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
    """Patch ultra64.h to include gbi.h before gu.h."""
    candidates = [
        decomp_root / "include" / "2.0L" / "ultra64.h",
        decomp_root / "include" / "ultra64.h",
    ]

    found_path = None
    for p in candidates:
        if p.exists():
            found_path = p
            break

    if found_path is None:
        print("  [WARN] ultra64.h not found in any candidate location")
        return

    content = found_path.read_text(encoding='utf-8', errors='ignore')

    if _ULTRA64_H_MARKER in content:
        print(f"  [OK] ultra64.h already patched at {found_path}")
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
            print(f"  [DEBUG] ultra64.h pattern matched: {pat!r}")
            break

    if patched is None:
        if 'gu.h' in content:
            lines = content.splitlines(keepends=True)
            new_lines = []
            injected = False
            for line in lines:
                if not injected and re.search(r'#\s*include\s*[<"]PR/gu\.h[>"]', line):
                    new_lines.append(_GBI_INJECTION + '\n')
                    injected = True
                new_lines.append(line)
            patched = ''.join(new_lines) if injected else (_GBI_INJECTION + '\n' + content)
        else:
            patched = _GBI_INJECTION + '\n' + content

    found_path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {found_path} — injected F3DEX_GBI_2 + gbi.h before gu.h")

# ─────────────────────────────────────────────────────────────────────────────
# Header pass H2 — Fix structs.h gbi.h include guard problem
# ─────────────────────────────────────────────────────────────────────────────
#
# THE ROOT CAUSE:
#   structs.h line 4:  #include <ultra64.h>
#   ultra64.h pulls in mbi.h, which includes gbi.h WITHOUT F3DEX_GBI_2.
#   gbi.h's include guard (_GBI_H_) is now set.
#   H1 injects #include <PR/gbi.h> before gu.h in ultra64.h, but that
#   include is a complete no-op — the guard already fired.
#   Result: Gfx / Mtx / LookAt / Hilite are never defined → gu.h errors.
#
# THE FIX:
#   Immediately before structs.h's #include <ultra64.h>:
#     1. Define F3DEX_GBI_2  — so gbi.h parses the F3DEX2 type block
#     2. Undef _GBI_H_       — so the include guard doesn't skip the body
#   Now when the chain ultra64.h → mbi.h → gbi.h fires, gbi.h re-parses
#   fully with F3DEX_GBI_2 active, and Gfx/Mtx/LookAt/Hilite are correctly
#   defined before gu.h is reached.

_STRUCTS_H_MARKER = "/* SH: F3DEX_GBI_2 + _GBI_H_ reset for ultra64.h */"

_STRUCTS_H_INJECTION = """\
/* SH: F3DEX_GBI_2 + _GBI_H_ reset for ultra64.h */
/* mbi.h (included by ultra64.h) pulls in gbi.h without F3DEX_GBI_2,        */
/* setting _GBI_H_ before gu.h is reached. We reset both here so gbi.h      */
/* re-parses with F3DEX_GBI_2 active and Gfx/Mtx/LookAt/Hilite are defined. */
#ifndef F3DEX_GBI_2
#  define F3DEX_GBI_2
#endif
#ifdef _GBI_H_
#  undef _GBI_H_
#endif
"""

def _fix_structs_h(decomp_root: Path) -> None:
    """Patch structs.h to force gbi.h re-parse with F3DEX_GBI_2 before ultra64.h."""
    path = decomp_root / "include" / "structs.h"
    if not path.exists():
        print(f"  [WARN] structs.h not found at {path}")
        return

    content = path.read_text(encoding='utf-8', errors='ignore')

    if _STRUCTS_H_MARKER in content:
        print(f"  [OK] structs.h already patched")
        return

    # Insert injection immediately before #include <ultra64.h>
    patched = re.sub(
        r'(#include\s*<ultra64\.h>)',
        _STRUCTS_H_INJECTION + r'\1',
        content,
        count=1
    )

    if patched == content:
        # Try quoted form too
        patched = re.sub(
            r'(#include\s*"ultra64\.h")',
            _STRUCTS_H_INJECTION + r'\1',
            content,
            count=1
        )

    if patched == content:
        print(f"  [WARN] structs.h: could not find #include <ultra64.h> or \"ultra64.h\"")
        print(f"  [WARN] structs.h first 10 lines:")
        for i, line in enumerate(content.splitlines()[:10], 1):
            print(f"    {i:3}: {line}")
        return

    path.write_text(patched, encoding='utf-8')
    print(f"  [PATCHED] {path} — injected F3DEX_GBI_2 + undef _GBI_H_ before ultra64.h")

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

    print(f"[>] SourceHarmonizer v75.57 — {src_dir}")
    if not src_dir.exists():
        print(f"[!] Source directory not found: {src_dir}")
        return

    # Header passes — must run before .c file loop
    _fix_ultra64_header(decomp_root)   # H1: inject gbi.h before gu.h in ultra64.h
    _fix_structs_h(decomp_root)        # H2: force gbi.h re-parse with F3DEX_GBI_2

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

    print(f"[+] v75.57 complete.")
    print(f"    Processed : {processed}")
    print(f"    Modified  : {modified}")
    if errors:
        print(f"    Errors    : {errors}")

if __name__ == "__main__":
    main()
