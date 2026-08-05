#!/usr/bin/env python3
"""
push_to_github.py — 通过 GitHub Contents API 批量推送文件
==========================================================
不走 git 协议（github.com 可能被网络限制），改用 api.github.com。
"""
import os, json, base64, urllib.request, urllib.error

TOKEN = os.environ.get("GH_TOKEN", "")
OWNER = "1T-T1-byte"
REPO = "cuffed-netease"
BRANCH = "main"
BASE = os.path.dirname(os.path.abspath(__file__))

# 要上传的文件（相对路径）
FILES = []
for root, dirs, files in os.walk(BASE):
    rel_root = os.path.relpath(root, BASE)
    # 跳过 git/临时/发布目录
    skip_dirs = {'.git', 'release', '__pycache__'}
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for f in files:
        if f.endswith('.pyc'):
            continue
        if f in ('Cuffed.jar',) or f.startswith('_preview_'):
            continue
        rel = os.path.join(rel_root, f) if rel_root != '.' else f
        FILES.append(rel)

FILES.sort()

def api(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "cuffed-push/1.0")
    body = json.dumps(data).encode() if data else None
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, body, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def upload_file(path, retry=3):
    full = os.path.join(BASE, path)
    with open(full, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode()
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    data = {
        "message": f"add {path}",
        "content": content_b64,
        "branch": BRANCH,
    }
    for attempt in range(retry):
        status, resp = api("PUT", url, data)
        if status in (200, 201):
            return True
        elif status == 422 and attempt < retry - 1:
            print(f"  ⚠️ {path}: {resp.get('message','')[:60]}... 重试")
            continue
        else:
            print(f"  ❌ {path}: HTTP {status} {resp.get('message','')[:80]}")
            return False
    return False

def main():
    if not TOKEN:
        print("❌ 请设置 GH_TOKEN 环境变量")
        return
    print(f"📤 开始推送 {len(FILES)} 个文件到 {OWNER}/{REPO} ...")
    ok = 0
    for i, path in enumerate(FILES, 1):
        mark = "✅" if upload_file(path) else "❌"
        if mark == "✅":
            ok += 1
        print(f"  [{i}/{len(FILES)}] {mark} {path}")
    print(f"\n完成：{ok}/{len(FILES)} 个文件上传成功")

if __name__ == "__main__":
    main()