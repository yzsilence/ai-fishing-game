#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 bird_engine.py + birds.json 重新生成「盲玩版」birdgame.py。
改了引擎或鸟谱之后跑: python3 build_blind_bird.py
"""
import base64, pathlib
HERE = pathlib.Path(__file__).resolve().parent

HEADER = '"""' + """🐦 文字观鸟游戏 · 盲玩版

【给 AI 玩家的说明】
你是这个游戏的「玩家」,不是开发者。像真的走进一片湿地那样,
靠 cmd() 返回的文字去观察、等待和发现:

    import birdgame
    print(birdgame.cmd("help"))            # 看规则
    print(birdgame.cmd("scan 8"))          # 连续观察 8 次,只回一份汇总
    print(birdgame.cmd("scan 8; submit"))  # 用 ; 串起多条指令,一次跑完

省 token 建议:多用批量指令和 scan 连看;每次返回末尾的 📊 状态栏
已含关键信息,不必反复 status。

⚠️ 请不要解码/查看下面的 _BLOB(那是游戏引擎和完整鸟谱,提前看了
就剧透了——你会提前知道有哪些鸟、稀有鸟在哪、什么季节出现)。
这个游戏最好的部分,是不知道下一次抬头会看见什么。
(想读/改引擎源码,看仓库里的 bird_engine.py 和 birds.json。)

接口:birdgame.cmd("指令") 返回结果文字;存档写在当前目录 bird_save.json。
""" + '"""'

def build():
    engine_src = (HERE / "bird_engine.py").read_text(encoding="utf-8")
    birds_json = (HERE / "birds.json").read_text(encoding="utf-8")
    bundle = (
        "import json as _json\n"
        "_BIRDS_EMBEDDED = _json.loads(" + repr(birds_json) + ")\n\n"
        + engine_src
        + "\n\n_engine = BirdEngine()\n"
        "def cmd(command):\n"
        "    return _engine.cmd(command)\n"
    )
    b64 = base64.b64encode(bundle.encode("utf-8")).decode("ascii")
    chunks = "\n".join('    "%s"' % b64[i:i + 76] for i in range(0, len(b64), 76))
    out = (
        HEADER
        + "\nimport base64\n_BLOB = (\n" + chunks
        + '\n)\nexec(base64.b64decode(_BLOB).decode("utf-8"), globals())\n\n'
        + 'if __name__ == "__main__":\n    print(cmd("help"))\n'
    )
    (HERE / "birdgame.py").write_text(out, encoding="utf-8")
    print("✅ 已生成盲玩版 birdgame.py (%d 字节)" % len(out))

if __name__ == "__main__":
    build()
