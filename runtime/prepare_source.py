#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.17 — K&R-style BKA forward declarations (return type only)

═══════════════════════════════════════════════════════════════════════════════
LOG 40 — v75.16 ran (861 files processed, 648 modified). Two files failed:
  tanktup.c   — 1 error: conflicting types for BKA_F_c88d10b3_func_8038F470
  code_3420.c — 1 error: conflicting types for BKA_F_ed0502ac_chvilegame_new_piece
═══════════════════════════════════════════════════════════════════════════════

ROOT CAUSE (v75.16 regression):

  Error at tanktup.c:55:
    void func_8038F470(ActorMarker *this, s32 arg1, enum chtanktup_leg_e leg_id){
    Previous declaration at line 18:
    void func_8038F470(ActorMarker *this, s32 arg1, enum chtanktup_leg_e leg_id);

  Line 9:  #define func_8038F470 BKA_F_c88d10b3_func_8038F470   ← BKA macro
  Line 18: void func_8038F470(...);                              ← our injected fwd decl
  Line 55: void func_8038F470(...){                              ← original definition

  v75.16 injected forward declarations that included the FULL parameter list,
  extracted from the source via regex. Despite the textual signatures looking
  identical, Clang reports a type conflict. The root cause is that our extraction
  regex captured a full-param signature that after macro expansion differed from
  the definition's expansion in a subtle way — specifically:

  In C99, `enum chtanktup_leg_e` in a forward declaration where the enum is
  INCOMPLETE at that point (not yet defined) differs in type from the same `enum`
  name once it IS complete (at the definition site). The full-param fwd decl
  introduces a reference to the incomplete enum type, which Clang distinguishes
  from the complete type used in the definition.

  code_3420.c has the same issue with `f32 position[3]` — an array parameter
  type that decays to `f32 *` in a declaration but the regex emitted it as `[3]`,
  creating a mismatch with what the definition produces after C parameter adjustment.

THE FIX — K&R-style forward declarations with empty parameter list:

  In C99 (and C11), a function declared with an empty parameter list `()` is
  compatible with any actual parameter list. This is specified in C99 §6.7.5.3 ¶15:
  "a declaration that uses an empty parameter list [...] is compatible with [...] 
  a function that has a parameter type list."

  We emit only the return type with `()`:
    void func_8038F470();
    ↓ (BKA macro expansion by preprocessor)
    void BKA_F_c88d10b3_func_8038F470();

  This:
  • Prevents implicit-int declarations at call sites (return type IS specified)
  • Is compatible with ANY actual parameter list (no param types to conflict)
  • Only requires extracting the return type (simpler, fewer failure modes)
  • Avoids ALL type conflicts from enum completeness, array decay, etc.

  The return type is extracted with a lightweight regex that captures just the
  tokens before the function name on its definition line, stripping storage-class
  qualifiers (static/inline/extern) that must not appear in a standalone fwd decl.

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
  Pass 5 — BKA injection (all after last #include):
            a) macros:     #undef fn / #define fn BKA_F_xxx_fn
            b) fwd decls:  RETTYPE fn();   (K&R empty params — compatible with any sig)
            c) aliases at end: #undef fn / __typeof__(BKA_F_xxx_fn) fn __attribute__((alias))
