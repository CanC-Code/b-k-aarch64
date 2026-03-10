#!/usr/bin/env python3
"""
SourceHarmonizer v75.53
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

Drop this file at:  runtime/prepare_source.py
It runs before the CMake/ninja build and patches decomp-files/src in-place.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHANGE LOG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
v75.53  Fix path resolution: anchor all paths via __file__ so the script
        works correctly regardless of the caller's working directory.
        Previously, Path("decomp-files") resolved relative to cwd; if the
        workflow cd'd elsewhere (e.g. during gradlew clean), _fix_ultra64_header
        silently failed to locate ultra64.h. Now repo_root is derived from
        Path(__file__).resolve().parent.parent, making all paths absolute
        and cwd-independent. The .c file passes were unaffected previously
        because rglob() produced absolute paths once iterated, but the header
        pass constructs paths directly and was the only thing broken.

v75.52  Fix ultra64.h include order: inject F3DEX_GBI_2 guard + gbi.h
        immediately before #include <PR/gu.h> in ultra64.h at the header
        level. gu.h references Gfx, Mtx, LookAt, Hilite which are defined
        in gbi.h; the original SGI toolchain pulled gbi.h in transitively
        but Clang/NDK does not. Patch is idempotent via marker comment.
        Also fix bug in _inject_missing_includes_generic: guard check was
        f'#{header}' (e.g. '#animctrl.h') instead of the correct
        f'#include "{header}"', causing duplicate inject on every run.

v75.51  Add #include <ultra64.h> → #include "ultra64.h" pass.
        Generalize missing includes logic for any unknown type.
v75.50  Add missing includes for custom types (e.g., AnimCtrl) in .c files.
        If a function uses a type not defined in the file, try to find and
        inject the correct #include.
v75.49  Fix return type mismatch: if a function is declared as `bool` in a header,
        but defined as `int` in a .c file, patch the .c file to match the header.
        This prevents "conflicting types" errors.
v75.48  Fix G_TRI2 and size_t: ensure F3DEX_GBI_2 and stddef.h are included
        before any code that uses them. Inject forward decls after type defs.
v75.47  Generic forward-decl injection for use-before-definition.
        code_1D00.c: audioManager_handleFrameMsg is called at line 428 but
        defined at line 445. No forward decl exists → C89 implicit-int →
        conflicting types with the actual `bool` return type.
        Fix: new Pass 0b scans every .c file for functions that are called
        before their own definition within the same TU, then injects a
        forward decl (matching the definition's return type + params) at the
        top of the file, after the preamble. Works for any file generically.

v75.46  Fix bool.h collision: remove #include <stdbool.h> from preamble,
        defines `bool` as `_Bool`.
        Then decomp-files/include/bool.h's `typedef int bool` would expand to
        `typedef int _Bool`, which Clang rejects ("cannot combine with previous
        'int' declaration specifier").
        Fix: remove `#include <stdbool.h>` from preamble entirely. Instead
        define `__bool_true_false_are_defined 1` — the standard suppression
        guard that stdbool.h sets, which decomp/bool.h checks before typedef.
        This silences the decomp's custom bool.h without pulling in stdbool.h.

v75.45  Fix generic array-init-from-symbol for code_4A6F0.c (and any future
        file with the same pattern).  Previous versions only patched
        code_41460.c by filename; this version uses a regex pass over every
        .c file so `TYPE var[N] = SYMBOL;` is always converted to a
        declaration + memcpy, regardless of which file it appears in.

v75.44  bool/stdbool guard, BOOL macro, min/max/abs undef, forward decls for
        code_1D00.c (AudioInfo / audioManager_handleFrameMsg), return-type
        fix for depthbuffer.c (func_80253400 → bool), array-init fix for
        code_41460.c (was hardcoded — superseded by v75.45 generic pass).

v75.43  bool/int return mismatch fix for func_80253400 in depthbuffer.c.
v75.42  struct AudioInfo forward + function forward decl in code_1D00.c.
v75.24  BOOL macro + extended preamble (MIN/MAX/CLAMP/ABS/ARRAY_COUNT).
v75.23  Rule D: strip `static` before control-flow keywords; Rule C: SPLIT
        static-typed-local init to preserve static storage.
v75.22  Whitelist-based group-2 in inject_weak_attribute (ends blacklist
        whack-a-mole for false-positive weak injection).
v75.21  [^(] added to return-type group to stop matching `if (` / `while (`.
v75.20  [^;] added to params group to stop spanning call statements.
v75.19  Initial working version: preamble (F3DEX_GBI_2 + stddef.h), array
        init → memcpy, static conflict fixes, IDO static normalisation,
        __attribute__((weak)) injection.

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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import re
from pathlib import Path

# Global constants for keywords and storage qualifiers
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
    """Replace #include <ultra64.h> with #include "ultra64.h"."""
    return re.sub(r'#include\s*<ultra64\.h>', '#include "ultra64.h"', content)

