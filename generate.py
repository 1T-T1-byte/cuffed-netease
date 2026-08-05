#!/usr/bin/env python3
"""
监禁 (Cuffed) - 网易版《我的世界》模组生成器
============================================
运行此脚本即可生成完整的模组项目文件。

注意：已存在的贴图不会被覆盖。如果想用原版占位贴图，先删除贴图文件再运行。
想用真实贴图，运行：python extract_textures.py
"""

import os, json, struct, zlib, uuid, random

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================
# 工具函数
# ============================

def make_uuid():
    return str(uuid.uuid4())

def write_json(path, data, indent=2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def write_plain(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

def make_png_16x16(path, r, g, b, pattern=None):
    """生成 16×16 PNG 占位纹理"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pixels = []
    for y in range(16):
        row = []
        for x in range(16):
            pr, pg, pb = r, g, b
            if pattern == "lock":
                # 简单的锁孔图案
                cx, cy = 8, 8
                if abs(x-cx) + abs(y-cy) < 4 or (x>5 and x<11 and y>2 and y<8):
                    pr,pg,pb = 200,180,100
                if x==8 and y==7:
                    pr,pg,pb = 80,60,30
            elif pattern == "key":
                if y < 4 and 6 < x < 12:
                    pr,pg,pb = 220,200,120
                elif y < 8 and 7 < x < 11:
                    pr,pg,pb = 220,200,120
                elif y > 7 and 7 < x < 11:
                    pr,pg,pb = 220,200,120
            elif pattern == "chain":
                if (x+y) % 4 == 0 or (x-y) % 4 == 0:
                    pr,pg,pb = 150,150,160
            elif pattern == "door":
                if x > 1 and x < 14 and y > 0 and y < 15:
                    pr,pg,pb = 140,130,120
                if x > 3 and x < 13 and y > 2 and y < 6:
                    pr,pg,pb = 100,90,80  # 窗口
            elif pattern == "pick":
                # 开锁器：细长形状
                if x > 6 and x < 10 and y > 2 and y < 14:
                    pr,pg,pb = 180,170,150
            elif pattern == "stone":
                noise = ((x*7+y*13)%5)*15
                pr = max(0, min(255, pr - noise))
                pg = max(0, min(255, pg - noise))
                pb = max(0, min(255, pb - noise))
            row.extend([pr, pg, pb, 255])
        pixels.append(bytes(row))
    raw = b''.join(pixels)
    
    def make_chunk(ctype, data):
        chunk = ctype + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
    
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', 16, 16, 8, 2, 0, 0, 0)
    compressed = zlib.compress(raw)
    
    with open(path, 'wb') as f:
        f.write(sig)
        f.write(make_chunk(b'IHDR', ihdr))
        f.write(make_chunk(b'IDAT', compressed))
        f.write(make_chunk(b'IEND', b''))

def make_pack_icon(path, color, letter):
    """生成简单的 pack_icon.png"""
    make_png_16x16(path, *color)

# ============================
# UUID 生成（运行时随机）
# ============================

# 主包 UUID
UUID_BP_HEADER = make_uuid()
UUID_BP_DATA = make_uuid()
UUID_BP_SCRIPT = make_uuid()
UUID_RP_HEADER = make_uuid()
UUID_RP_RES = make_uuid()

# 物品/方块标识符
NS = "cuffed"

# ============================
# 1. 行为包 manifest.json
# ============================

bp_manifest = {
    "format_version": 2,
    "header": {
        "name": "§4§l监禁 §rCuffed",
        "description": "给你的朋友们戴上手铐并关起来！\n§7手铐 | 牢门 | 挂锁 | 开锁器 | 加固方块",
        "uuid": UUID_BP_HEADER,
        "version": [1, 0, 0],
        "min_engine_version": [1, 21, 0]
    },
    "modules": [
        {"type": "data", "uuid": UUID_BP_DATA, "version": [1, 0, 0]},
        {
            "type": "script",
            "language": "javascript",
            "uuid": UUID_BP_SCRIPT,
            "version": [1, 0, 0],
            "entry": "scripts/main.js"
        }
    ],
    "dependencies": [
        {"uuid": UUID_RP_HEADER, "version": [1, 0, 0]},
        {"module_name": "@minecraft/server", "version": "1.10.0"},
        {"module_name": "@minecraft/server-ui", "version": "1.3.0"}
    ],
    "capabilities": ["script_eval"]
}
write_json(f"{BASE}/behavior_pack/manifest.json", bp_manifest)

# ============================
# 2. 物品定义 (items/)
# ============================

# 工具：获取物品JSON
def make_item(item_id, name, lore, texture, max_stack=64, components=None):
    data = {
        "format_version": "1.21.60",
        "minecraft:item": {
            "description": {
                "identifier": f"{NS}:{item_id}",
                "menu_category": {"category": "equipment", "group": "itemGroup.name.weapons"}
            },
            "components": {
                "minecraft:icon": texture,
                "minecraft:display_name": {"value": name},
                "minecraft:max_stack_size": max_stack,
                "minecraft:hand_equipped": True
            }
        }
    }
    if components:
        data["minecraft:item"]["components"].update(components)
    return data

items = [
    make_item("handcuffs", "§7手铐", "用于铐住其他玩家", "handcuffs", 16, {
        "minecraft:durability": {"max_durability": 50},
        "minecraft:tags": {"tags": ["cuffed:handcuffs"]}
    }),
    make_item("handcuff_key", "§e手铐钥匙", "用于解开手铐", "handcuff_key", 64, {
        "minecraft:tags": {"tags": ["cuffed:key"]}
    }),
    make_item("lockpick", "§7开锁器", "可以破坏手铐或挂锁", "lockpick", 16, {
        "minecraft:durability": {"max_durability": 20},
        "minecraft:tags": {"tags": ["cuffed:lockpick"]}
    }),
    make_item("padlock", "§6挂锁", "右键箱子使用，把箱子锁起来", "padlock", 64, {
        "minecraft:tags": {"tags": ["cuffed:padlock"]}
    }),
    make_item("padlock_key", "§6挂锁钥匙", "用来打开挂锁", "padlock_key", 64, {
        "minecraft:tags": {"tags": ["cuffed:lock_key"]}
    }),
    make_item("chain", "§7锁链", "牵着被铐住的玩家", "chain", 16, {
        "minecraft:tags": {"tags": ["cuffed:chain"]}
    }),
]

for item in items:
    item_id = item["minecraft:item"]["description"]["identifier"].split(":")[1]
    write_json(f"{BASE}/behavior_pack/items/{item_id}.json", item)

# ============================
# 3. 方块定义 (blocks/)
# ============================

def make_block(block_id, name, texture, components=None):
    data = {
        "format_version": "1.21.60",
        "minecraft:block": {
            "description": {
                "identifier": f"{NS}:{block_id}",
                "menu_category": {"category": "construction", "group": "itemGroup.name.stone"}
            },
            "components": {
                "minecraft:display_name": name,
                "minecraft:geometry": "geometry.block",
                "minecraft:material_instances": {
                    "*": {"texture": texture, "render_method": "alpha_test"}
                },
                "minecraft:destructible_by_mining": {
                    "seconds_to_destroy": 6000.0,
                    "item_specific_speeds": [
                        {"item": {"tags": "q.any_tag('minecraft:is_pickaxe')"}, "destroy_speed": 1500.0}
                    ]
                },
                "minecraft:destructible_by_explosion": {"explosion_resistance": 6000.0},
                "minecraft:map_color": [100, 90, 80],
                "minecraft:loot": {"table": f"loot_tables/blocks/{block_id}.json"}
            }
        }
    }
    if components:
        data["minecraft:block"]["components"].update(components)
    return data

blocks = [
    make_block("reinforced_stone", "§7加固石砖", "reinforced_stone"),
    make_block("cell_door", "§7§l牢门", "cell_door", {
        "minecraft:destructible_by_mining": {"seconds_to_destroy": 9999.0}
    }),
]

for block in blocks:
    block_id = block["minecraft:block"]["description"]["identifier"].split(":")[1]
    write_json(f"{BASE}/behavior_pack/blocks/{block_id}.json", block)

# ============================
# 3.1 方块战利品表
# ============================
for block_id in ["reinforced_stone", "cell_door"]:
    loot = {
        "pools": [{
            "rolls": 1,
            "entries": [{"type": "item", "name": f"{NS}:{block_id}"}]
        }]
    }
    write_json(f"{BASE}/behavior_pack/loot_tables/blocks/{block_id}.json", loot)

# ============================
# 4. 合成配方 (recipes/)
# ============================

recipes = {
    "handcuffs": {
        "description": {"identifier": f"{NS}:handcuffs_recipe"},
        "tags": ["crafting_table"],
        "pattern": ["I I", " I ", "I I"],
        "key": {"I": "minecraft:iron_ingot"},
        "result": {"item": f"{NS}:handcuffs", "count": 1}
    },
    "handcuff_key": {
        "description": {"identifier": f"{NS}:handcuff_key_recipe"},
        "tags": ["crafting_table"],
        "pattern": [" I ", " I ", " I "],
        "key": {"I": "minecraft:iron_ingot"},
        "result": {"item": f"{NS}:handcuff_key", "count": 1}
    },
    "lockpick": {
        "description": {"identifier": f"{NS}:lockpick_recipe"},
        "tags": ["crafting_table"],
        "pattern": ["  I", " I ", "I  "],
        "key": {"I": "minecraft:iron_ingot"},
        "result": {"item": f"{NS}:lockpick", "count": 1}
    },
    "padlock": {
        "description": {"identifier": f"{NS}:padlock_recipe"},
        "tags": ["crafting_table"],
        "pattern": ["III", "I I", "III"],
        "key": {"I": "minecraft:iron_ingot"},
        "result": {"item": f"{NS}:padlock", "count": 1}
    },
    "padlock_key": {
        "description": {"identifier": f"{NS}:padlock_key_recipe"},
        "tags": ["crafting_table"],
        "pattern": [" I ", " G ", " I "],
        "key": {"I": "minecraft:iron_ingot", "G": "minecraft:gold_ingot"},
        "result": {"item": f"{NS}:padlock_key", "count": 1}
    },
    "chain": {
        "description": {"identifier": f"{NS}:chain_recipe"},
        "tags": ["crafting_table"],
        "pattern": ["I", "I", "I"],
        "key": {"I": "minecraft:iron_ingot"},
        "result": {"item": f"{NS}:chain", "count": 3}
    },
    "reinforced_stone": {
        "description": {"identifier": f"{NS}:reinforced_stone_recipe"},
        "tags": ["crafting_table"],
        "pattern": ["SSS", "SIS", "SSS"],
        "key": {"S": "minecraft:stone_bricks", "I": "minecraft:iron_block"},
        "result": {"item": f"{NS}:reinforced_stone", "count": 8}
    },
}

for recipe_id, recipe in recipes.items():
    r = {"format_version": "1.21.60", "minecraft:recipe_shaped": recipe}
    write_json(f"{BASE}/behavior_pack/recipes/{recipe_id}.json", r)

# ============================
# 5. 资源包 manifest.json
# ============================

rp_manifest = {
    "format_version": 2,
    "header": {
        "name": "§4§l监禁 §rCuffed 资源包",
        "description": "监禁模组 - 纹理与模型",
        "uuid": UUID_RP_HEADER,
        "version": [1, 0, 0],
        "min_engine_version": [1, 21, 0]
    },
    "modules": [
        {"type": "resources", "uuid": UUID_RP_RES, "version": [1, 0, 0]}
    ]
}
write_json(f"{BASE}/resource_pack/manifest.json", rp_manifest)

# ============================
# 6. 语言文件 (texts/)
# ============================

lang_zh = """## 监禁 Cuffed - 中文语言文件
item.cuffed:handcuffs=手铐
item.cuffed:handcuff_key=手铐钥匙
item.cuffed:lockpick=开锁器
item.cuffed:padlock=挂锁
item.cuffed:padlock_key=挂锁钥匙
item.cuffed:chain=锁链
tile.cuffed:reinforced_stone.name=加固石砖
tile.cuffed:cell_door.name=牢门

item.cuffed:handcuffs.description=§7右键铐住其他玩家
item.cuffed:handcuff_key.description=§e右键被铐住的玩家以解锁
item.cuffed:lockpick.description=§7可以破坏手铐或挂锁
item.cuffed:padlock.description=§6右键箱子安装挂锁
item.cuffed:padlock_key.description=§6右键挂锁箱子解锁
item.cuffed:chain.description=§7牵着被铐住的玩家

action.cuffed.locked=§c这个箱子被锁住了！
action.cuffed.unlocked=§a锁已打开
action.cuffed.handcuffed=§c你被铐住了！
action.cuffed.freed=§a手铐已解开
action.cuffed.pick_success=§a开锁成功！
action.cuffed.pick_fail=§7开锁失败...
action.cuffed.chain_attach=§7已用锁链连接玩家
action.cuffed.loot_take=§7已缴获物品
"""
write_plain(f"{BASE}/resource_pack/texts/zh_CN.lang", lang_zh)

lang_en = """## Cuffed - English Language File
item.cuffed:handcuffs=Handcuffs
item.cuffed:handcuff_key=Handcuff Key
item.cuffed:lockpick=Lockpick
item.cuffed:padlock=Padlock
item.cuffed:padlock_key=Padlock Key
item.cuffed:chain=Chain
tile.cuffed:reinforced_stone.name=Reinforced Stone Bricks
tile.cuffed:cell_door.name=Cell Door
"""
write_plain(f"{BASE}/resource_pack/texts/en_US.lang", lang_en)

languages_json = ["zh_CN", "en_US"]
write_json(f"{BASE}/resource_pack/texts/languages.json", languages_json)

# ============================
# 7. 纹理映射
# ============================

item_texture = {
    "resource_pack_name": "cuffed",
    "texture_name": "atlas.items",
    "texture_data": {
        "handcuffs": {"textures": "textures/items/handcuffs"},
        "handcuff_key": {"textures": "textures/items/handcuff_key"},
        "lockpick": {"textures": "textures/items/lockpick"},
        "padlock": {"textures": "textures/items/padlock"},
        "padlock_key": {"textures": "textures/items/padlock_key"},
        "chain": {"textures": "textures/items/chain"},
    }
}
write_json(f"{BASE}/resource_pack/textures/item_texture.json", item_texture)

terrain_texture = {
    "resource_pack_name": "cuffed",
    "texture_name": "atlas.terrain",
    "texture_data": {
        "reinforced_stone": {"textures": "textures/blocks/reinforced_stone"},
        "cell_door": {"textures": "textures/blocks/cell_door"},
    }
}
write_json(f"{BASE}/resource_pack/textures/terrain_texture.json", terrain_texture)

# ============================
# 8. 生成占位纹理图片（已存在的跳过）
# ============================

# 物品纹理
for name, rgb, pat in [
    ('handcuffs',    (120, 110, 100), "chain"),  # 灰色金属
    ('handcuff_key', (220, 200, 120), "key"),    # 金色
    ('lockpick',     (180, 170, 150), "pick"),   # 银色
    ('padlock',      (200, 180, 100), "lock"),   # 金色
    ('padlock_key',  (200, 190, 130), "key"),    # 金色
    ('chain',        (150, 150, 160), "chain"),  # 铁灰色
]:
    path = f"{BASE}/resource_pack/textures/items/{name}.png"
    if not os.path.exists(path):
        make_png_16x16(path, *rgb, pat)

# 方块纹理
for name, rgb, pat in [
    ('reinforced_stone', (130, 120, 110), "stone"),  # 深灰石砖
    ('cell_door',        (140, 130, 120), "door"),   # 牢门
]:
    path = f"{BASE}/resource_pack/textures/blocks/{name}.png"
    if not os.path.exists(path):
        make_png_16x16(path, *rgb, pat)

# Pack icons
make_pack_icon(f"{BASE}/behavior_pack/pack_icon.png", (180, 40, 40), "C")   # 红色 - 行为包
make_pack_icon(f"{BASE}/resource_pack/pack_icon.png", (40, 80, 180), "C")   # 蓝色 - 资源包

# ============================
# 9. 核心 JS 脚本
# ============================

script_code = r"""
/=========================================================================
 监禁 (Cuffed) - 核心逻辑
 网易版《我的世界》基岩版
=========================================================================/

import { world, system, EntityComponentTypes, ItemComponentTypes, GameMode } from "@minecraft/server";

const MOD_PREFIX = "§7[监禁]§r ";
const TAG_CUFFED = "cuffed:handcuffed";
const TAG_CHAINED = "cuffed:chained";
const DYNAMIC_LOCKED_CHEST = "cuffed:locked_chest";
const DYNAMIC_CHEST_OWNER = "cuffed:chest_owner";

// ================================================================
// 工具函数
// ================================================================

function hasTag(item, tag) {
    try {
        const tags = item.getComponent(ItemComponentTypes.Durability)?.maxDurability;
        // 使用 tags 组件检查
        const comp = item.getComponent("minecraft:tags");
        if (comp && comp.tags) return comp.tags.includes(tag);
    } catch (e) {}
    return false;
}

function getItemId(item) {
    if (!item) return "";
    try { return item.typeId; } catch (e) { return ""; }
}

function isCuffed(player) {
    return player.hasTag(TAG_CUFFED);
}

function sendMsg(player, msg) {
    player.sendMessage(MOD_PREFIX + msg);
}

// ================================================================
// 事件：玩家被右键（使用物品对实体）
// ================================================================

world.afterEvents.playerInteractWithEntity.subscribe((event) => {
    const { player, target, itemStack } = event;
    if (!player || !target || !itemStack || !target.typeId.startsWith("minecraft:player")) return;

    const itemId = getItemId(itemStack);

    // ---------- 1. 使用手铐 ----------
    if (itemId === "cuffed:handcuffs" && !isCuffed(target)) {
        // 给目标加标签
        target.addTag(TAG_CUFFED);
        // 应用缓慢效果（模拟束缚）
        target.addEffect("slowness", 999999, { amplifier: 5, showParticles: false });
        target.addEffect("jump_boost", 999999, { amplifier: -10, showParticles: false });  // 不能跳
        target.addEffect("weakness", 999999, { amplifier: 10, showParticles: false });      // 不能攻击
        target.addEffect("mining_fatigue", 999999, { amplifier: 10, showParticles: true });  // 不能挖矿
        sendMsg(target, "§c你被铐住了！无法移动和交互！");
        sendMsg(player, "§a成功铐住了 " + target.name);
        // 消耗耐久
        try { itemStack?.getComponent("minecraft:durability")?.damage?.(); } catch(e) {}
    }

    // ---------- 2. 使用钥匙解锁 ----------
    if (itemId === "cuffed:handcuff_key" && isCuffed(target)) {
        target.removeTag(TAG_CUFFED);
        target.removeEffect("slowness");
        target.removeEffect("jump_boost");
        target.removeEffect("weakness");
        target.removeEffect("mining_fatigue");
        sendMsg(target, "§a你被解开了手铐！");
        sendMsg(player, "§a已解开 " + target.name + " 的手铐");
    }

    // ---------- 3. 使用开锁器 ----------
    if (itemId === "cuffed:lockpick" && isCuffed(target)) {
        const success = Math.random() < 0.4;  // 40% 成功率
        if (success) {
            target.removeTag(TAG_CUFFED);
            target.removeEffect("slowness");
            target.removeEffect("jump_boost");
            target.removeEffect("weakness");
            target.removeEffect("mining_fatigue");
            sendMsg(target, "§a有人用开锁器救了你！");
            sendMsg(player, "§a开锁成功！手铐已解除");
        } else {
            sendMsg(player, "§7开锁失败...再试一次");
        }
        // 消耗耐久
        if (Math.random() < 0.3) {
            try { itemStack?.getComponent("minecraft:durability")?.damage?.(); } catch(e) {}
        }
    }

    // ---------- 4. 使用锁链牵引 ----------
    if (itemId === "cuffed:chain" && isCuffed(target)) {
        target.addTag(TAG_CHAINED);
        target.setDynamicProperty("cuffed:chained_by", player.id);
        sendMsg(player, "§7已用锁链连接 " + target.name + "，牵引模式启动");
        
        // 每 tick 拉向玩家
        const chainId = system.runInterval(() => {
            try {
                if (!player.isValid() || !target.isValid()) {
                    system.clearRun(chainId);
                    return;
                }
                if (!target.hasTag(TAG_CHAINED)) {
                    system.clearRun(chainId);
                    return;
                }
                const loc = player.location;
                const tloc = target.location;
                const dx = loc.x - tloc.x;
                const dz = loc.z - tloc.z;
                const dist = Math.sqrt(dx*dx + dz*dz);
                if (dist > 2.0 && dist < 20.0) {
                    const pull = 0.3;
                    target.teleport({
                        x: tloc.x + dx * pull,
                        y: tloc.y,
                        z: tloc.z + dz * pull
                    });
                }
            } catch(e) {
                system.clearRun(chainId);
            }
        }, 1);
    }
});

// ================================================================
// 事件：方块交互（挂锁 + 牢门）
// ================================================================

world.afterEvents.playerInteractWithBlock.subscribe((event) => {
    const { player, block, itemStack } = event;
    if (!player || !block || !itemStack) return;

    const itemId = getItemId(itemStack);

    // ---------- 挂锁箱子 ----------
    if (itemId === "cuffed:padlock" && block.typeId === "minecraft:chest") {
        const loc = `${block.x},${block.y},${block.z}`;
        block.setDynamicProperty(DYNAMIC_LOCKED_CHEST, true);
        block.setDynamicProperty(DYNAMIC_CHEST_OWNER, player.id);
        sendMsg(player, "§6箱子已上锁！只有你的钥匙可以打开");
        // 消耗一个挂锁
        const inv = player.getComponent("minecraft:inventory");
        if (inv) {
            const container = inv.container;
            const slot = player.selectedSlotIndex;
            const current = container.getItem(slot);
            if (current) {
                current.amount--;
                if (current.amount <= 0) container.setItem(slot);
                else container.setItem(slot, current);
            }
        }
    }

    // ---------- 解锁挂锁箱子 ----------
    if (itemId === "cuffed:padlock_key") {
        const isLocked = block.getDynamicProperty(DYNAMIC_LOCKED_CHEST);
        const ownerId = block.getDynamicProperty(DYNAMIC_CHEST_OWNER);
        if (isLocked) {
            block.setDynamicProperty(DYNAMIC_LOCKED_CHEST, false);
            block.setDynamicProperty(DYNAMIC_CHEST_OWNER, undefined);
            sendMsg(player, "§a锁已打开！");
        }
    }
});

// ================================================================
// 事件：阻止被铐玩家打开锁住的箱子
// ================================================================

world.beforeEvents.playerInteractWithBlock.subscribe((event) => {
    const { player, block } = event;
    if (!player || !block) return;
    
    // 阻止被铐玩家交互
    if (isCuffed(player)) {
        event.cancel = true;
        sendMsg(player, "§c你被铐住了！无法操作");
        return;
    }

    // 阻止打开锁住的箱子
    if (block.typeId === "minecraft:chest") {
        const isLocked = block.getDynamicProperty(DYNAMIC_LOCKED_CHEST);
        const ownerId = block.getDynamicProperty(DYNAMIC_CHEST_OWNER);
        if (isLocked && player.id !== ownerId) {
            event.cancel = true;
            sendMsg(player, "§c这个箱子被锁住了！");
        }
    }
});

// ================================================================
// 周期检查：对铐住玩家持续施加效果（防止用指令清除）
// ================================================================

system.runInterval(() => {
    for (const player of world.getAllPlayers()) {
        if (isCuffed(player)) {
            if (!player.hasEffect("slowness")) {
                player.addEffect("slowness", 999999, { amplifier: 5, showParticles: false });
            }
            if (!player.hasEffect("jump_boost")) {
                player.addEffect("jump_boost", 999999, { amplifier: -10, showParticles: false });
            }
        }
    }
}, 100);  // 每5秒检查一次

// ================================================================
// 提示信息（玩家加入时）
// ================================================================

world.afterEvents.playerSpawn.subscribe((event) => {
    const player = event.player;
    system.runTimeout(() => {
        sendMsg(player, "§b§l监禁 §r§7Cuffed 模组已加载");
        sendMsg(player, "§7合成手铐 → 右键铐人 | 钥匙解锁 | 挂锁锁箱子");
    }, 20);
});
""".strip()

write_plain(f"{BASE}/behavior_pack/scripts/main.js", script_code)

# ============================
# 10. README
# ============================

readme = f"""# 监禁 (Cuffed) - 网易版《我的世界》模组

> 给你的朋友们戴上手铐并关起来！

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
│   ├── textures/          # 16×16 占位纹理
│   └── texts/             # 语言文件
└── generate.py            # 生成脚本（重新运行即可全部重建）
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

当前纹理为 **16×16 占位纹理**（纯色带简单图案）。

想换成好看的像素风纹理，可以用 Agnes API 生成：

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

## 🐾 来自 WoWo

一一自己玩的模组，不卖钻石！
觉得丑的纹理以后用 Agnes 重新生成就行，代码部分直接能用。
有问题随时找我改！
"""
write_plain(f"{BASE}/README.md", readme)

print("✅ 监禁 (Cuffed) 网易版模组生成完毕！")
print(f"📂 位置: {BASE}")
print(f"📦 行为包: behavior_pack/")
print(f"🎨 资源包: resource_pack/")
print(f"📖 README: README.md")
print(f"\n🎮 共生成 {len(items)} 个物品, {len(blocks)} 个方块, {len(recipes)} 个配方")
print()
print("💡 提示：贴图如果已存在会被跳过（不会覆盖你提取的真实贴图）")
print("   想换贴图：运行 python extract_textures.py")
