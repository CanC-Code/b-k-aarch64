cmake_minimum_required(VERSION 3.20)
project(zstd C)
set(ZSTD_SOURCES
    lib/common/entropy_common.c
    lib/common/error_private.c
    lib/common/fse_decompress.c
    lib/common/pool.c
    lib/common/threading.c
    lib/common/xxhash.c
    lib/common/zstd_common.c
    lib/compress/fse_compress.c
    lib/compress/hist.c
    lib/compress/huf_compress.c
    lib/compress/zstd_compress.c
    lib/compress/zstd_compress_literals.c
    lib/compress/zstd_compress_sequences.c
    lib/compress/zstd_compress_superblock.c
    lib/compress/zstd_double_fast.c
    lib/compress/zstd_fast.c
    lib/compress/zstd_lazy.c
    lib/compress/zstd_ldm.c
    lib/compress/zstd_opt.c
    lib/compress/zstdmt_compress.c
    lib/decompress/huf_decompress.c
    lib/decompress/zstd_ddict.c
    lib/decompress/zstd_decompress.c
    lib/decompress/zstd_decompress_block.c
    lib/dictBuilder/cover.c
    lib/dictBuilder/divsufsort.c
    lib/dictBuilder/fastcover.c
    lib/dictBuilder/zdict.c
)
add_library(libzstd_static STATIC ${ZSTD_SOURCES})
target_include_directories(libzstd_static PUBLIC lib)
target_compile_definitions(libzstd_static PRIVATE ZSTD_LEGACY_SUPPORT=0)