# ─────────────────────────────────────────────────────────────────────────────
# Pass 1 — Generic array-init-from-symbol fix
# ─────────────────────────────────────────────────────────────────────────────

_ARRAY_INIT_PAT = re.compile(
    r'^([ \t]*)'                                    # group 1: indent
    r'((?:(?:struct|union|enum)\s+)?'               # group 2: type
    r'[A-Za-z_]\w*(?:\s*\*)*)\s+'
    r'([A-Za-z_]\w*)'                               # group 3: varname
    r'\[(\d+)\]\s*=\s*'                             # group 4: array size
    r'([A-Za-z_]\w*)\s*;',                          # group 5: source symbol
    re.MULTILINE
)

def _fix_array_inits(content: str) -> str:
    """Replace `TYPE var[N] = SYM;` with `TYPE var[N]; memcpy(var, SYM, sizeof(var));`"""
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
    """Return {name: signature_string} for every static function definition."""
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
        # Strategy A: patch existing non-static forward decl → add `static`
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

        # Strategy B: inject a new static forward decl after last #include
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

_P3A = re.compile(        # Rule A: compound assign
    r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
    re.MULTILINE
)
_P3A2 = re.compile(       # Rule A2: member assign
    r'^([ \t]+)static\s+([A-Za-z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
    re.MULTILINE
)
_P3B = re.compile(        # Rule B: implicit-int assign
    r'^([ \t]+)static\s+([A-Za-z_]\w*)\s*=\s*'
    r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
    re.MULTILINE
)
_P3C = re.compile(        # Rule C: typed static local with fn-call init
    r'^([ \t]+)static\s+([^=\n;{}]+?)\b([A-Za-z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
    re.MULTILINE
)

