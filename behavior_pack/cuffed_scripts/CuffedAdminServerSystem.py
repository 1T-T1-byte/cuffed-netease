# -*- coding: utf-8 -*-
"""
监禁 (Cuffed) - 自定义指令 /admin 处理
=======================================
监听网易自定义指令事件，给目标玩家添加 cuffed:admin 标签
（该标签由 JS 侧的 main.js 识别，用于管理员秒拆加固方块）
"""

import mod.server.extraServerApi as serverApi

SERVER_SYSTEM = serverApi.GetServerSystemCls()

ADMIN_TAG = "cuffed:admin"
CMD_NAME = "admin"


class CuffedAdminServerSystem(SERVER_SYSTEM):

    def __init__(self, namespace, system_name):
        super(CuffedAdminServerSystem, self).__init__(namespace, system_name)
        # 监听自定义指令触发事件
        self.ListenForEvent(
            serverApi.GetEngineNamespace(),
            serverApi.GetEngineSystemName(),
            "CustomCommandTriggerServerEvent",
            self,
            self.OnCustomCommandTrigger
        )

    def OnCustomCommandTrigger(self, args):
        # 只处理 /admin 指令
        if args.get("command") != CMD_NAME:
            return

        params = args.get("args") or []
        if not params:
            return

        # target 类型参数的 value 是所有目标的 entityId 元组
        target_ids = params[0].get("value") or ()
        comp_factory = serverApi.GetEngineCompFactory()
        count = 0
        for entity_id in target_ids:
            try:
                comp = comp_factory.CreateTag(entity_id)
                if comp.AddEntityTag(ADMIN_TAG):
                    count += 1
            except Exception:
                pass

        if count > 0:
            args["return_msg_key"] = u"§a\u2705 \u5df2\u7ed9 %d \u4e2a\u73a9\u5bb6\u6dfb\u52a0\u7ba1\u7406\u5458\u6743\u9650" % count
        else:
            args["return_msg_key"] = u"§c\u672a\u627e\u5230\u76ee\u6807\u73a9\u5bb6"
