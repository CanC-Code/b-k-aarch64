#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.15 — Fix BKA macro injection ordering

═══════════════════════════════════════════════════════════════════════════════
LOG 38 CONFIRMED: v75.14 ran (line 525-530 of log):
  "[>] Preparing v75.14 Workspace..."
  "[+] v75.14 Complete. Files Processed: 861  Files Modified: 648"
═══════════════════════════════════════════════════════════════════════════════

ROOT CAUSE — code_1D00.c (only failing file; all 861 others compiled clean):

  Error: use of undeclared identifier 'BKA_F_674a416b_audioManager_getThread_PAL'
         did you mean 'BKA_F_674a416b_audioManager_getThread'?

  Failing line (684):
    __typeof__(BKA_F_674a416b_audioManager_getThread_PAL)
      audioManager_getThread_PAL __attribute__((weak, alias(...)));

  Clang note: 'BKA_F_674a416b_audioManager_getThread' declared at line 645:
    OSThread * audioManager_getThread(void){   ← expanded from macro 'audioManager_getThread'
    #define audioManager_getThread BKA_F_674a416b_audioManager_getThread  ← line 12 of file

  What happened (v75.14 structure — macros at file TOP, before #includes):

    Line  1:  // --- BKA MACROS START ---
    Line 12:  #define audioManager_getThread     BKA_F_xxx_audioManager_getThread      ← OUR macro
    Line 13:  #define audioManager_getThread_PAL BKA_F_xxx_audioManager_getThread_PAL  ← OUR macro
    Line 14:  // --- BKA MACROS END ---
    Line 15:  #include "audio.h"   ← HEADER redefines audioManager_getThread_PAL → audioManager_getThread
                                     This OVERRIDES our BKA macro (later #define wins)
    ...
    Line 645: OSThread * audioManager_getThread_PAL(void){
              ↑ preprocessed as: audioManager_getThread (header's override wins)
              ↑ then:            BKA_F_xxx_audioManager_getThread(void){   ← only this symbol defined
    Line 684: __typeof__(BKA_F_xxx_audioManager_getThread_PAL) ...  ← this symbol NEVER defined → ERROR

THE FIX (v75.15) — inject BKA macros AFTER the last #include:

  New file structure:
    #include "audio.h"              ← header defines audioManager_getThread_PAL → audioManager_getThread
    // --- BKA MACROS START ---
    #undef audioManager_getThread_PAL                              ← suppress redefinition warning
    #define audioManager_getThread_PAL BKA_F_xxx_..._PAL          ← OUR macro wins (comes after header)
    #undef audioManager_getThread
    #define audioManager_getThread BKA_F_xxx_audioManager_getThread
    // --- BKA MACROS END ---
    ...
    OSThread * audioManager_getThread_PAL(void){
    ↑ preprocessed as: BKA_F_xxx_audioManager_getThread_PAL(void){  ← symbol IS defined ✓
    ...
    // --- BKA ALIASES START ---
    #undef audioManager_getThread_PAL
    __typeof__(BKA_F_xxx_audioManager_getThread_PAL) audioManager_getThread_PAL
      __attribute__((weak, alias("BKA_F_xxx_audioManager_getThread_PAL")));  ← symbol exists ✓

  The explicit #undef before each #define also prevents -Wmacro-redefinition
  warnings from Clang when the header already defined the same name.

═══════════════════════════════════════════════════════════════════════════════
FULL PASS SUMMARY
═══════════════════════════════════════════════════════════════════════════════
  Pass 1 — Array init          u8 tmp[N] = D_x;              -> __builtin_memcpy
  Pass 2 — Static conflicts
    Strategy A                 non-static forward decl        -> add `static`
    Strategy B                 missing static fwd decl        -> inject after #includes
  Pass 3 — Static local C89 normalisation (Rules A/A2/B/C)
    Rule A   compound-assign   static LVALUE OP= expr;        -> LVALUE OP= expr;
    Rule A2  member plain-asgn static obj->field = call();    -> obj->field = call();
    Rule B   implicit-int init static v = call(); /* cmt */   -> v = call();
    Rule C   typed init        static TYPE v = call();        -> TYPE v = call();
  Pass 4 — BKA exclusion set   static + forward-declared functions excluded
  Pass 5 — BKA macros injected AFTER last #include (v75.15 fix); aliases at end
             Each #define preceded by explicit #undef (prevents redefinition warning)
"""


class SourceHarmonizerV7515:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}

        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }

        # Never rename — called directly from NativeBridge.cpp / C++ layer.
        self.std_c = {
            'main', 'main_no_args',
            'memcpy', 'memset', 'strlen', 'strcpy', 'strcmp',
            'sprintf', 'printf', 'malloc', 'free',
            'sin', 'cos', 'sinf', 'cosf', 'sqrt', 'sqrtf', 'abs', 'fabs'
        }

        self.sdk_prefixes = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon')

        self._storage_quals = {
            'static', 'extern', 'inline', 'const', 'volatile', '__attribute__',
            '__restrict', 'restrict', 'register'
        }
        self._ctrl_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'typedef'
        }

        # ── Pre-compiled Pass 3 patterns ──────────────────────────────────────

        # Rule A: compound-assign, any lvalue
        self._p3a = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
            re.MULTILINE
        )
        # Rule A2: plain assign where LHS contains -> or . (member access = unambiguous statement)
        self._p3a2 = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
            re.MULTILINE
        )
        # Rule B: implicit-int plain assign, runtime RHS, optional trailing comment
        self._p3b = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*'
            r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
            re.MULTILINE
        )
        # Rule C: explicit-type plain assign, runtime RHS, optional trailing comment
        self._p3c = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
            re.MULTILINE
        )

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        """Copy fresh source from decomp-files/ — invalidates CMake build cache."""
        print("[>] Preparing v75.15 Workspace...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    def remove_strings_and_comments(self, text):
        text = re.sub(r'//[^\n]*',          '',   text)
        text = re.sub(r'/\*.*?\*/',         '',   text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    # ─────────────────────────────────────────────────────────────────────────
    def find_static_definitions(self, clean_content):
        """Returns {func_name -> signature} for every static function definition."""
        static_funcs = {}
        pat = re.compile(
            r'\bstatic\b([^;{}]*?\b([a-zA-Z_]\w*)\s*\([^{}]*?\))\s*\{',
            re.DOTALL
        )
        for m in pat.finditer(clean_content):
            name = m.group(2)
            if name not in self.c_keywords and name not in static_funcs:
                static_funcs[name] = m.group(1).strip()
        return static_funcs

    # ─────────────────────────────────────────────────────────────────────────
    def has_existing_forward_decl(self, clean_content, func_name):
        """True only if func_name has a real forward declaration (not a call statement)."""
        pat = re.compile(
            r'^([ \t]*(?:[^\n]*?))\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*;',
            re.MULTILINE
        )
        for m in pat.finditer(clean_content):
            prefix = m.group(1)
            if re.search(r'[=!&|^~+\-/%<>?]', prefix):
                continue
            if '(' in prefix:
                continue
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix)
            type_tokens = [t for t in tokens
                           if t not in self._storage_quals
                           and t not in self._ctrl_keywords]
            if type_tokens:
                return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    def fix_static_conflicts(self, content):
        """Pass 2: resolve 'static declaration follows non-static declaration'."""
        clean       = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified       = content
        needs_injected = []

        for func_name, sig in static_defs.items():
            fwd_pat = re.compile(
                r'^([ \t]*)(?!static\b)(\b\S[^\n]*?\b'
                + re.escape(func_name) + r'\s*\([^)]*\)\s*;)',
                re.MULTILINE
            )
            patched = fwd_pat.sub(lambda m: f"{m.group(1)}static {m.group(2)}", modified)
            if patched != modified:
                modified = patched
                continue

            if self.has_existing_forward_decl(clean, func_name):
                continue

            call_pat = re.compile(r'\b' + re.escape(func_name) + r'\s*\(')
            def_pat  = re.compile(
                r'\bstatic\b[^;{}]*?\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*\{',
                re.DOTALL
            )
            call_m = call_pat.search(clean)
            def_m  = def_pat.search(clean)
            if call_m and def_m and call_m.start() < def_m.start():
                needs_injected.append(f"static {sig};")

        if needs_injected:
            block = (
                "// --- SH static forward declarations ---\n"
                + "\n".join(needs_injected) + "\n"
                + "// --- SH static forward declarations end ---\n\n"
            )
            last_inc = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_inc = m
            pos      = last_inc.end() if last_inc else 0
            modified = modified[:pos] + block + modified[pos:]

        return modified

    # ─────────────────────────────────────────────────────────────────────────
    def fix_static_local_c89_patterns(self, content):
        """Pass 3: fix all C89/IDO static-local patterns Clang C99 rejects."""
        content = self._p3a.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}",
            content
        )
        content = self._p3a2.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
            content
        )
        content = self._p3b.sub(
            lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};",
            content
        )
        def _repl_c(m):
            rhs = m.group(4).strip()
            if '(' not in rhs:
                return m.group(0)
            return f"{m.group(1)}{m.group(2)}{m.group(3)} = {rhs};"
        content = self._p3c.sub(_repl_c, content)
        return content

    # ─────────────────────────────────────────────────────────────────────────
    def find_forward_declared_functions(self, clean_content):
        """Returns names of all forward-declared functions (excluded from BKA)."""
        names = set()
        pat   = re.compile(r'(?<![;{}])\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*;', re.DOTALL)
        for m in pat.finditer(clean_content):
            name = m.group(1)
            if name in self.c_keywords:
                continue
            prefix  = clean_content[:m.start()]
            cut     = max(prefix.rfind(';'), prefix.rfind('{'), prefix.rfind('}'))
            segment = prefix[cut+1:] if cut != -1 else prefix
            tokens  = set(re.findall(r'[a-zA-Z_]\w*', segment))
            if not tokens or 'typedef' in tokens:
                continue
            names.add(name)
        return names

    # ─────────────────────────────────────────────────────────────────────────
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Pass 1 — Array init: u8 tmp[N] = D_x;  ->  __builtin_memcpy
        arr_pat = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+'
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        def _arr_repl(m):
            ts, nm, sz, src = m.group(1), m.group(2), m.group(3), m.group(4)
            return (f"{ts} {nm}[{sz}]; "
                    f"__builtin_memcpy({nm}, {src}, {sz} * sizeof({ts.strip()}));")

        modified = arr_pat.sub(_arr_repl, original_content)

        # Pass 2 — Static/forward-decl conflicts
        modified = self.fix_static_conflicts(modified)

        # Pass 3 — C89/IDO static-local patterns
        modified = self.fix_static_local_c89_patterns(modified)

        # Analysis pass (comments/strings stripped for safe pattern scanning)
        clean = self.remove_strings_and_comments(modified)

        # Pass 4 — Build BKA exclusion set
        static_func_names  = set(self.find_static_definitions(clean).keys())
        forward_decl_names = self.find_forward_declared_functions(clean)
        excluded_names     = static_func_names | forward_decl_names

        fid      = hashlib.md5(file_path.name.encode()).hexdigest()[:8]
        func_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')
        defined_funcs = []

        for match in func_pat.finditer(clean):
            fname     = match.group(1)
            start_idx = match.start()

            if fname in self.c_keywords or fname in self.std_c:
                continue
            if fname.startswith(self.sdk_prefixes):
                continue
            if fname.isupper() or fname.startswith('__'):
                continue
            if fname in excluded_names:
                continue

            pre = clean[:start_idx]
            cut = max(pre.rfind(';'), pre.rfind('}'), pre.rfind('{'))
            seg = pre[cut+1:] if cut != -1 else pre
            if any(k in re.findall(r'[a-zA-Z_]\w*', seg)
                   for k in ('static', 'inline', 'typedef')):
                continue

            defined_funcs.append(fname)

        defined_funcs = list(dict.fromkeys(defined_funcs))

        if not defined_funcs:
            new_content = modified
        else:
            # Pass 5 — BKA macro/weak-alias injection
            #
            # KEY CHANGE v75.15: macros are injected AFTER the last #include, not at
            # the file top. This ensures our #defines override any same-named macros
            # from headers (the C preprocessor uses last-definition-wins semantics).
            #
            # Each #define is preceded by an explicit #undef to suppress
            # -Wmacro-redefinition warnings when a header already defined that name.
            #
            # Example for audioManager_getThread_PAL in code_1D00.c:
            #   Header defines: audioManager_getThread_PAL -> audioManager_getThread
            #   Our injection:  #undef audioManager_getThread_PAL
            #                   #define audioManager_getThread_PAL BKA_F_xxx_..._PAL
            #   Function def:   audioManager_getThread_PAL(void){
            #                -> BKA_F_xxx_audioManager_getThread_PAL(void){  ✓ defined
            #   Alias:          __typeof__(BKA_F_xxx_audioManager_getThread_PAL) ...  ✓ works

            macros_lines = ["", "// --- BKA MACROS START ---"]
            for fn in defined_funcs:
                un = f"BKA_F_{fid}_{fn}"
                macros_lines.append(f"#undef {fn}")
                macros_lines.append(f"#define {fn} {un}")
            macros_lines.append("// --- BKA MACROS END ---")
            macros_lines.append("")
            macros_block = "\n".join(macros_lines) + "\n"

            aliases_lines = ["", "", "// --- BKA ALIASES START ---"]
            for fn in defined_funcs:
                un = f"BKA_F_{fid}_{fn}"
                aliases_lines.append(f"#undef {fn}")
                aliases_lines.append(
                    f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));"
                )
            aliases_lines.append("// --- BKA ALIASES END ---")
            aliases_block = "\n".join(aliases_lines) + "\n"

            # Find last #include in modified content and insert macros right after it
            last_inc = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_inc = m

            if last_inc:
                pos = last_inc.end()
                new_content = modified[:pos] + macros_block + modified[pos:] + aliases_block
            else:
                # No #includes: macros go at the very top
                new_content = macros_block + modified + aliases_block

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.stats["changes_made"] += 1

    # ─────────────────────────────────────────────────────────────────────────
    def run(self):
        if not self.decomp_path.exists():
            print(f"[!] Error: decompilation path '{self.decomp_path}' not found.")
            return
        self.setup_workspace()
        print("[*] Applying v75.15 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.15 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    SourceHarmonizerV7515(target, decomp).run()
