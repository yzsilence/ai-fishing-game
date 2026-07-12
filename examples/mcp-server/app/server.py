#!/usr/bin/env python3
"""
MCP Server for Fishing + Birdwatching
Supports: play_fishing (uses fishing.py) and birdwatch (uses birds.json)
"""

import os
import sys
import json
import random
import time
from typing import Any, Dict, List, Optional, Tuple
from mcp.server.fastmcp import FastMCP

# ---------- Environment Config ----------
FISHING_ENGINE = os.getenv("FISHING_ENGINE", "fishing")  # "fishing" or "engine"
FISHING_PATH = os.getenv("FISHING_PATH", "/mcp")
HOST = os.getenv("FISHING_HOST", "0.0.0.0")
PORT = int(os.getenv("FISHING_PORT", "3457"))

# ---------- Fishing Engine ----------
# Directly import from fishing.py (blind version)
from fishing import cmd as fishing_cmd
from fishing import new_game as fishing_new_game

# ---------- Birdwatching Engine ----------
from bird_engine import BirdEngine

# ---------- MCP Server ----------
mcp = FastMCP("fishing", host=HOST, port=PORT, streamable_http_path=FISHING_PATH, stateless_http=True)

# 初始化鸟引擎（全局）
bird_engine = BirdEngine()

@mcp.tool()
def play_fishing(command: str) -> str:
    """Send a command to the fishing game (uses fishing.py engine)."""
    return fishing_cmd(command)

@mcp.tool()
def birdwatch(command: str) -> str:
    """文字观鸟游戏。把一条游戏指令作为 command 传入，返回结果文字。
    常用指令：
      help / status / shop / inventory / encyclopedia / letters
      goto [生境名]                        不带参数 = 列出生境和本季情报
      scan [次数] [饵id] [stop=新种,稀有,传说]  观察；带次数=连看 1~8 次；stop= 遇新种/稀有就提前停
      submit                               提交笔记换点数
      buy <饵id> [数量]                    买饵 (berries/seeds/fish)
      aviary / invite <鸟名> / feed <鸟名> <饵id>   鸟园：查看 / 邀请 / 喂食
      hatch [蛋名] / feed 雏鸟 <饵id>      孵化鸟蛋 / 喂养雏鸟
      story <鸟名> / look <鸟名>           读日志残页 / 细看某鸟
    省 token 技巧：用 `scan 8` 一次连看只回一个汇总；用 ; 把多条指令串成一批一次跑
    （最多 8 条），如 'scan 8; submit'、'status; aviary; letters'。
    每次返回末尾带一行 📊 状态栏 JSON，看它即可掌握局面，不必反复 status。
    行为约定：一条回复中最多调用一次本工具（可用批量指令），看完结果再决定下一步；
    连续 scan 有冷却，被提醒休息时请转向鸟园、故事或整理收藏。
    """
    try:
        return bird_engine.cmd(command)
    except Exception as e:
        return f"⚠️ 指令执行出错：{e}。请检查格式，或调 birdwatch('help') 看规则。"

@mcp.tool()
def new_game(seed: Optional[int] = None) -> str:
    """Reset the fishing game (clears save)."""
    return fishing_new_game(seed)

@mcp.tool()
def bird_reset(confirm: bool = False) -> str:
    """重置观鸟游戏，清空全部进度（图鉴、点数、收藏、笔记）。
    直接调用只会返回确认提示；真的要重置请传 confirm=True。
    注意：此操作不可恢复，不影响钓鱼游戏。
    """
    global bird_engine
    if not confirm:
        return "⚠️ 这会清空观鸟的全部进度（图鉴、收藏、点数），且无法恢复。确认重置请用 bird_reset(confirm=True)。"
    try:
        if os.path.exists(bird_engine.save_path):
            os.remove(bird_engine.save_path)
        bird_engine = BirdEngine()
        return "✅ 观鸟游戏已重置，一切回到最初：200 点，站在芦花浅渚。"
    except Exception as e:
        return f"⚠️ 重置失败：{e}"

# ---------- Run ----------
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