def _fix_static_locals(content: str) -> str:
    # Rule D — must run FIRST
    content = _CTRL_KW_PAT.sub(lambda m: f"{m.group(1)}{m.group(2)}", content)
    # Rule A
    content = _P3A.sub(
        lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}", content
    )
    # Rule A2
    content = _P3A2.sub(
        lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
        content
    )
    # Rule B
    content = _P3B.sub(
        lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};", content
    )
    # Rule C — SPLIT: keep static, split dynamic init
    def _rule_c(m: re.Match) -> str:
        rhs = m.group(4).strip()
        if '(' not in rhs:          # no fn-call → leave alone
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
        # Check context for static/inline/typedef
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
    """Inject forward decls for functions called before their definition."""
    clean = _strip_comments(content)

    # Step 1: collect all definitions with their positions
    defs: dict[str, tuple[int, str, str]] = {}  # name → (pos, rettype, params)
    for m in _FDEF_SCAN.finditer(clean):
        indent = m.group(1)
        # Skip indented definitions (nested / inside another function body)
        if indent:
            continue
        ret_raw = m.group(2).strip()
        name    = m.group(3)
        params  = m.group(4)
        pos     = m.start()

        # Skip if name looks like a keyword, macro, or SDK function
        if name in _NOT_RETURN or name.isupper() or name.startswith('__'):
            continue
        if name.startswith(_SDK_PREFIXES):
            continue
        # Skip static definitions — they don't need forward decls here
        if 'static' in ret_raw.split():
            continue
        # Normalise the return type
        ret = re.sub(r'\s+', ' ', ret_raw).strip()
        if not ret or ret in _NOT_RETURN:
            ret = 'void'

        if name not in defs:
            defs[name] = (pos, ret, params)

    if not defs:
        return content

    # Step 2: find calls that precede the definition
    needed: list[str] = []
    seen_needed: set[str] = set()

    for m in _CALL_SCAN.finditer(clean):
        name = m.group(1)
        if name not in defs:
            continue
        def_pos, ret, params = defs[name]
        if m.start() >= def_pos:
            continue  # call is after definition — fine
        if name in seen_needed:
            continue
        seen_needed.add(name)
        needed.append(f'{ret} {name}{params};')

    if not needed:
        return content

    # Filter out any that already have a forward decl in the file
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

    # Find the position after the AudioInfo type definition
    audioinfo_def = re.search(r'typedef\s+struct\s+AudioInfo_s\s+\{.*?\};', content, re.DOTALL)
    if audioinfo_def:
        insert_at = audioinfo_def.end()
    else:
        # Fallback: insert after the preamble
        end_marker = re.search(r'/\* ── End SourceHarmonizer.*?preamble.*?\*/\n', content)
        if end_marker:
            insert_at = end_marker.end()
        else:
            # Fallback: insert at very top
            insert_at = 0

    return content[:insert_at] + block + content[insert_at:]

# ─────────────────────────────────────────────────────────────────────────────
# Pass 5 — Return type mismatch fix
# ─────────────────────────────────────────────────────────────────────────────

def _fix_return_type_mismatch(content: str, path: Path) -> str:
    """Patch .c files to match return types declared in headers."""
    # Only run for depthbuffer.c
    if path.name != "depthbuffer.c":
        return content

    # Look for func_80253400 defined as int, but declared as bool in core1.h
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
    """Inject #include for unknown types (e.g., AnimCtrl) in .c files."""
    # Only run for anctrl.c
    if path.name != "anctrl.c":
        return content

    # Check if AnimCtrl is used but not defined
    if "AnimCtrl" in content and "#include \"animctrl.h\"" not in content:
        # Find the last #include
        last_inc = None
        for m in re.finditer(r'^#include\b[^\n]*\n', content, re.MULTILINE):
            last_inc = m
        pos = last_inc.end() if last_inc else 0
        content = content[:pos] + '#include "animctrl.h"\n' + content[pos:]

    return content

def _inject_missing_includes_generic(content: str, path: Path) -> str:
    """Scan for unknown types and inject likely includes."""
    type_to_header = {
        "ActorMarker": "prop.h",
        "AnimCtrl": "animctrl.h",
        "AudioInfo": "audio.h",
        # Add more mappings as needed
    }
    for typ, header in type_to_header.items():
        if re.search(rf'\b{typ}\b', content) and \
                f'#include "{header}"' not in content and \
                f'#include <{header}>' not in content:
            # Find the last #include
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

