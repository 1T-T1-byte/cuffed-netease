#!/usr/bin/env python3
"""
extract_textures.py — 从原版 Cuffed 模组 jar 中提取贴图
==========================================================
使用方法：
  1. 网易开发者账号 → Modrinth 或 CurseForge 下载 Cuffed-1.20.1-x.x.x.jar
  2. 把 jar 放到本目录，重命名为 Cuffed.jar
  3. 运行：python extract_textures.py
"""

import zipfile, os, sys, urllib.request, json

BASE = os.path.dirname(os.path.abspath(__file__))

# 原模组路径 → 我们资源包路径
MAPPING = {
    'item/handcuffs.png':        'resource_pack/textures/items/handcuffs.png',
    'item/handcuff_key.png':     'resource_pack/textures/items/handcuff_key.png',
    'item/lockpick.png':         'resource_pack/textures/items/lockpick.png',
    'item/padlock.png':          'resource_pack/textures/items/padlock.png',
    'item/key.png':              'resource_pack/textures/items/padlock_key.png',
    'entity/chain_knot.png':     'resource_pack/textures/items/chain.png',
    'block/reinforced_stone.png':'resource_pack/textures/blocks/reinforced_stone.png',
    'block/cell_door_top.png':   'resource_pack/textures/blocks/cell_door.png',
}

JAR_LOCAL = os.path.join(BASE, 'Cuffed.jar')

def download_latest():
    """从 Modrinth 下载最新版 Cuffed jar"""
    print('正在查询 Modrinth 最新版...')
    req = urllib.request.Request('https://api.modrinth.com/v2/project/cuffed/version',
                                  headers={'User-Agent': 'cuffed-extractor/1.0'})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    # 选 1.20.1 系列的最新版本（最稳定的）
    for v in data:
        for f in v['files']:
            if '1.20.1' in f['filename'] and f['filename'].endswith('.jar'):
                url = f['url']
                print(f"下载: {v['version_number']} ({f['filename']})")
                urllib.request.urlretrieve(url, JAR_LOCAL)
                size_mb = os.path.getsize(JAR_LOCAL) / 1024 / 1024
                print(f"已下载 ({size_mb:.2f} MB)")
                return True
    return False

def extract_from_jar():
    """从 jar 中提取贴图到资源包"""
    if not os.path.exists(JAR_LOCAL):
        print('未找到 Cuffed.jar，尝试自动下载...')
        if not download_latest():
            print('下载失败！请手动下载后放到本目录')
            return False
    
    print('打开 jar:', JAR_LOCAL)
    with zipfile.ZipFile(JAR_LOCAL) as z:
        base = 'assets/cuffed/textures/'
        ok, miss = 0, 0
        for src, dst in MAPPING.items():
            full = base + src
            try:
                data = z.read(full)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, 'wb') as f:
                    f.write(data)
                print(f'  ✅ {src} -> {os.path.relpath(dst, BASE)}')
                ok += 1
            except KeyError:
                print(f'  ❌ 缺少: {src}')
                miss += 1
        print(f'\n完成！共提取 {ok}/{len(MAPPING)} 张贴图')
        return miss == 0

if __name__ == '__main__':
    print('='*60)
    print('  Cuffed 贴图提取工具')
    print('='*60)
    if extract_from_jar():
        print('\n🎉 贴图已替换！现在可以直接打开网易MC测试新贴图')
    else:
        sys.exit(1)