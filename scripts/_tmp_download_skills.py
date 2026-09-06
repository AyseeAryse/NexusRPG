"""
Загрузка исходников скиллов с прямыми URL.
HTTP 200 + непустое тело = OK. Иначе — запись ошибки, переход к следующей.
"""
import urllib.request
import urllib.error
import json
import time
from pathlib import Path

URLS = {
    "A_skill-creator": "https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md",
    "B_code-review": "https://raw.githubusercontent.com/skillcreatorai/Awesome-Agent-Skills/master/code-review/SKILL.md",
    "C_code-refactoring": "https://raw.githubusercontent.com/skillcreatorai/Awesome-Agent-Skills/master/code-refactoring/SKILL.md",
    "D_webapp-testing": "https://raw.githubusercontent.com/skillcreatorai/Awesome-Agent-Skills/master/webapp-testing/SKILL.md",
    "E_coding-plan": "https://raw.githubusercontent.com/danielmiessler/fabric/main/data/patterns/create_coding_plan/system.md",
}

OUT_DIR = Path(r"D:\NexusRPG-main\scripts\_tmp_skills_raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)

results = {}

for key, url in URLS.items():
    print(f"\n=== {key} ===")
    print(f"URL: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            status = r.status
            ctype = r.headers.get("Content-Type", "")
            body = r.read()
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                text = body.decode("latin-1", errors="replace")
            print(f"  status: {status}, content-type: {ctype}, bytes: {len(body)}")
            if status == 200 and len(text.strip()) > 0:
                out_path = OUT_DIR / f"{key}.md"
                out_path.write_text(text, encoding="utf-8")
                print(f"  ✓ saved to {out_path} ({len(text)} chars)")
                results[key] = {"status": status, "bytes": len(body), "chars": len(text), "path": str(out_path)}
            else:
                print(f"  ✗ FAILED: status={status}, body_len={len(body)}")
                results[key] = {"status": status, "bytes": len(body), "error": "empty body or non-200"}
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"  ✗ FAILED: {type(e).__name__}: {e}")
        results[key] = {"error": f"{type(e).__name__}: {e}"}
    except Exception as e:
        print(f"  ✗ FAILED: {type(e).__name__}: {e}")
        results[key] = {"error": f"{type(e).__name__}: {e}"}
    time.sleep(0.5)

# Save results
results_path = Path(r"D:\NexusRPG-main\scripts\_tmp_download_results.json")
results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
print(f"\n\n=== SUMMARY ===")
for k, v in results.items():
    if "error" in v:
        print(f"  ✗ {k}: {v['error']}")
    else:
        print(f"  ✓ {k}: {v['status']} ({v['chars']} chars)")
print(f"\nResults saved to {results_path}")
