#!/usr/bin/env bash
# Shared config resolution: project .autocontext/config.json -> global ~/.claude/autocontext.json -> default
# Usage: source this file, then call read_config "key.path" "default_value"

read_config() {
    local key="$1"
    local default="$2"
    python3 -c "
import json, os
key_parts = '${key}'.split('.')
for path in ['.autocontext/config.json', os.path.expanduser('~/.claude/autocontext.json')]:
    try:
        with open(path) as f:
            cfg = json.load(f)
        val = cfg
        for k in key_parts:
            val = val[k]
        if isinstance(val, bool):
            print(str(val).lower())
        elif isinstance(val, list):
            import json as j
            print(j.dumps(val))
        else:
            print(val)
        exit(0)
    except Exception:
        continue
print('${default}')
"
}
