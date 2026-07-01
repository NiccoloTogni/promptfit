#!/usr/bin/env bash
# Static self-check for the promptfit plugin repo. Does NOT run the LLM loop.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); print('plugin.json OK')"

python3 - <<'PY'
import re
t=open('skills/promptfit/SKILL.md').read()
m=re.match(r'^---\n(.*?)\n---\n', t, re.S); assert m, 'no frontmatter'
assert re.search(r'^name:\s*promptfit\s*$', m.group(1), re.M), 'name'
assert re.search(r'^description:\s*\S', m.group(1), re.M), 'description'
print('SKILL.md frontmatter OK')
PY

for f in optimizer-prompt.md evaluators.md loop-spec.md lineage.md score.py; do
  test -s "skills/promptfit/references/$f" || { echo "missing/empty $f"; exit 1; }
done
echo "references OK"

python3 -c "
import json,glob
fs=sorted(glob.glob('examples/ex*/expected_output.json'))
assert len(fs)==12,len(fs)
for f in fs: json.load(open(f))
print('examples OK', len(fs))
"

# score.py self-test on a fixture
tmp=$(mktemp -d); mkdir -p "$tmp/pred" "$tmp/gold"
printf '{"a":1,"b":2}' > "$tmp/gold/x.json"; printf '{"b":2,"a":1}' > "$tmp/pred/x.json"
out=$(python3 skills/promptfit/references/score.py --mode json_field --pred "$tmp/pred" --gold "$tmp/gold")
echo "$out" | grep -q '"mean": 1.0' || { echo "score.py self-test FAILED: $out"; rm -rf "$tmp"; exit 1; }
rm -rf "$tmp"; echo "score.py OK"

echo "ALL CHECKS PASSED"
