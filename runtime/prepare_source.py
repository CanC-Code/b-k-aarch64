#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.16 — BKA forward declarations after macro block

═══════════════════════════════════════════════════════════════════════════════
LOG 39 — v75.15 ran (861 files processed, 648 modified). One file failed:
  pfsmanager.c — 6 errors, two types
═══════════════════════════════════════════════════════════════════════════════

ROOT CAUSE:

  Error type 1 — "conflicting types for 'BKA_F_xxx_func_8024F224'" (×3):
    Line 391: void func_8024F224(void){
    Note:     previous implicit declaration at line 360: func_8024F224();
    Note:     both expanded via macro → BKA_F_1f86d77d_func_8024F224

    The file calls func_8024F224() at line 360, before its definition at
    line 391. Both go through the BKA #define (now active from after last
    #include). At the call site no prototype is visible for the BKA-renamed
    symbol, so Clang creates an implicit `int`-returning declaration. When
    the actual `void` definition arrives, types conflict.

  Error type 2 — "definition 'func_8024F224' cannot also be an alias" (×3):
    The alias block (bottom of file) tries to create:
      func_8024F224 → alias of BKA_F_xxx_func_8024F224
    But Clang's TU symbol table already has BKA_F_xxx_func_8024F224 with a
    broken (implicit-int) type from error type 1, making the alias invalid.
    Cascade: fix error type 1 and error type 2 disappears automatically.

THE FIX — inject BKA forward declarations immediately after the BKA macros:

  // --- BKA MACROS START ---
  #undef func_8024F224
  #define func_8024F224 BKA_F_xxx_func_8024F224
  // --- BKA MACROS END ---
  
  // --- BKA FORWARD DECLARATIONS ---       ← NEW v75.16
  void func_8024F224(void);                 ← macro expands this to:
                                               void BKA_F_xxx_func_8024F224(void);
  void func_8024F35C(s32 arg0);             ← gives Clang exact prototype
  void func_8024F4AC(void);
  // --- BKA FORWARD DECLARATIONS END ---
  
  [file body — calls and definitions now have visible prototypes]

  // --- BKA ALIASES START ---
  #undef func_8024F224
  __typeof__(BKA_F_xxx_func_8024F224) func_8024F224 __attribute__((weak, alias(...)));
  // --- BKA ALIASES END ---

  With a visible prototype for each BKA-renamed symbol, the call at line 360
  resolves correctly (no implicit int), and the void definition at line 391
  matches exactly. Both errors disappear.

  Signature extraction: for each function in defined_funcs, a regex captures
  the return type and parameter list from the actual definition in the source
  text. This produces an exact prototype rather than a generic stub.

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
            a) macros:         #undef fn / #define fn BKA_F_xxx_fn
            b) fwd decls:      TYPE fn(PARAMS);  (→ TYPE BKA_F_xxx_fn(PARAMS); via macro)
            c) aliases at end: #undef fn / __typeof__(BKA_F_xxx_fn) fn __attribute__((alias))
"""


class SourceHarmonizerV7516:
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
        # Rule A2: plain assign where LHS is a struct/member access (contains -> or .)
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

        # Signature extraction: capture return_type + funcname + params from a definition
        # Used to emit exact forward declarations for BKA-renamed functions.
        # Group 1: everything before the function name (return type + qualifiers)
        # Group 2: function name (substituted per-call with re.escape(fname))
        # Group 3: parameter list
        self._sig_pat_template = (
            r'^([ \t]*[^\n;{}]+?)\b{fname}\s*\(([^{{}}]*?)\)\s*\{{'
        )

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        """Copy fresh source from decomp-files/ — invalidates CMake build cache."""
        print("[>] Preparing v75.16 Workspace...")
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
    def extract_bka_forward_decls(self, clean_content, defined_funcs):
        """
        For each function in defined_funcs, extract its full signature from
        the definition in the source and return a forward declaration string.

        The forward declaration uses the PLAIN function name (not BKA-prefixed).
        When injected after the BKA #define block, the macro expands the plain
        name to the BKA-prefixed symbol, giving Clang the correct prototype.

        Example:
          Source:  void func_8024F224(void) {
          Output:  void func_8024F224(void);
          After BKA macro expansion by preprocessor:
                   void BKA_F_xxx_func_8024F224(void);   ← exact prototype ✓
        """
        fwd_decls = []
        for fname in defined_funcs:
            pat = re.compile(
                r'^([ \t]*[^\n;{}]+?)\b' + re.escape(fname) + r'\s*\(([^{}]*?)\)\s*\{',
                re.MULTILINE | re.DOTALL
            )
            m = pat.search(clean_content)
            if m:
                ret_type = m.group(1).strip()
                params   = re.sub(r'\s+', ' ', m.group(2).strip())
                # Emit: return_type funcname(params);
                fwd_decls.append(f"{ret_type} {fname}({params});")
            else:
                # Fallback: emit a void prototype — safer than no prototype
                fwd_decls.append(f"void {fname}(void);")
        return fwd_decls

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

        # Analysis pass (strip strings/comments for safe scanning)
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
            # Pass 5 — BKA injection (after last #include):
            #
            # a) #undef + #define macros (so our defines override any header macros)
            # b) Forward declarations using plain function names (v75.16 NEW):
            #    These pass through the BKA #defines and give Clang exact prototypes
            #    for every BKA-renamed symbol BEFORE any call site in the file body.
            #    Eliminates implicit-int declarations and "conflicting types" errors.
            # c) Aliases block at end of file

            # Build macros block
            macros_lines = ["", "// --- BKA MACROS START ---"]
            for fn in defined_funcs:
                un = f"BKA_F_{fid}_{fn}"
                macros_lines.append(f"#undef {fn}")
                macros_lines.append(f"#define {fn} {un}")
            macros_lines.append("// --- BKA MACROS END ---")
            macros_block = "\n".join(macros_lines) + "\n"

            # Build forward declarations block (NEW v75.16)
            fwd_decls = self.extract_bka_forward_decls(clean, defined_funcs)
            fwd_lines  = ["// --- BKA FORWARD DECLARATIONS ---"]
            fwd_lines += fwd_decls
            fwd_lines.append("// --- BKA FORWARD DECLARATIONS END ---")
            fwd_block = "\n".join(fwd_lines) + "\n\n"

            # Build aliases block
            aliases_lines = ["", "", "// --- BKA ALIASES START ---"]
            for fn in defined_funcs:
                un = f"BKA_F_{fid}_{fn}"
                aliases_lines.append(f"#undef {fn}")
                aliases_lines.append(
                    f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));"
                )
            aliases_lines.append("// --- BKA ALIASES END ---")
            aliases_block = "\n".join(aliases_lines) + "\n"

            # Find last #include position and insert (macros + fwd_decls) right after
            last_inc = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_inc = m

            inject_block = macros_block + fwd_block

            if last_inc:
                pos = last_inc.end()
                new_content = modified[:pos] + inject_block + modified[pos:] + aliases_block
            else:
                # No #includes: inject at very top
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
        print("[*] Applying v75.16 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.16 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    SourceHarmonizerV7516(target, decomp).run()
