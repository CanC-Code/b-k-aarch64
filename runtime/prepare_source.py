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
    # (idempotency: don't re-inject on second run)
    existing_fwds = set()
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\([^)]*\)\s*;', clean):
        existing_fwds.add(m.group(1))
    needed = [decl for decl in needed
              if decl.split('(')[0].split()[-1] not in existing_fwds]

    if not needed:
        return content

    # Check if AudioInfo is used in any forward decl
    needs_audioinfo_include = any('AudioInfo' in decl for decl in needed)

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