def _fix_ultra64_header(decomp_root: Path) -> None:
    """Patch ultra64.h to define F3DEX_GBI_2 and include gbi.h before gu.h and libaudio.h.

    gu.h uses Gfx, Mtx, LookAt, and Hilite which are defined in gbi.h.
    The original SGI toolchain pulled gbi.h in transitively, but Clang/NDK
    does not. This patch inserts an explicit include with an F3DEX_GBI_2
    guard directly into ultra64.h so the types are always available.
    The patch is idempotent — the marker comment prevents double-injection.
    """
    candidates = [
        decomp_root / "include" / "2.0L" / "ultra64.h",
        decomp_root / "include" / "ultra64.h",
    ]
    for path in candidates:
        if not path.exists():
            continue
        content = path.read_text(encoding='utf-8', errors='ignore')
        if _ULTRA64_H_MARKER in content:
            return  # already patched

        # Patch both libaudio.h and gu.h
        patched = re.sub(
            r'(#include\s*[<"]PR/libaudio\.h[>"]\s*\n\s*#include\s*[<"]PR/gu\.h[>"])',
            (
                f'{_ULTRA64_H_MARKER}\n'
                f'#ifndef F3DEX_GBI_2\n'
                f'#define F3DEX_GBI_2\n'
                f'#endif\n'
                f'#include <PR/gbi.h>\n'
                f'\\1'
            ),
            content
        )
        if patched != content:
            path.write_text(patched, encoding='utf-8')
            print(f"  [PATCHED] {path} — injected F3DEX_GBI_2 + gbi.h before libaudio.h and gu.h")
        else:
            # Fallback: patch gu.h only if libaudio.h is not found
            patched = re.sub(
                r'(#include\s*[<"]PR/gu\.h[>"])',
                (
                    f'{_ULTRA64_H_MARKER}\n'
                    f'#ifndef F3DEX_GBI_2\n'
                    f'#define F3DEX_GBI_2\n'
                    f'#endif\n'
                    f'#include <PR/gbi.h>\n'
                    f'\\1'
                ),
                content
            )
            if patched != content:
                path.write_text(patched, encoding='utf-8')
                print(f"  [PATCHED] {path} — injected F3DEX_GBI_2 + gbi.h before gu.h")
        return
    print("  [WARN] ultra64.h not found — skipping gbi.h injection")

# ─────────────────────────────────────────────────────────────────────────────
# Per-file processor
# ─────────────────────────────────────────────────────────────────────────────

def process_c_file(path: Path) -> bool:
    """Apply all passes to a single .c file. Returns True if the file changed."""
    try:
        original = path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"  [READ ERROR] {path}: {e}")
        return False

    content = original

    # Pass 0 — preamble (idempotent via marker)
    if PREAMBLE_MARKER not in content:
        content = PREAMBLE + content

    # Pass 0a — fix #include <ultra64.h> → #include "ultra64.h"
    content = _fix_ultra64_include(content)

    # Pass 0b — forward decls for use-before-definition (generic)
    content = _inject_use_before_def_fwddecls(content)

    # Pass 1 — generic array-init-from-symbol → declaration + memcpy
    content = _fix_array_inits(content)

    # Pass 2 — static conflict resolution
    content = _fix_static_conflicts(content)

    # Pass 3 — IDO static-local normalisation
    content = _fix_static_locals(content)

    # Pass 4 — weak symbol injection
    content = _inject_weak_symbols(content)

    # Pass 5 — return type mismatch fix
    content = _fix_return_type_mismatch(content, path)

    # Pass 6 — missing includes for custom types
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
    # Anchor paths to the script's own location so they resolve correctly
    # regardless of what directory the caller runs from.
    # Layout:  <repo_root>/runtime/prepare_source.py
    #          <repo_root>/decomp-files/src
    #          <repo_root>/decomp-files/include/2.0L/ultra64.h
    repo_root   = Path(__file__).resolve().parent.parent
    src_dir     = repo_root / "decomp-files" / "src"
    decomp_root = repo_root / "decomp-files"

    print(f"[>] SourceHarmonizer v75.53 — {src_dir}")
    if not src_dir.exists():
        print(f"[!] Source directory not found: {src_dir}")
        return

    # Header pass — must run before .c file loop
    _fix_ultra64_header(decomp_root)

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

    print(f"[+] v75.53 complete.")
    print(f"    Processed : {processed}")
    print(f"    Modified  : {modified}")
    if errors:
        print(f"    Errors    : {errors}")

if __name__ == "__main__":
    main()