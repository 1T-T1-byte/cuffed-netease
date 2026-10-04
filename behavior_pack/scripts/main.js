//=========================================================================
// 监禁 (Cuffed) - 核心逻辑
// 网易版《我的世界》基岩版
//=========================================================================

import { world, system, EntityComponentTypes, ItemComponentTypes, GameMode, ItemStack, BlockPermutation } from "@minecraft/server";
import { ModalFormData } from "@minecraft/server-ui";

const MOD_PREFIX = "§7[监禁]§r ";
const TAG_CUFFED = "cuffed:handcuffed";
const TAG_CHAINED = "cuffed:chained";
const DYNAMIC_LOCKED_CHEST = "cuffed:locked_chest";
const DYNAMIC_CHEST_OWNER = "cuffed:chest_owner";

// ================================================================
// 工具函数
// ================================================================

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

// 消耗手持物品 1 个
function consumeOneItem(player) {
    try {
        const inv = player.getComponent("minecraft:inventory");
        if (!inv) return;
        const container = inv.container;
        const slot = player.selectedSlotIndex;
        const current = container.getItem(slot);
        if (current) {
            current.amount--;
            container.setItem(slot, current.amount > 0 ? current : undefined);
        }
    } catch(e) {}
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
// 事件：方块交互（牢门放置 / 密码锁 / 传统挂锁 / 开锁器暴力破解）
// 适用范围：箱子 + 铁门（牢门）
// ================================================================

// 可以上锁的方块
function isLockableBlock(block) {
    const t = block.typeId;
    return t === "minecraft:chest" || t === "minecraft:iron_door";
}

// 获取铁门的上下两半（锁数据要同步到两半）
function getDoorHalves(block) {
    const dim = block.dimension;
    const loc = block.location;
    let lowerY = loc.y;
    try {
        if (block.permutation.getState("minecraft:vertical_half") === "upper") {
            lowerY = loc.y - 1;
        }
    } catch (e) {}
    return {
        lower: dim.getBlock({ x: loc.x, y: lowerY, z: loc.z }),
        upper: dim.getBlock({ x: loc.x, y: lowerY + 1, z: loc.z })
    };
}

// 获取锁数据存储方块：箱子=自身；铁门=下半部分（统一存储，避免上下两半数据不同步）
function getLockHost(block) {
    if (block.typeId === "minecraft:iron_door") {
        const { lower } = getDoorHalves(block);
        return lower || block;
    }
    return block;
}

// 放置牢门（铁门）
function placeCellDoor(player, clickedBlock) {
    const dim = clickedBlock.dimension;
    const baseLoc = { x: clickedBlock.x, y: clickedBlock.y + 1, z: clickedBlock.z };
    const topLoc = { x: baseLoc.x, y: baseLoc.y + 1, z: baseLoc.z };

    let below, above;
    try {
        below = dim.getBlock(baseLoc);
        above = dim.getBlock(topLoc);
    } catch (e) { return; }

    if (!below || !above || !below.isAir || !above.isAir) {
        sendMsg(player, "§c这里放不下牢门（需要两格高空间）");
        return;
    }

    // 根据玩家朝向决定门的方向
    const yaw = player.getRotation().y;
    let dir = "north";
    if (yaw >= -45 && yaw < 45) dir = "south";
    else if (yaw >= 45 && yaw < 135) dir = "west";
    else if (yaw >= -135 && yaw < -45) dir = "east";

    try {
        dim.setBlockPermutation(baseLoc, BlockPermutation.resolve("minecraft:iron_door", {
            "minecraft:cardinal_direction": dir,
            "minecraft:vertical_half": "lower"
        }));
        dim.setBlockPermutation(topLoc, BlockPermutation.resolve("minecraft:iron_door", {
            "minecraft:cardinal_direction": dir,
            "minecraft:vertical_half": "upper"
        }));
        consumeOneItem(player);
        sendMsg(player, "§6🚪 牢门已放置！用密码锁/挂锁可以锁住它");
    } catch (e) {
        sendMsg(player, "§c放置失败：" + e);
    }
}

// 手动开关铁门（原版铁门只能红石开，这里用脚本改成可手开）
function toggleDoor(block) {
    const dim = block.dimension;
    const { lower, upper } = getDoorHalves(block);
    if (!lower || !upper) return;
    try {
        const isOpen = lower.permutation.getState("open_bit");
        const newOpen = !isOpen;
        dim.setBlockPermutation(lower.location, lower.permutation.withState("open_bit", newOpen));
        dim.setBlockPermutation(upper.location, upper.permutation.withState("open_bit", newOpen));
    } catch (e) {}
}

world.afterEvents.playerInteractWithBlock.subscribe((event) => {
    const { player, block, itemStack } = event;
    if (!player || !block) return;

    const itemId = getItemId(itemStack);

    // ---------- 🚪 放置牢门 ----------
    if (itemId === "cuffed:cell_door") {
        placeCellDoor(player, block);
        return;
    }

    // ---------- 🚪 铁门手开（空手或非锁物品右键）----------
    if (block.typeId === "minecraft:iron_door") {
        if (itemId === "cuffed:padlock" || itemId === "cuffed:key_lock" ||
            itemId === "cuffed:padlock_key" || itemId === "cuffed:lockpick") {
            // 这些物品走下面的锁逻辑
        } else {
            const host = getLockHost(block);
            const locked = host.getDynamicProperty("cuffed:password_locked") || host.getDynamicProperty("cuffed:key_locked");
            if (locked && player.id !== host.getDynamicProperty("cuffed:chest_owner")) {
                sendMsg(player, "§c这个牢门被锁住了！");
                return;
            }
            toggleDoor(block);
            return;
        }
    }

    if (!itemStack || !isLockableBlock(block)) return;

    // ---------- 🔐 密码锁上锁（用户自定义密码）----------
    if (itemId === "cuffed:padlock") {
        const host = getLockHost(block);
        if (host.getDynamicProperty("cuffed:password_locked") || host.getDynamicProperty("cuffed:key_locked")) {
            sendMsg(player, "§c这里已经上锁了！");
            return;
        }
        new ModalFormData()
            .title("🔐 设置密码锁")
            .textField("请输入你的密码", "1-9999 的数字")
            .show(player).then(resp => {
                if (resp.canceled) return;
                const password = parseInt(resp.formValues[0]);
                if (isNaN(password) || password < 1 || password > 9999) {
                    sendMsg(player, "§c密码必须是 1-9999 的数字！");
                    return;
                }
                try {
                    host.setDynamicProperty("cuffed:password_locked", true);
                    host.setDynamicProperty("cuffed:chest_owner", player.id);
                    host.setDynamicProperty("cuffed:password", password);
                    host.setDynamicProperty("cuffed:brute_attempts", 0);
                    host.setDynamicProperty("cuffed:brute_locked_until_tick", 0);
                } catch (e) {
                    sendMsg(player, "§c上锁失败，方块可能已被移除");
                    return;
                }
                sendMsg(player, "§6🔒 密码锁已上锁！");
                sendMsg(player, `§e你的密码是 §l§a${password}§r §e(记好！)`);
                consumeOneItem(player);
            });
    }

    // ---------- 🔐 所有者密码解锁 ----------
    if (itemId === "cuffed:padlock") {
        const host = getLockHost(block);
        if (host.getDynamicProperty("cuffed:password_locked") === true) {
            const ownerId = host.getDynamicProperty("cuffed:chest_owner");
            if (player.id !== ownerId) {
                sendMsg(player, "§c这不是你上的锁");
                return;
            }
            const correctPwd = host.getDynamicProperty("cuffed:password");
            new ModalFormData()
                .title("🔓 密码解锁")
                .textField("请输入密码", "1-9999")
                .show(player).then(resp => {
                    if (resp.canceled) return;
                    if (parseInt(resp.formValues[0]) === correctPwd) {
                        unlockPwdChest(host, player);
                    } else {
                        sendMsg(player, "§c密码错误！");
                    }
                });
        }
    }

    // ---------- 🔑 传统挂锁上锁 ----------
    if (itemId === "cuffed:key_lock") {
        const host = getLockHost(block);
        if (host.getDynamicProperty("cuffed:password_locked") || host.getDynamicProperty("cuffed:key_locked")) {
            sendMsg(player, "§c这里已经上锁了！");
            return;
        }
        host.setDynamicProperty("cuffed:key_locked", true);
        host.setDynamicProperty("cuffed:chest_owner", player.id);
        sendMsg(player, "§6🔒 挂锁已上锁！用挂锁钥匙打开");
        consumeOneItem(player);
    }

    // ---------- 🔑 挂锁钥匙解锁 ----------
    if (itemId === "cuffed:padlock_key") {
        const host = getLockHost(block);
        if (host.getDynamicProperty("cuffed:key_locked") === true) {
            clearLock(host);
            sendMsg(player, "§a🔓 挂锁已解开！");
        }
    }

    // ---------- 🗡️ 开锁器暴力破解密码锁 ----------
    if (itemId === "cuffed:lockpick") {
        const host = getLockHost(block);
        if (host.getDynamicProperty("cuffed:password_locked") === true) {
            const ownerId = host.getDynamicProperty("cuffed:chest_owner");
            if (player.id === ownerId) {
                sendMsg(player, "§e这是你的锁，用密码锁直接解锁就行");
                return;
            }
            // 检查是否锁死中
            const lockedUntil = host.getDynamicProperty("cuffed:brute_locked_until_tick") || 0;
            const nowTick = system.currentTick;
            if (lockedUntil > nowTick) {
                const remain = Math.ceil((lockedUntil - nowTick) / 20 / 60);
                sendMsg(player, `§c🔒 已锁死！还需约 ${remain} 分钟才能再次暴力破解`);
                return;
            }
            const attempts = host.getDynamicProperty("cuffed:brute_attempts") || 0;
            const remaining = 3 - attempts;

            // 系统随机生成一个爆破目标密码（和原密码无关，纯暴力破解）
            const brutePwd = Math.floor(Math.random() * 9999) + 1;

            new ModalFormData()
                .title("🗡️ 暴力破解")
                .textField(`猜密码 (1-9999)，剩 ${remaining} 次机会`, "输入数字")
                .show(player).then(resp => {
                    if (resp.canceled) return;
                    const input = parseInt(resp.formValues[0]);
                    if (input === brutePwd) {
                        unlockPwdChest(host, player);
                        sendMsg(player, "§a🎉 密码正确！暴力破解成功！");
                    } else {
                        const newAttempts = attempts + 1;
                        try {
                            host.setDynamicProperty("cuffed:brute_attempts", newAttempts);
                            if (newAttempts >= 3) {
                                host.setDynamicProperty("cuffed:brute_locked_until_tick", nowTick + 36000);
                                host.setDynamicProperty("cuffed:brute_attempts", 0);
                            }
                        } catch (e) {}
                        try { itemStack?.getComponent("minecraft:durability")?.damage?.(); } catch(e) {}
                        if (newAttempts >= 3) {
                            sendMsg(player, "§4💀 3次全错！锁死 30 分钟！");
                        } else {
                            sendMsg(player, `§7密码错误！还剩 §c${2 - attempts} §7次`);
                        }
                    }
                });
        }
    }

    // ---------- 开锁器破坏手铐（保留原功能）----------
    // 这个功能在 playerInteractWithEntity 事件里已保留
});

function unlockPwdChest(host, player) {
    host.setDynamicProperty("cuffed:password_locked", false);
    clearLockData(host);
    sendMsg(player, "§a🔓 密码锁已解开！");
}

function clearLock(host) {
    host.setDynamicProperty("cuffed:key_locked", false);
    clearLockData(host);
}

function clearLockData(host) {
    host.setDynamicProperty("cuffed:chest_owner", undefined);
    host.setDynamicProperty("cuffed:password", undefined);
    host.setDynamicProperty("cuffed:brute_attempts", 0);
    host.setDynamicProperty("cuffed:brute_locked_until_tick", 0);
}

// ================================================================
// 破坏保护：非管理员挖不动加固方块，管理员可以正常挖掉
// （方块硬度设得很低，所以管理员一挖就破；普通玩家每次都被取消）
// ================================================================

function isAdminPlayer(player) {
    try {
        if (player.getGameMode() === GameMode.creative) return true;
        if (player.hasTag("cuffed:admin")) return true;
        if (player.isOp && player.isOp()) return true;
    } catch (e) {}
    return false;
}

world.beforeEvents.playerBreakBlock.subscribe((event) => {
    const { player, block } = event;
    if (!block || !player) return;
    const bt = block.typeId;
    if (!bt.startsWith("cuffed:")) return; // 只保护本模组方块

    if (!isAdminPlayer(player)) {
        event.cancel = true;
        sendMsg(player, "§c这个方块太坚固了，只有管理员才能破坏！");
    }
    // 管理员：不拦截 → 正常破坏（方块硬度低，几乎瞬间）
});

// ================================================================
// 事件：阻止被铐玩家打开锁住的箱子
// ================================================================

world.beforeEvents.playerInteractWithBlock.subscribe((event) => {
    const { player, block } = event;
    if (!player || !block) return;

    // 阻止被铐玩家与箱子/牢门交互
    if (isCuffed(player) && isLockableBlock(block)) {
        event.cancel = true;
        sendMsg(player, "§c你被铐住了！无法操作");
        return;
    }

    // 阻止非拥有者打开已锁的箱子/牢门
    if (isLockableBlock(block)) {
        const host = getLockHost(block);
        const pwdLocked = host.getDynamicProperty("cuffed:password_locked");
        const keyLocked = host.getDynamicProperty("cuffed:key_locked");
        if ((pwdLocked || keyLocked) && player.id !== host.getDynamicProperty("cuffed:chest_owner")) {
            event.cancel = true;
            sendMsg(player, "§c这个被锁住了！");
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
        // 自动检测OP/管理员 → 加 admin tag
        try {
            if (player.isOp?.() && !player.hasTag("cuffed:admin")) {
                player.addTag("cuffed:admin");
            }
            if (!player.isOp?.() && player.hasTag("cuffed:admin")) {
                player.removeTag("cuffed:admin"); // 被撤权自动摘 tag
            }
        } catch(e) {}
    }
}, 100);  // 每5秒检查一次

// ================================================================
// 提示信息（玩家加入时）
// ================================================================

world.afterEvents.playerSpawn.subscribe((event) => {
    const player = event.player;
    system.runTimeout(() => {
        sendMsg(player, "§b§l监禁 §r§7Cuffed 模组已加载");
        sendMsg(player, "§7手铐→铐人 | 钥匙→解锁 | 密码锁→上锁 | 挂锁→传统钥匙锁 | 开锁器→暴力破解");
        sendMsg(player, "§7给管理员权限：输入 §e!admin <玩家名>");
    }, 20);
});

// ================================================================
// 命令：!admin <玩家名>  一键给管理员快拆权限
// （用 ! 前缀而不是 /，因为 / 开头会被原版命令系统拦截）
// ================================================================

function giveAdminTag(targetName, sender) {
    const all = world.getAllPlayers();
    if (!targetName) {
        sender.addTag("cuffed:admin");
        sendMsg(sender, "§a✅ 你已获得管理员快拆权限！");
        return;
    }
    if (targetName === "@a") {
        for (const p of all) p.addTag("cuffed:admin");
        sendMsg(sender, "§a✅ 已给所有玩家添加管理员快拆权限！");
        return;
    }
    if (targetName === "@p") {
        sender.addTag("cuffed:admin");
        sendMsg(sender, "§a✅ 已给自己添加管理员快拆权限！");
        return;
    }
    const target = all.find(p => p.name === targetName);
    if (!target) {
        sendMsg(sender, `§c找不到玩家: ${targetName}`);
        return;
    }
    target.addTag("cuffed:admin");
    sendMsg(sender, `§a✅ 已给 §e${targetName}§a 添加管理员快拆权限！`);
    sendMsg(target, "§a你已获得管理员快拆权限！");
}

// 方式 1：聊天命令 !admin（100% 可用）
world.beforeEvents.chatSend.subscribe((event) => {
    const msg = event.message.trim();
    if (!msg.startsWith("!admin") && !msg.startsWith("！admin")) return;
    event.cancel = true;
    const parts = msg.replace(/^[!！]admin\s*/, "").trim().split(/\s+/).filter(Boolean);
    giveAdminTag(parts[0], event.sender);
});

// 方式 2：尝试注册原生命令 /cuffed:admin（需 Script API 2.0+，不支持则自动跳过）
try {
    system.beforeEvents.startup.subscribe((event) => {
        try {
            const registry = event.customCommandRegistry;
            if (!registry) return;
            registry.registerCommand({
                name: "cuffed:admin",
                description: "给玩家管理员快拆权限",
                permissionLevel: 1,
                cheatsRequired: false,
                mandatoryParameters: [{ name: "player", type: "PlayerSelector" }]
            }, (origin, args) => {
                const sender = origin.sourceEntity;
                const targets = args[0];
                if (sender && targets) {
                    for (const t of targets) {
                        t.addTag("cuffed:admin");
                        sendMsg(t, "§a你已获得管理员快拆权限！");
                    }
                    sendMsg(sender, "§a✅ 已添加管理员快拆权限！");
                }
                return { status: 0 };
            });
        } catch (e) {}
    });
} catch (e) {}