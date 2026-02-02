import os
import shutil
import re
import hashlib

class SourceHarmonizerV47_1:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        self.func_signatures = {} 
        self.var_declarations = {} 
        self.discovered_types = set()
        self.sdk_defined_types = set()  # Track types already in SDK headers
        
        # Comprehensive list of SDK types that MUST NOT be redeclared as opaque structs
        self.reserved_types = {
            'u32', 's32', 'u16', 's16', 'u8', 's8', 'f32', 'f64', 'u64', 's64',
            'Vtx', 'Mtx', 'Gfx', 'Acmd', 'OSIntMask', 'OSPri', 'OSMesgQueue',
            'OSPiHandle', 'OSThread', 'OSMesg', 'uintptr_t', 'intptr_t', 'size_t',
            'bool', 'void', 'char', 'int', 'float', 'long', 'short', 'double',
            'ALCSPlayer', 'ALSeq', 'ALEvent', 'ALEventListItem', 'ALEventQueue',
            'ALPlayer', 'ALSeqpConfig', 'ALSynConfig', 'ALVoiceConfig', 'ALInstrument',
            'ALBank', 'ALWave', 'ALEnvelope', 'ALKeyMap', 'ALInstrumentListItem',
            'ALBankFile', 'ALVoice', 'ALSndpConfig', 'ALSndPlayer', 'ALSeqPlayer',
            'ALHeap', 'ALGlobals', 'ALCSeqPlayer', 'ALLink', 'ALCSeq', 'ALSynth',
            # Audio library types
            'N_ALSeqPlayer', 'N_ALVoice', 'N_PVoice',
            # Common C types
            'FILE', 'va_list',
        }
        
        self.reserved_names = {'main', '_start', 'memcpy', 'memset', 'printf', 'sprintf'}

    def get_file_id(self, filepath):
        rel = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel.encode()).hexdigest()[:12]

    def sync_files(self):
        print("  [>] Pass 0: Event-Horizon Sync...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): 
                shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if os.path.exists(source):
                for root, _, files in os.walk(source):
                    rel = os.path.relpath(root, source)
                    dest_dir = os.path.join(target, rel)
                    os.makedirs(dest_dir, exist_ok=True)
                    for f in files: 
                        shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))

    def extract_sdk_types(self):
        """Extract all typedef'd types from SDK headers to avoid conflicts"""
        print("  [>] Pass 0.5: Scanning SDK Headers...")
        
        # Pattern to match typedef struct declarations
        typedef_pattern = re.compile(
            r'typedef\s+struct\s+(\w+)\s*\{[^}]*\}\s*(\w+)\s*;|'  # typedef struct X {...} Y;
            r'typedef\s+struct\s+(\w+)\s+(\w+)\s*;'                # typedef struct X Y;
        )
        
        include_dirs = [
            os.path.join(self.android_path, "include"),
            os.path.join(self.android_path, "include/2.0L"),
            os.path.join(self.android_path, "include/2.0L/PR"),
        ]
        
        for inc_dir in include_dirs:
            if not os.path.exists(inc_dir):
                continue
            for root, _, files in os.walk(inc_dir):
                for f in files:
                    if f.endswith('.h'):
                        path = os.path.join(root, f)
                        try:
                            with open(path, 'r', errors='ignore') as file:
                                content = file.read()
                                for match in typedef_pattern.finditer(content):
                                    # Extract the type name (last non-None group)
                                    groups = [g for g in match.groups() if g]
                                    if groups:
                                        type_name = groups[-1]
                                        self.sdk_defined_types.add(type_name)
                        except:
                            pass
        
        print(f"      Found {len(self.sdk_defined_types)} SDK-defined types")

    def extract_type_from_declaration(self, decl_str):
        """
        Safely extract type names from C declarations.
        Handles cases like:
        - 'SnackerCtlState' from 'SnackerCtlState func(void)'
        - 'AnimSprite*' from 'void func(AnimSprite *arg)'
        - Avoids extracting 'void', 'const', etc.
        """
        # Remove function parameters and common keywords
        decl_str = re.sub(r'\([^)]*\)', '', decl_str)  # Remove (...)
        decl_str = re.sub(r'\bconst\b|\bstatic\b|\bextern\b|\binline\b|\bvoid\b', '', decl_str)
        
        # Extract potential type names (capital letter start, followed by alphanumeric/underscore)
        types = re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', decl_str)
        
        return types

    def map_linkage(self):
        print("  [>] Pass 1: Semantic Type Mapping...")
        
        # More precise function pattern - captures return type separately from name
        func_pat = re.compile(
            r'^(?!.*inline)(?!.*extern)static\s+'
            r'((?:const\s+)?(?:struct\s+)?[\w\*\s]+?)\s+'  # return type (group 1)
            r'([a-zA-Z_]\w*)\s*'                            # function name (group 2)
            r'\(([^\{]*?)\)\s*\{',                          # parameters (group 3)
            re.MULTILINE | re.DOTALL
        )
        
        var_pat = re.compile(
            r'^static\s+(const\s+)?([\w\* ]+)\s+([a-zA-Z_]\w*)(\s*\[[^\]]*\])*\s*([:=;])', 
            re.MULTILINE
        )
        
        # Pattern to find struct/typedef definitions in source files
        struct_pat = re.compile(
            r'typedef\s+struct\s+(\w+)?\s*\{[^}]*\}\s*(\w+)\s*;|'  # typedef struct {...} Name;
            r'struct\s+(\w+)\s*\{',                                 # struct Name {
            re.MULTILINE
        )
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'):
                    continue
                    
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                
                try:
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                        
                        # Extract struct definitions
                        for match in struct_pat.finditer(content):
                            groups = [g for g in match.groups() if g]
                            for type_name in groups:
                                if type_name and type_name not in self.reserved_types:
                                    self.discovered_types.add(type_name)
                        
                        # Extract function signatures
                        for match in func_pat.finditer(content):
                            ret_type = match.group(1).strip()
                            func_name = match.group(2).strip()
                            params = match.group(3).strip() or "void"
                            
                            if func_name in self.reserved_names:
                                continue
                            
                            self.func_signatures[f"{fid}_{func_name}"] = (
                                func_name, 
                                ret_type, 
                                params
                            )
                            
                            # Extract types from return type and parameters
                            for type_candidate in self.extract_type_from_declaration(ret_type + ' ' + params):
                                if (type_candidate not in self.reserved_types and 
                                    type_candidate not in self.sdk_defined_types):
                                    self.discovered_types.add(type_candidate)
                        
                        # Extract variable declarations
                        for is_const, vtype, vname, varr, suffix in var_pat.findall(content):
                            vname = vname.strip()
                            full_type = ("const " if is_const else "") + vtype.strip()
                            self.var_declarations[f"{fid}_{vname}"] = (
                                vname, 
                                full_type, 
                                varr.strip(), 
                                suffix == ';'
                            )
                            
                            # Extract types from variable type
                            for type_candidate in self.extract_type_from_declaration(full_type):
                                if (type_candidate not in self.reserved_types and 
                                    type_candidate not in self.sdk_defined_types):
                                    self.discovered_types.add(type_candidate)
                
                except Exception as e:
                    print(f"      Warning: Error processing {f}: {e}")
        
        print(f"      Discovered {len(self.discovered_types)} custom types")
        print(f"      Found {len(self.func_signatures)} static functions")
        print(f"      Found {len(self.var_declarations)} static variables")

    def promote_linkage(self):
        print("  [>] Pass 2: Global Symbol Promotion...")
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'):
                    continue
                    
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                
                try:
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Replace static functions
                    def func_repl(m):
                        name = m.group(2).strip()
                        if name in self.reserved_names:
                            return m.group(0)
                        
                        ret_type = m.group(1).strip()
                        params = m.group(3).strip()
                        
                        return (
                            f"#undef {name}\n"
                            f"#define GLOBAL_DEF_{fid}_{name}\n"
                            f"__attribute__((visibility(\"protected\"), used)) "
                            f"{ret_type} EH_{fid}_{name}({params}) "
                        )
                    
                    func_pat = re.compile(
                        r'^(?!.*inline)(?!.*extern)static\s+'
                        r'((?:const\s+)?(?:struct\s+)?[\w\*\s]+?)\s+'
                        r'([a-zA-Z_]\w*)\s*'
                        r'\(([^\{]*?)\)\s*\{',
                        re.MULTILINE | re.DOTALL
                    )
                    
                    content = func_pat.sub(func_repl, content)
                    
                    # Replace static variables
                    for key, (vname, vtype, varr, is_bss) in self.var_declarations.items():
                        if not key.startswith(fid):
                            continue
                            
                        attr = '__attribute__((visibility("protected"), used, aligned(8)))'
                        
                        if is_bss:
                            pattern = rf'^static\s+(?:const\s+)?[\w\*\s]+\s+{re.escape(vname)}\s*{re.escape(varr)}\s*;'
                            replacement = (
                                f"#undef {vname}\n"
                                f"#define GLOBAL_DEF_{key}\n"
                                f"{attr} {vtype} EH_{key}{varr};"
                            )
                        else:
                            pattern = rf'^static\s+((?:const\s+)?[\w\*\s]+\s+{re.escape(vname)}\s*{re.escape(varr)}\s*[:=])'
                            replacement = (
                                f"#undef {vname}\n"
                                f"#define GLOBAL_DEF_{key}\n"
                                f"{attr} {vtype} EH_{key}{varr} = "
                            )
                        
                        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    
                    with open(path, 'w') as file:
                        # Include ultra64.h first to define SDK types, then our header
                        file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + content)
                
                except Exception as e:
                    print(f"      Warning: Error promoting linkage in {f}: {e}")

    def generate_header(self):
        print("  [>] Pass 3: Generating Macro-Shielded Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#include <stdbool.h>\n#include <stdint.h>\n#include <stddef.h>\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # Only declare types that aren't in SDK headers
            f.write("/* Forward declarations for custom types */\n")
            for t in sorted(self.discovered_types):
                # Skip if it's in SDK headers or reserved
                if t in self.sdk_defined_types or t in self.reserved_types:
                    continue
                    
                f.write(f"#ifndef TYPE_DEFINED_{t}\n")
                f.write(f"  typedef struct {t} {t};\n")
                f.write(f"  #define TYPE_DEFINED_{t}\n")
                f.write(f"#endif\n")
            
            f.write("\n/* Function declarations */\n")
            for key, (name, ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n")
                f.write(f"  #undef {name}\n")
                f.write(f"  #define {name} EH_{key}\n")
                f.write(f"  extern {ret} EH_{key}({params});\n")
                f.write(f"#endif\n")
            
            f.write("\n/* Variable declarations */\n")
            for key, (vname, vtype, varr, _) in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n")
                f.write(f"  #undef {vname}\n")
                f.write(f"  #define {vname} EH_{key}\n")
                f.write(f"  extern {vtype} EH_{key}{varr};\n")
                f.write(f"#endif\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n")
            f.write("#endif /* HARMONIZED_GLOBALS_H */\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file):
            return
            
        with open(self.cmake_file, 'r') as f:
            content = f.read()
        
        # Remove old harmonizer injection
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v47.1 Event-Horizon (Fixed) ---\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fPIC -fno-common -fvisibility=hidden -flto=thin\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# -----------------------------------------------\n"
        )
        
        with open(self.cmake_file, 'w') as f:
            f.write(content + injection)

    def run(self):
        self.sync_files()
        self.extract_sdk_types()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v47.1 Event-Horizon: Fixed Type Conflicts ---")

if __name__ == "__main__":
    h = SourceHarmonizerV47_1("Android/app/src/main/cpp", "decomp-files")
    h.run()
