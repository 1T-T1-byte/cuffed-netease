# 监禁 (Cuffed) — 网易版MC模组 项目记忆

> ⚠️ 换工作空间后，本文件会丢失。
> **完整档案在项目里的 `PROJECT_STATUS.md`（已推送 GitHub）**，请以那份为准。
> 仓库：https://github.com/1T-T1-byte/cuffed-netease

## 项目位置
- 开发目录：`E:\监禁\cuffed-netease\`
- MC Studio 项目：`D:\MCStudioDownload\work\huangjunxi-11-yiyi@outlook.com\Cpp\AddOn\278cfe425e0c464498f9bca0954d980d\`
- GitHub：https://github.com/1T-T1-byte/cuffed-netease
- 乐享页面：entry_id `1957e41031174a9d9e2c338a0de844e1`
- 项目带 git，误操作可回滚

## 技术栈
- 网易版 MC 基岩版（3.9 / 1.21.120+）
- **双脚本并存**：Script API（JS，`@minecraft/server@1.10.0`）+ 网易 ModAPI（Python 2）
- 物品/配方：`format_version 1.21.60`
- **方块：`format_version 1.10.0`**（网易推荐，新版方块需实验性玩法）
- 命名空间：`cuffed:*`

## 物品（8 种）
| ID | 中文名 | 功能 |
|----|--------|------|
| handcuffs | 手铐 | 右键铐人 |
| handcuff_key | 手铐钥匙 | 解锁手铐 |
| lockpick | 开锁器 | 破坏手铐 / 暴力破解密码锁 |
| padlock | 密码锁 | 自设密码上锁（箱子/铁门） |
| key_lock | 挂锁 | 传统钥匙锁 |
| padlock_key | 挂锁钥匙 | 解锁挂锁 |
| chain | 锁链 | 牵引被铐玩家 |
| cell_door | 牢门 | 右键放置**原版铁门** |

## 方块（1 种）
- **reinforced_stone**（加固石砖）：硬度 0.2 + 代码拦截，非管理员挖不动

## 关键设计决策
- **双锁系统**：密码锁（自设密码）/ 挂锁（钥匙），都可作用于箱子 + 铁门
- **暴力破解**：开锁器 → 系统随机 1-9999 → 猜中开锁 / 3 次错锁死 30 分钟
- **牢门 = 原版铁门**：脚本让它可手开（原版只能红石开）
- **权限三层检测**：创造模式 / `isOp()` / `cuffed:admin` tag
- **命令**：`/admin 玩家名`（Python+netease_commands）+ `!admin 玩家名`（JS 后备）
- **加固方块权限实现**：低硬度(0.2s) + `beforeEvents.playerBreakBlock` cancel（硬度过高会导致事件永不触发！）
- 物品分组：`cuffed:items`；方块旧版格式不支持自定义 group

## 已知坑（重要）
- MC Studio 改了文件不会同步回开发目录，需手动复制
- **游戏加载目录是符号链接**指向 MC Studio 项目目录（改项目目录=直接生效）
- **本机 git push 到 github.com 失败**（网络限制）→ 用 `push_to_github.py`（GitHub Contents API）
  - 更新已存在文件**必须带 sha**（脚本已支持）
- GitHub API 不支持中文文件名（Release assets）
- MC Studio "全部升级"只改 manifest 版本号，`git checkout` 可恢复
- 物品 JSON `menu_category.group` 必须有命名空间前缀（`cuffed:items`）
- 1.20+ 配方必须有 `unlock` 字段
- 方块必须用 `format_version 1.10.0`，字段用旧版（destroy_time 等）
- 旧版方块贴图在**资源包根目录 blocks.json** 定义
- `/` 开头输入不走 Script API 的 chatSend（必须用 `!` 前缀或网易自定义指令）
- `generate.py` **已落后于实际代码**，重跑会覆盖手改内容，谨慎使用
- Python + JS 能否共存于同一行为包**尚未完全验证**（用户未反馈）

## 待办
- [ ] 用户测试：加固方块权限、牢门放置/手开/上锁、`/admin` 与 `!admin`
- [ ] 乐享知识库页面待更新（工具未加载，内容已备）
- [ ] generate.py 同步到最新代码
- [ ] 牢门纳入加固保护（需 DynamicProperty 标记）
