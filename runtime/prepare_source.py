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
< truncated lines 195-592 >
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
    """Patch ultra64.h to define F3DEX_GBI_2 and include gbi.h before gu.h.

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
    """Apply all passes to a single .c file.  Returns True if the file changed."""
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