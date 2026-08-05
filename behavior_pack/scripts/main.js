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