"""


class SourceHarmonizerV7517:
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
        # Storage-class keywords that must not appear in a standalone forward declaration
        self._strip_from_rettype = ('static', 'inline', 'extern')

        # ── Pre-compiled Pass 3 patterns ──────────────────────────────────────
        self._p3a = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
            re.MULTILINE
        )
        self._p3a2 = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
            re.MULTILINE
        )
        self._p3b = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*'
            r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
            re.MULTILINE
        )
        self._p3c = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
            re.MULTILINE
        )

        # Return-type extraction: capture everything before fname on its definition line
        # Used only to emit `RETTYPE fname();` — params deliberately omitted (K&R style)
        self._rettype_pat_cache = {}

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        """Copy fresh source from decomp-files/ — invalidates CMake build cache."""
        print("[>] Preparing v75.17 Workspace...")
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
    def extract_return_type(self, clean_content, fname):
        """
        Extract the return type from a function definition.

        Only the return type is captured — the parameter list is deliberately
        omitted. We emit K&R-style `RETTYPE fname();` forward declarations,
        which C99 §6.7.5.3 ¶15 guarantees are compatible with any actual
        parameter list. This avoids all type conflicts arising from:
          - Incomplete enum types at fwd-decl time vs complete at definition
          - Array parameter decay (f32 pos[3] vs f32 *pos)
          - Variadic/complex type expressions in params
        """
        if fname not in self._rettype_pat_cache:
            self._rettype_pat_cache[fname] = re.compile(
                r'^([ \t]*[^\n;{}]+?)\b' + re.escape(fname) + r'\s*\(',
                re.MULTILINE
            )
        pat = self._rettype_pat_cache[fname]
        m = pat.search(clean_content)
        if m:
            ret = m.group(1).strip()
            # Strip storage-class qualifiers — invalid in a standalone fwd decl
            for kw in self._strip_from_rettype:
                ret = re.sub(r'\b' + kw + r'\b\s*', '', ret).strip()
            return ret if ret else 'void'
        return 'void'   # safe fallback: void prevents implicit-int, compatible decl

    # ─────────────────────────────────────────────────────────────────────────
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Pass 1 — Array init
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

        # Analysis pass
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
            # Pass 5 — BKA injection after last #include
            #
            # Structure injected immediately after last #include:
            #   // --- BKA MACROS ---
            #   #undef fn             (suppress header macro redefinition warning)
            #   #define fn BKA_F_xxx_fn
            #   ...
            #   // --- BKA MACROS END ---
            #
            #   // --- BKA FORWARD DECLARATIONS ---
            #   RETTYPE fn();         (K&R style — compatible with any param list)
            #   ...                   (via macro → RETTYPE BKA_F_xxx_fn();)
            #   // --- BKA FORWARD DECLARATIONS END ---
            #
            # The K&R-style `RETTYPE fn()` fwd decl:
            #   - Passes through the BKA #define → names the BKA-prefixed symbol
            #   - Provides the return type → prevents implicit-int at call sites
            #   - Has no parameter types → compatible with any actual definition
            #     per C99 §6.7.5.3 ¶15 (avoids enum/array/pointer conflicts)
            #
            # Aliases appended at end of file (unchanged from v75.15):
            #   #undef fn
            #   __typeof__(BKA_F_xxx_fn) fn __attribute__((weak, alias("BKA_F_xxx_fn")));

            macros_lines = ["", "// --- BKA MACROS START ---"]
            fwd_lines    = ["// --- BKA FORWARD DECLARATIONS ---"]

            for fn in defined_funcs:
                un      = f"BKA_F_{fid}_{fn}"
                ret_type = self.extract_return_type(clean, fn)

                macros_lines.append(f"#undef {fn}")
                macros_lines.append(f"#define {fn} {un}")
                # K&R-style: return type + empty params — no param types to conflict
                fwd_lines.append(f"{ret_type} {fn}();")

            macros_lines.append("// --- BKA MACROS END ---")
            fwd_lines.append("// --- BKA FORWARD DECLARATIONS END ---")

            macros_block = "\n".join(macros_lines) + "\n"
            fwd_block    = "\n".join(fwd_lines)    + "\n\n"

            aliases_lines = ["", "", "// --- BKA ALIASES START ---"]
            for fn in defined_funcs:
                un = f"BKA_F_{fid}_{fn}"
                aliases_lines.append(f"#undef {fn}")
                aliases_lines.append(
                    f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));"
                )
            aliases_lines.append("// --- BKA ALIASES END ---")
            aliases_block = "\n".join(aliases_lines) + "\n"

            last_inc = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_inc = m

            inject_block = macros_block + fwd_block

            if last_inc:
                pos = last_inc.end()
                new_content = modified[:pos] + inject_block + modified[pos:] + aliases_block
            else:
                new_content = inject_block + modified + aliases_block

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
        print("[*] Applying v75.17 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.17 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    SourceHarmonizerV7517(target, decomp).run()
