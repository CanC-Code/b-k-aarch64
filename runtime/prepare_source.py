#!/usr/bin/env python3
import re
from pathlib import Path
from itertools import chain

"""
SourceHarmonizer v75.43 — forward decl after struct + return type mismatch fixes

Changelog v75.43:
- v75.42: struct AudioInfo forward early + function forward decl after struct definition
- New: fix bool/int return type mismatch for func_80253400 in depthbuffer.c
  (header says bool, body says int → change body to bool)
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.43 — Android/NDK compat    */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.43 preamble is ACTIVE"

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#include <stddef.h>
#include <stdbool.h>   /* SourceHarmonizer: use native _Bool on Android NDK */

#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#ifdef abs
#undef abs
#endif

#ifndef BOOL
#define BOOL(x) (!!(x))
#endif

#ifndef TRUE
#define TRUE 1
#endif
#ifndef FALSE
#define FALSE 0
#endif

#ifndef ABS
#define ABS(x) ((x) < 0 ? -(x) : (x))
#endif
#ifndef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))
#endif
#ifndef MAX
#define MAX(a,b) ((a) > (b) ? (a) : (b))
#endif
#ifndef CLAMP
#define CLAMP(x,lo,hi) ((x) < (lo) ? (lo) : (x) > (hi) ? (hi) : (x))
#endif
#ifndef ARRAY_COUNT
#define ARRAY_COUNT(x) (sizeof(x) / sizeof((x)[0]))
#endif

/* ──────────────────────────────────────────────── */
/* End compat block v75.43                          */
/* ──────────────────────────────────────────────── */
"""

def count_ifdef_endif(content: str) -> tuple[int, int, bool]:
    ifs = len(re.findall(r'(?m)^#ifndef\s', content))
    endifs = len(re.findall(r'(?m)^#endif', content))
    balanced = endifs >= ifs
    return ifs, endifs, balanced


def harmonize_string_h(file_path: Path, content: str) -> tuple[str, bool]:
    if re.search(r'extern\s*"C"\s*{', content, re.IGNORECASE | re.DOTALL):
        print(f"  [STRING_H SKIP] Already has extern \"C\" → {file_path.name}")
        return content, False

    if_count, endif_count, balanced = count_ifdef_endif(content)

    if not balanced:
        print(f"  [STRING_H WARN] Unbalanced guard ({if_count}/{endif_count}) → attempting repair")

    last_endif_matches = list(re.finditer(r'(?m)^#endif\b.*?$', content))
    if not last_endif_matches:
        print(f"  [STRING_H WARN] No #endif found → appending block")
        insert_pos = len(content)
    else:
        insert_pos = last_endif_matches[-1].start()

    insert_text = """
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.43 – C++ / NDK compatibility  */
/* ──────────────────────────────────────────────── */

#ifdef __cplusplus
extern "C" {
#endif

"""

    new_content = content[:insert_pos] + insert_text + content[insert_pos:]

    new_content = re.sub(
        r'(#endif\s*(?:/\*.*?\*/)?\s*$)',
        r'#ifdef __cplusplus\n}\n#endif\n\1',
        new_content,
        flags=re.DOTALL | re.MULTILINE,
        count=1
    )

    print(f"  [STRING_H FIXED] Inserted extern \"C\" guard → {file_path.name}")
    return new_content, True


def guard_custom_bool_h(file_path: Path, content: str) -> tuple[str, bool]:
    """Robust line-based guard insertion for bool.h"""
    if '__bool_true_false_are_defined' in content:
        print(f"  [BOOL_H SKIP] Already guarded → {file_path.name}")
        return content, False

    if 'typedef int bool' not in content:
        print(f"  [BOOL_H NO MATCH] No 'typedef int bool' found → {file_path.name}")
        return content, False

    lines = content.splitlines(keepends=True)
    new_lines = []
    guard_inserted = False
    guard_end_inserted = False

    for line in lines:
        stripped = line.strip()

        if 'typedef int bool' in stripped and not guard_inserted:
            new_lines.append('#ifndef __bool_true_false_are_defined\n')
            new_lines.append('#define false 0\n')
            new_lines.append('#define true  1\n')
            guard_inserted = True

        new_lines.append(line)

        if stripped == '#endif' and guard_inserted and not guard_end_inserted:
            new_lines.insert(-1, '#endif /* __bool_true_false_are_defined */\n')
            guard_end_inserted = True

    if guard_inserted:
        new_content = ''.join(new_lines)
        print(f"  [BOOL_H FIXED] Inserted compatibility guard around typedef → {file_path.name}")
        return new_content, True

    print(f"  [BOOL_H NO INSERT] Guard not inserted → {file_path.name}")
    return content, False


