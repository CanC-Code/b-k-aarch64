import os

gbi_path = "include/ultra64/gbi.h"
with open(gbi_path, "r") as f:
    content = f.read()

# Make sure we don't double patch
if "BKA_LOG_GDL_EMIT" not in content:
    replacement = """
#define BKA_LOG_GDL_EMIT(dl) do { \\
    static int emit_cnt = 0; \\
    if (emit_cnt++ < 20) { \\
        BKA_LOG("gSPDisplayList EMIT target=0x%08X caller_ra=%p", (uint32_t)(dl), __builtin_return_address(0)); \\
    } \\
} while(0)

#define gSPDisplayList(pkt, dl) \\
{ \\
    BKA_LOG_GDL_EMIT(dl); \\
    gDma1p((pkt), G_DL, (dl), 0, 0); \\
}
"""
    content = content.replace("#define gSPDisplayList(pkt, dl) \\", replacement + "\n//#define gSPDisplayList(pkt, dl) \\")
    
    with open(gbi_path, "w") as f:
        f.write(content)
