import os, glob
files = glob.glob("include/**/gbi.h", recursive=True)
if not files:
    print("gbi.h not found, skipping patch.")
    exit(0)
gbi_path = files[0]
with open(gbi_path, "r") as f:
    content = f.read()
if "BKA_LOG_GDL_EMIT" not in content:
    replacement = """
#define BKA_LOG_GDL_EMIT(dl) do { \
    static int emit_cnt = 0; \
    if (emit_cnt++ < 20) { \
        BKA_LOG("gSPDisplayList EMIT target=0x%08X caller_ra=%p", (uint32_t)(dl), __builtin_return_address(0)); \
    } \
} while(0)

#define gSTDisplayList(pkt, dl) \
{ \
    BKA_LOG_GDL_EMIT(dl); \
    gDma1p((pkt), G_DL, (dl), 0, 0); \
}
"""
    content = content.replace("#define gSPDisplayList(pkt, dl) \\\n{", replacement + "\n//#define gSTDisplayList(pkt, dl) \\\n//{")
    with open(gbi_path, "w") as f:
        f.write(content)
    print("Patched " + gbi_path)