def fix_implicit_bool_decls(file_path: Path, content: str) -> tuple[str, bool]:
    """
    v75.42: Insert struct AudioInfo; early + function forward decl RIGHT AFTER
    the full struct AudioInfo definition (so AudioInfo is known type).
    """
    if file_path.name != "code_1D00.c":
        return content, False

    if "audioManager_handleFrameMsg" not in content:
        return content, False

    marker = "/* SourceHarmonizer v75.42: forward decl after AudioInfo definition */"
    if marker in content:
        print(f"  [IMPLICIT_DECL SKIP] Already fixed v75.42 → {file_path.name}")
        return content, False

    lines = content.splitlines(keepends=True)

    # 1. Early forward struct decl (after includes)
    include_end = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("#include"):
            include_end = i + 1
        else:
            break

    struct_decl_pos = sum(len(lines[j]) for j in range(include_end))

    struct_forward = """\
/* SourceHarmonizer v75.42: forward struct decl so AudioInfo can be used early */
struct AudioInfo;

"""

    # 2. Try to find end of struct AudioInfo definition
    struct_end_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("}") and ("AudioInfo" in stripped or ";" in stripped or i > 50):
            struct_end_idx = i + 1
            break

    if struct_end_idx == -1:
        # Fallback: before first call
        call_line_idx = -1
        for i, line in enumerate(lines):
            if "audioManager_handleFrameMsg" in line and "(" in line:
                call_line_idx = i
                break
        if call_line_idx == -1:
            print(f"  [IMPLICIT_DECL WARN] No call site or struct end found → {file_path.name}")
            return content, False
        struct_end_idx = call_line_idx

    func_decl_pos = sum(len(lines[j]) for j in range(struct_end_idx))

    func_forward = f"""\
{marker}
bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);

"""

    new_content = (
        content[:struct_decl_pos] +
        struct_forward +
        content[struct_decl_pos:func_decl_pos] +
        func_forward +
        content[func_decl_pos:]
    )

    print(f"  [IMPLICIT_DECL FIXED v75.42] Forward decl AFTER AudioInfo struct → {file_path.name}")
    return new_content, True


def fix_return_type_mismatches(file_path: Path, content: str) -> tuple[str, bool]:
    """
    v75.43: Fix known bool/int return type conflicts
    Currently targets func_80253400 in depthbuffer.c (header = bool, body = int)
    """
    if file_path.name != "depthbuffer.c":
        return content, False

    marker = "/* SourceHarmonizer v75.43: fix bool/int return mismatch */"
    if marker in content:
        print(f"  [RETURN_MISMATCH SKIP] Already fixed → {file_path.name}")
        return content, False

    # Replace the function signature from int → bool
    # We assume the signature is "int func_80253400(void)" or similar
    # This is a simple string replacement – safe as long as no overloads exist
    if "int func_80253400(void)" in content:
        new_content = content.replace(
            "int func_80253400(void)",
            "bool func_80253400(void)",
            1  # only replace the first (definition) occurrence
        )
        print(f"  [RETURN_MISMATCH FIXED v75.43] Changed func_80253400 return to bool → {file_path.name}")
        return new_content + "\n" + marker + "\n", True

    print(f"  [RETURN_MISMATCH NO MATCH] No int func_80253400 found → {file_path.name}")
    return content, False


def insert_preamble_and_fixes(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content
    modified = False

    is_c = file_path.suffix == ".c"
    is_cpp = file_path.suffix in {".cpp", ".hpp", ".cc", ".cxx", ".c++"}
    is_header = file_path.suffix == ".h"
    fname_lower = file_path.name.lower()

    # 1. Preamble for .c files
    if is_c:
        marker = "SourceHarmonizer v75.43 preamble is ACTIVE"
        if marker not in content:
            content = PREAMBLE + "\n" + content
            print(f"  [PREAMBLE+STDBOOL] Inserted in {file_path.name}")
            modified = True

    # 2. Guard custom bool.h
    if is_header and "bool.h" in fname_lower:
        new_content, changed = guard_custom_bool_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 3. Fix implicit / conflicting declarations
    if is_c:
        new_content, changed = fix_implicit_bool_decls(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 4. Fix return type mismatches (new in v75.43)
    if is_c:
        new_content, changed = fix_return_type_mismatches(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 5. string.h fix
    if is_header and "string.h" in fname_lower:
        new_content, changed = harmonize_string_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 6. C++ safety net
    if is_cpp:
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.43: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        inject = '\n// SourceHarmonizer v75.43: force standard headers\n#include <cstddef>\n#include <cstring>\n#include <stdbool.h>\n\n'
        if "SourceHarmonizer v75.43 preamble" in content:
            content = re.sub(
                r'(/\* End compat block v75\.43.*?\*/\s*)',
                rf'\1{inject}',
                content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            content = inject + content

        print(f"  [C++ SAFETY] Applied in {file_path.name}")
        modified = True

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [MODIFIED] {file_path.name}")
            return True
        except Exception as e:
            print(f"Write failed {file_path}: {e}")
            return False

    print(f"  [SKIP] {file_path.name}")
    return False


def main():
    dirs = [
        Path("decomp-files/src"),
        Path("decomp-files/include"),
        Path("Android/app/src/main/cpp"),
    ]

    print("SourceHarmonizer v75.43 running – return type fixes + previous forward decls")

    count = 0
    for d in dirs:
        if not d.is_dir():
            print(f"  Dir missing: {d}")
            continue
        for p in sorted(chain(d.rglob("*.[ch]"), d.rglob("*.[ch]pp"))):
            if insert_preamble_and_fixes(p):
                count += 1

    print(f"\nFinished. Changed {count} files.")
    print("Recommended:")
    print("  git add decomp-files/src/core1/depthbuffer.c decomp-files/src/core1/code_1D00.c")
    print("  git commit -m 'harmonizer v75.43: fix bool/int return mismatch for func_80253400 in depthbuffer.c'")
    print("Verify:")
    print("  grep -A 5 'func_80253400' decomp-files/src/core1/depthbuffer.c")
    print("  grep -C 8 'audioManager_handleFrameMsg' decomp-files/src/core1/code_1D00.c")


if __name__ == "__main__":
    main()