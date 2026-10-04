# -*- coding: utf-8 -*-
"""
监禁 (Cuffed) - Python Mod 入口
================================
作用：注册服务端 System，用于监听网易自定义指令 /admin
（纯 JS 的 Script API 无法注册不带命名空间的 /admin 命令，
  所以这里用网易 ModAPI 的 netease_commands 机制实现）
"""

from common.mod import Mod
import mod.server.extraServerApi as serverApi

MOD_NAME = "CuffedAdminMod"
MOD_VERSION = "1.0.0"
SERVER_SYSTEM_NAME = "CuffedAdminServerSystem"
SERVER_SYSTEM_CLS = "cuffed_scripts.CuffedAdminServerSystem.CuffedAdminServerSystem"


@Mod.Binding(name=MOD_NAME, version=MOD_VERSION)
class CuffedAdminMod(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    def init_server(self):
        # 注册服务端系统，系统内部会监听自定义指令事件
        serverApi.RegisterSystem(MOD_NAME, SERVER_SYSTEM_NAME, SERVER_SYSTEM_CLS)

    @Mod.DestroyServer()
    def destroy_server(self):
        pass

    @Mod.InitClient()
    def init_client(self):
        pass

    @Mod.DestroyClient()
    def destroy_client(self):
        pass
