#!/usr/bin/env bash
# Static self-check for the promptfit plugin repo. Does NOT run the LLM loop.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); print('plugin.json OK')"
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); print('marketplace.json OK')"

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
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/pred" "$tmp/gold"
printf '{"a":1,"b":2}' > "$tmp/gold/x.json"; printf '{"b":2,"a":1}' > "$tmp/pred/x.json"
out=$(python3 skills/promptfit/references/score.py --mode json_field --pred "$tmp/pred" --gold "$tmp/gold")
echo "$out" | grep -q '"mean": 1.0' || { echo "score.py self-test FAILED: $out"; exit 1; }
# partial credit: one wrong field of two -> 0.5
printf '{"a":9,"b":2}' > "$tmp/pred/x.json"
out=$(python3 skills/promptfit/references/score.py --mode json_field --pred "$tmp/pred" --gold "$tmp/gold")
echo "$out" | grep -q '"mean": 0.5' || { echo "score.py partial-score FAILED: $out"; exit 1; }
echo "score.py OK"

# regression guard: pointing score.py at the subdir-per-example dataset must NOT look like success
warn=$(python3 skills/promptfit/references/score.py --mode json_field --pred examples --gold examples 2>&1 >/dev/null)
echo "$warn" | grep -q 'WARNING' || { echo "score.py subdir-guard FAILED: expected a WARNING, got: $warn"; exit 1; }
echo "score.py subdir-guard OK"

echo "ALL CHECKS PASSED"
