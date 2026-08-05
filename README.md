# 监禁 (Cuffed) - 网易版《我的世界》模组

> 给你的朋友们戴上手铐并关起来！

## ⚖️ 开源声明

- 本项目基于 **LazrProductions** 的 [Cuffed](https://modrinth.com/mod/cuffed)（Java 版）移植/重制，适配网易版《我的世界》（基岩版）
- 原模组协议：**GPL-3.0**
- 本项目同样采用 **GPL-3.0** 协议（见 [LICENSE](LICENSE)）
- 贴图素材来自原 Cuffed 模组
- 原模组下载：https://modrinth.com/mod/cuffed

## 📦 项目结构

```
cuffed-netease/
├── behavior_pack/         # 行为包（物品、方块、配方、脚本）
│   ├── manifest.json
│   ├── pack_icon.png
│   ├── items/             # 物品定义
│   ├── blocks/            # 方块定义
│   ├── recipes/           # 合成配方
│   └── scripts/main.js    # 核心游戏逻辑
├── resource_pack/         # 资源包（纹理、语言）
│   ├── manifest.json
│   ├── pack_icon.png
│   ├── textures/          # 16×16 纹理
│   └── texts/             # 语言文件
├── generate.py            # 生成脚本（重新运行即可全部重建）
└── extract_textures.py    # 从原 Cuffed jar 提取贴图
```

## 🎮 功能列表

| 功能 | 说明 |
|------|------|
| 🔗 **手铐** | 手持手铐右键点击玩家，将其铐住 |
| 🔑 **手铐钥匙** | 右键被铐玩家，解锁 |
| 🧱 **加固石砖** | 高爆炸抗性，只能镐子破坏（需15秒） |
| 🚪 **牢门** | 无法破坏的监狱门 |
| 🔒 **挂锁** | 右键箱子安装挂锁，锁住箱子 |
| 🔑 **挂锁钥匙** | 解锁挂锁箱子 |
| ⛓ **锁链** | 牵住被铐玩家，强制拉向自己 |
| 📍 **开锁器** | 40%几率破坏手铐 |
| 📦 **物品追回** | 对被铐住的玩家右键可打开背包（未实现） |

## 🛠 安装使用

### 方式一：网易开发测试（推荐）
1. 打开 **网易MC Studio**
2. 新建基岩版组件项目
3. 将 `behavior_pack` 和 `resource_pack` 分别导入
4. 点击调试 → 启动游戏测试

### 方式二：打包上传
1. 将 `behavior_pack` 打包为 `.mcpack`（zip 改后缀）
2. 将 `resource_pack` 打包为 `.mcpack`
3. 再打包为 `.mcaddon`（两个mcpack再打一次zip）
4. 登录 [网易MC开发者中心](https://mc.163.com/dev/)
5. 创建组件 → 上传

### 方式三：本地单机安装
1. 找到 Minecraft 存档目录
2. 将行为包放入 `behavior_packs/`，资源包放入 `resource_packs/`
3. 在世界的设置中启用两个包

## 🎨 纹理素材

纹理已从**原 Cuffed 模组**中提取（见 `extract_textures.py`，可自动下载并重新提取）。

想换/补充纹理，也可以用 Agnes API 生成：

```python
# 用 Agnes 生成手铐像素纹理示例
# POST https://apihub.agnes-ai.com/v1/chat/completions
# 模型: agnes-image-2.1-flash
# 提示: "16x16 pixel art handcuffs, Minecraft item style, transparent background"
```

## 🧪 合成配方

| 物品 | 合成方式 |
|------|----------|
| 手铐 × 1 | 铁锭摆成" I I / I / I I" |
| 手铐钥匙 × 1 | 铁锭摆成" I / I / I" |
| 开锁器 × 1 | 铁锭摆成"  I / I / I  " |
| 挂锁 × 1 | 铁锭摆满工作台 |
| 挂锁钥匙 × 1 | 铁锭+金锭纵向排列 |
| 锁链 × 3 | 铁锭纵向排列3格 |
| 加固石砖 × 8 | 石砖围一圈，中间放铁块 |

## 📤 发布指南

### 网易版（中国版）
1. 将 `behavior_pack` 和 `resource_pack` 分别打包为 `.mcpack`
2. 上传到 [网易MC开发者中心](https://mc.163.com/dev/)
3. 在组件简介中注明：*基于 Cuffed (GPL-3.0) 重制，源码见本仓库*

### 国际版（可选）
将两个包再合打包为 `.mcaddon` 即可在基岩版直接导入。

## 🐾 来自 WoWo

一一自己开发的模组，免费发布，不卖钻石！
希望网易上的免费优质模组越来越多，大家一起加油！
有问题随时找我改！
