# 监禁 (Cuffed) — 项目完整档案

> 📅 最后更新：2026-10-04
> 📌 本文档是项目的**唯一完整记录**，换设备后看这一份就能恢复全部上下文。

---

## 一、项目概览

**监禁 (Cuffed)** 是一款**免费开源**的网易版《我的世界》（基岩版）模组。
移植自 Java 版 [Cuffed](https://modrinth.com/mod/cuffed)（作者 LazrProductions，GPL-3.0）。

核心玩法：手铐铐人 → 关进牢房 → 上锁 → 越狱（开锁器暴力破解）

---

## 二、关键位置

| 项目 | 位置 |
|------|------|
| 开发目录 | `E:\监禁\cuffed-netease\` |
| MC Studio 项目 | `D:\MCStudioDownload\work\huangjunxi-11-yiyi@outlook.com\Cpp\AddOn\278cfe425e0c464498f9bca0954d980d\` |
| **GitHub 仓库** | https://github.com/1T-T1-byte/cuffed-netease |
| 乐享知识库页 | entry_id `1957e41031174a9d9e2c338a0de844e1` |
| 乐享 space_id | `e5d74a553d1a478aa67ef9f4c9d85152`（Yiyi的个人知识库） |

**⚠️ 重要：MC Studio 的游戏加载目录是符号链接**
```
C:\Users\Administrator\AppData\Roaming\MinecraftPE_Netease\games\com.netease\behavior_packs\behavior_pack
   ↓ (symlink)
D:\MCStudioDownload\work\huangjunxi-11-yiyi@outlook.com\Cpp\AddOn\278cfe425e0c464498f9bca0954d980d\behavior_pack
```
改 MC Studio 项目目录 = 直接生效，无需额外同步。

---

## 三、技术栈

| 项目 | 值 |
|------|-----|
| 目标平台 | 网易版 MC 基岩版（适配 3.9 / 1.21.120+） |
| 脚本 | **双套并存**：Script API（JavaScript）+ 网易 ModAPI（Python 2） |
| JS 依赖 | `@minecraft/server@1.10.0` + `@minecraft/server-ui@1.3.0` |
| 物品/配方格式 | `format_version: 1.21.60` |
| 方块格式 | `format_version: **1.10.0**`（网易推荐，无需实验性玩法） |
| 命名空间 | `cuffed:*` |

---

## 四、完整文件清单

### 行为包 `behavior_pack/`
```
manifest.json                          包清单（UUID 已固定，勿改）
pack_icon.png                          包图标

scripts/main.js                        ★ 核心逻辑（JS，~600 行）
items/
  handcuffs.json                       手铐
  handcuff_key.json                    手铐钥匙
  lockpick.json                        开锁器
  padlock.json                         密码锁
  key_lock.json                        挂锁
  padlock_key.json                     挂锁钥匙
  chain.json                           锁链
  cell_door.json                       牢门（物品，放置铁门用）
blocks/
  reinforced_stone.json                加固石砖（1.10.0 旧版格式）
loot_tables/blocks/
  reinforced_stone.json                加固石砖掉落表
  cell_door.json                       （遗留，可忽略）
recipes/
  handcuffs.json / handcuff_key.json / lockpick.json
  padlock.json / key_lock.json / padlock_key.json
  chain.json / reinforced_stone.json / cell_door.json
netease_commands/
  cuffed_admin.json                    ★ /admin 指令定义（网易自定义指令）
cuffed_scripts/                        ★ Python ModAPI 脚本
  __init__.py                          模块标记（必须存在）
  modMain.py                           Mod 入口
  CuffedAdminServerSystem.py           监听 /admin 并加标签
```

### 资源包 `resource_pack/`
```
manifest.json
pack_icon.png
blocks.json                            ★ 加固石砖的贴图定义（旧版方块必须）
texts/zh_CN.lang / en_US.lang / languages.json
textures/item_texture.json             物品贴图索引
textures/terrain_texture.json          方块贴图索引
textures/items/*.png                   8 张物品贴图
textures/blocks/*.png                  2 张方块贴图
```

### 项目根目录
```
generate.py                            项目生成器（⚠️ 已落后，见"已知坑"）
extract_textures.py                    从 Cuffed.jar 提取贴图
push_to_github.py                      GitHub API 批量推送（绕过 git 协议）
README.md                              项目说明
LICENSE                                GPL-3.0
PROJECT_STATUS.md                      ★ 本文件
Cuffed.jar                             原模组（贴图来源，勿删）
```

---

## 五、功能系统

### 物品（8 种）

| ID | 名称 | 功能 |
|----|------|------|
| `cuffed:handcuffs` | 手铐 | 右键玩家 → 铐住（缓慢+禁跳+虚弱+挖掘疲劳） |
| `cuffed:handcuff_key` | 手铐钥匙 | 右键被铐玩家 → 解锁 |
| `cuffed:lockpick` | 开锁器 | ①40% 破坏手铐 ②暴力破解密码锁 |
| `cuffed:padlock` | 密码锁 | 右键箱子/铁门 → 自设密码上锁；再右键 → 输入密码解锁 |
| `cuffed:key_lock` | 挂锁 | 右键箱子/铁门 → 传统钥匙锁 |
| `cuffed:padlock_key` | 挂锁钥匙 | 右键 → 解开挂锁 |
| `cuffed:chain` | 锁链 | 右键被铐玩家 → 牵引（拉向自己） |
| `cuffed:cell_door` | 牢门 | 右键方块上方 → 放置**原版铁门**（两格高） |

### 方块（1 种）
| ID | 名称 | 特性 |
|----|------|------|
| `cuffed:reinforced_stone` | 加固石砖 | 硬度 0.2（代码层拦截，非管理员挖不动） |

### 双锁系统

| | 🔐 密码锁 | 🔑 挂锁 |
|---|---------|--------|
| 上锁 | 玩家**自设密码**（1-9999） | 直接锁 |
| 解锁 | 输入密码 | 挂锁钥匙 |
| 暴力破解 | ✅ 开锁器猜数字 | ❌ |
| 适用 | 箱子 + 铁门 | 箱子 + 铁门 |

### 暴力破解规则
- 系统**随机生成**一个 1-9999 的数字（与真实密码无关）
- 破解者猜中 → 开锁成功
- 猜错 3 次 → **锁死 30 分钟**（36000 ticks）
- 30 分钟后自动解锁可再试

### 牢门（原版铁门实现）
- 用 `cuffed:cell_door` 物品右键方块上方 → 放置双格高铁门
- **空手右键铁门可开关**（脚本模拟，原版铁门只能红石开）
- 支持上锁（锁数据存在铁门**下半部分**）

### 管理员权限

**三层检测**：创造模式 / `isOp()` / `cuffed:admin` 标签

**权限命令**（两种都可用）：
```
/admin 玩家名        ← 网易自定义指令（Python 实现，有 Tab 补全）
!admin 玩家名        ← 聊天命令（JS 实现，后备方案）
!admin @a            ← 给所有人
```

**权限效果**：非管理员挖不动加固石砖；管理员一挖就破

---

## 六、关键设计决策与技术要点

### 1. 命令系统为什么用 Python
- Mojang Script API 的 `customCommandRegistry` **强制** `namespace:name` 格式 → 无法做纯 `/admin`
- `/` 开头的输入被原版命令系统吃掉，**JS 的 chatSend 事件收不到**
- 网易 `netease_commands`（JSON）+ ModAPI（Python）可以实现**纯 `/admin`** ✅

### 2. 加固方块权限为什么用"低硬度 + 拦截"
❌ **走过的死路**：方块硬度设 6000 秒 → 玩家永远挖不完 → `playerBreakBlock` 事件永不触发 → 权限代码根本不执行

✅ **正确姿势**：
- 方块硬度设 **0.2 秒**（事件能触发）
- `world.beforeEvents.playerBreakBlock` 里，非管理员 `event.cancel = true`
- 管理员放行 → 0.2 秒即破

### 3. 铁门方块状态名
```js
BlockPermutation.resolve("minecraft:iron_door", {
    "minecraft:cardinal_direction": "north",   // 朝向
    "minecraft:vertical_half": "lower"          // 上半/下半
})
// 开合状态用 open_bit
```
⚠️ 状态名若不对会抛异常（已 catch，会提示"放置失败"）

### 4. 锁数据存储位置
- 箱子 → 存在箱子自身
- 铁门 → 统一存在**下半部分**（`getLockHost()` 函数）
- 用方块 DynamicProperty（`cuffed:password_locked` / `cuffed:chest_owner` / `cuffed:password` / `cuffed:brute_attempts` / `cuffed:brute_locked_until_tick`）

---

## 七、已知坑（踩过的雷，别再踩）

### 物品 JSON
- ❌ `menu_category.group: "cuffed"` → 报 `must be prefixed with a namespace`
- ✅ 必须写 `"cuffed:items"`（`namespace:value` 格式）
- ✅ 1.20+ 配方必须有 `unlock` 字段

### 方块 JSON
- ❌ `format_version: 1.21.x` → 报 `Unexpected version`（新版方块需实验性玩法）
- ✅ 必须用 **1.10.0**（网易推荐）
- ❌ `menu_category.group` 会被引擎拼 `minecraft:` 前缀 → `minecraft:cuffed:blocks` 双重冒号报错
- ✅ 用 `category` + `register_to_creative_menu`，**不设 group**
- ✅ 旧版字段：`destroy_time` / `explosion_resistance` / `map_color`(十六进制) / `loot`(字符串路径)
- ✅ 旧版方块贴图在**资源包根目录的 `blocks.json`** 定义

### 命令
- ❌ JS 的 `chatSend` 收不到 `/` 开头的输入
- ✅ 用 `!` 前缀 或 网易 `netease_commands` + Python

### 权限控制
- ❌ 高硬度方块 + 破坏事件 = 事件永不触发（死锁）
- ✅ 低硬度 + before 事件 cancel

### 工具/流程
- MC Studio 改了文件不会同步回开发目录，需手动复制
- MC Studio "全部升级"按钮只改 manifest 版本号 → `git checkout` 可恢复
- GitHub API **不支持中文文件名**（Release assets 会变 `Cuffed_._v1.0`）→ 用 ASCII 命名
- `generate.py` 重跑会保留已有 UUID（读取现有 manifest），且不覆盖已有贴图
- ⚠️ **`generate.py` 已经落后于实际代码**（不含 cell_door 改造、Python 脚本、密码锁逻辑），重跑会覆盖手改内容，**谨慎使用**

---

## 八、GitHub 推送方法（重要）

**本机 git push 到 github.com 会失败**（网络限制，但 `api.github.com` 可用）。

✅ 用 `push_to_github.py`（走 GitHub Contents API + base64）：
```bash
cd E:\监禁\cuffed-netease
GH_TOKEN="<token>" python push_to_github.py
```
Token 存在乐享「关于我」页面里。

---

## 九、待测试 / 待办

### 待用户测试验证
- [ ] 加固石砖：管理员一挖就破？普通玩家挖不动？
- [ ] 牢门：能放置？是门形状？空手右键能开关？
- [ ] 密码锁/挂锁能锁住铁门？
- [ ] `/admin 玩家名` 与 `!admin 玩家名` 是否都能用？

### 待办功能
- [ ] 加固石砖的分组问题（旧版方块不支持自定义 group，网易另有 `netease_tab` 机制可试）
- [ ] 牢门目前是原版硬度（可用镐挖），未纳入加固保护（需用 DynamicProperty 标记"这是牢门"）
- [ ] 牢门贴图优化（现在是原版铁门外观）
- [ ] 同步 `generate.py` 到最新代码状态

---

## 十、换设备恢复步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/1T-T1-byte/cuffed-netease.git
   ```
2. **装 MC Studio**，新建/导入项目，把 `behavior_pack` 和 `resource_pack` 放进去
3. **看这份文档**（PROJECT_STATUS.md）+ 乐享知识库页面 → 上下文恢复完毕
4. **改代码** → 用 `push_to_github.py` 推回 GitHub

---

## 十一、网易文档参考链接

| 内容 | 链接 |
|------|------|
| 自定义指令 | https://mc.163.com/dev/mcmanual/mc-dev/mcguide/20-玩法开发/15-自定义游戏内容/9-自定义指令.html |
| 自定义方块 | https://mc.163.com/mcstudio/mc-dev/MCDocs/2-ModSDK模组开发beta/03-自定义游戏内容/05-自定义方块/0-自定义方块概述.html |
| 标签接口 | https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/接口/实体/标签.html |
| 权限接口 | https://dev.mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/接口/玩家/权限.html |
| 世界事件 | https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/事件/世界.html |
| Mod 开发指引 | https://mc.163.com/m/mcstudio/modapi/modkfjjmj.html |

---

## 十二、开源信息

- **协议**：GPL-3.0（见 LICENSE）
- **归属**：基于 LazrProductions 的 Cuffed 重制
- **原模组**：https://modrinth.com/mod/cuffed
- **发布**：GitHub Release v1.0（3 个包：`.mcaddon` / `.mcpack` ×2）
- **用户意愿**：免费发布到网易，给免费模组圈助力 💪
