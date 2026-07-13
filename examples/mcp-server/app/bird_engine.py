#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""观鸟游戏引擎(可读源码)。
改鸟谱:编辑 birds.json | 改玩法:编辑本文件
改完记得跑 python3 build_blind_bird.py 重新生成盲玩版 birdgame.py
"""
import os
import json
import random
import time
from typing import Any, Dict, List, Optional, Tuple

class BirdEngine:
    def __init__(self, data_path: str = "birds.json", save_path: str = "bird_save.json"):
        self.data_path = data_path
        self.save_path = save_path
        self.birds = []
        if "_BIRDS_EMBEDDED" in globals():
            self.birds = globals()["_BIRDS_EMBEDDED"]
        else:
            self.load_data()
        self.load_save()

    def load_data(self):
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.birds = data.get("birds", [])
        except Exception as e:
            self.birds = []
            print(f"Warning: Could not load birds.json: {e}")

    def load_save(self):
        default = {
            "points": 200,
            "season": "春",
            "turn": 0,
            "unlocked_habitats": ["芦花浅渚", "城隅林"],
            "current_habitat": "芦花浅渚",
            "notebook": [],
            "inventory": {
                "诱饵:浆果": 0,
                "诱饵:种子": 5,
                "诱饵:小鱼干": 0,
            },
            "collection": {
                "鸟蛋": [],
                "珍羽": [],
                "宝石": [],
                "风信笺": [],
                "迁徙图碎片": [],
            },
            "habitat_fragments": {},
            "encountered": [],
            "active_boost": 0,
            "aviary": {},
            "aviary_memory": {},
            "nest_egg": None,
            "scan_times": [],
            "scans_window": [],
            "field_notes": [],
        }
        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                for key in default:
                    if key in saved:
                        default[key] = saved[key]
        except:
            pass
        self.__dict__.update(default)
        self._season_cycle = ["春", "夏", "秋", "冬"]
        self._season_idx = self._season_cycle.index(self.season)

    def save(self):
        data = {k: v for k, v in self.__dict__.items()
                if not k.startswith('_') and k not in ['birds', 'data_path', 'save_path']}
        try:
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"⚠️ 存档失败: {e}"
        return ""

    def _advance_season(self):
        self.turn += 1
        if self.turn % 10 == 0:
            self._season_idx = (self._season_idx + 1) % 4
            self.season = self._season_cycle[self._season_idx]

    def _get_bird_by_id(self, bird_id):
        for b in self.birds:
            if b["id"] == bird_id:
                return b
        return None

    def _get_birds_in_habitat(self, habitat):
        return [b for b in self.birds
                if habitat in b.get("habitats", [])
                and ("seasons" not in b or self.season in b["seasons"])]

    def _pick_random_bird(self, habitat, baits=None):
        pool = self._get_birds_in_habitat(habitat)
        if not pool:
            return None
        weights = []
        boost = getattr(self, "active_boost", 0) > 0
        for b in pool:
            if b["rarity"] == "普通":
                w = 70
            elif b["rarity"] == "稀有":
                w = 50 if boost else 25
            else:
                w = 15 if boost else 5
            if b.get("habitats") and b["habitats"][0] != habitat:
                w = w / 2
            if getattr(self, "trace_left", 0) > 0 and b["id"] == getattr(self, "trace_bird", None):
                w = w * 6
            weights.append(w)
        if baits:
            weights = [w + (10 if b["rarity"]=="稀有" else 5 if b["rarity"]=="传说" else 0) for b, w in zip(pool, weights)]
        total = sum(weights)
        if total == 0:
            return random.choice(pool)
        r = random.uniform(0, total)
        cum = 0
        for b, w in zip(pool, weights):
            cum += w
            if r <= cum:
                return b
        return pool[-1]

    def _pick_drop(self, bird):
        drops = bird.get("drops", [])
        if not drops:
            return None
        rarity = bird["rarity"]
        if rarity == "普通":
            count = 1
        elif rarity == "稀有":
            count = random.randint(1, 2)
        else:
            count = random.randint(2, 3)
        chosen = random.sample(drops, min(count, len(drops)))
        result = []
        for item in chosen:
            if "羽" in item or "绒" in item:
                result.append({"type": "珍羽", "name": item})
            elif "石" in item:
                result.append({"type": "宝石", "name": item})
            elif "蛋" in item or "卵" in item:
                result.append({"type": "鸟蛋", "name": item})
            elif "笺" in item or "信" in item:
                result.append({"type": "风信笺", "name": item})
            elif "碎片" in item or "图" in item:
                result.append({"type": "迁徙图碎片", "name": item})
            else:
                result.append({"type": "珍羽", "name": item})
        return result

    AMBIENCE = {
        "芦花浅渚": [
            "风把整片芦花往同一个方向吹得弯了腰，随即又松了手。",
            "水面忽然泛起波澜，涟漪一圈圈散开，却什么也没出现。",
            "远处的浅滩上，雾正在一点一点缓缓散开。",
            "一尾鱼跃出水面又落回去，像有人丢了枚硬币。",
            "芦苇丛深处传来窸窣声，你刚屏息凝神，它就停了。",
            "夕阳把水面照射成一整块缓缓晃动的铜。"
        ],
        "苍针岭": [
            "松涛从山脊那头滚滚而来，经过你，又迅速往谷底去。",
            "一颗松果毫无预兆地砸在地上，弹了两下。",
            "林子深处有什么轻轻踩断了一根枯枝。",
            "阳光从针叶的缝隙漏下来，在地上织成一张晃动的网。",
            "空气中全是松脂被晒过的味道，竟然有一丝暖意。",
            "一小簇雪从高处的枝头滑落，悄无声息。"
        ],
        "平野风吟": [
            "风穿过草海，草浪一路追到天边。",
            "一朵云的影子，正缓缓爬过整片草原。",
            "草籽被风卷了起来，在光里若隐若现。",
            "远处有只小兽窜过，草梢泛起波动，转眼又平息。",
            "你听见风里有极细的声音，像谁在遥远的地方吟诵。",
            "整片原野忽然安静下来，连风也停驻几秒。"
        ],
        "云栖崖": [
            "一团云从崖下漫上来，漫过你的脚背，又散了。",
            "谷底传来水声，很远，像是来自另一个季节。",
            "一块小石子从崖壁上跌落，声音响了很久才消失。",
            "风在岩缝间穿行，发出近似呜咽的声音。",
            "阳光劈开云层，一道光柱恰好落在对面的山脊上。",
            "崖边的草伏得很低，它们比你更懂如何享受这里的风。"
        ],
        "雾隐泽": [
            "雾很厚，但你脚下的路始终空出一步的宽度。",
            "远处传来水声，你分不清它来自左边还是右边，或者上面。",
            "雾里浮着极小的光点，你伸手，它绕开了你的手指。",
            "你回头看来时的路，雾已经合拢了，但你并不慌张——说不清为什么。",
            "某个方向传来一声鸟鸣，雾把它送到你耳边时，已经柔软得像一句耳语。",
            "雾忽然淡了一瞬，你看见极远处有水，有洲，有一道白色的影子。然后雾又合上了。"
        ],
        "城隅林": [
            "老墙上的爬山虎晃了晃，有什么从叶子后面偷偷溜走。",
            "谁家窗台上的风铃响了两声，又安静下来。",
            "一片叶子转着圈落在长椅上，像特意挑好了位置。",
            "巷口飘来饭菜的香气，混着一点桂花。",
            "屋檐的影子往前寸寸挪动，阳光很有耐心。",
            "自行车铃在远处叮了一声，惊起一小片扑翅声。"
        ]
    }

    def _item_value(self, item_name):
        for b in self.birds:
            if item_name in b.get("drops", []):
                if "石" in item_name:
                    return 25
                return {"普通": 15, "稀有": 40, "传说": 100}.get(b["rarity"], 15)
        return 25 if "石" in item_name else 15

    def _exchange(self, args):
        if not args:
            return ("💱 兑换说明：exchange <物品名> [数量] — 把珍羽或宝石换成点数\n"
                    "exchange all — 一键兑换全部珍羽和宝石\n"
                    "（鸟蛋、风信笺、迁徙图碎片是珍藏，不可兑换）")
        sellable = ["珍羽", "宝石"]
        if args[0] == "all":
            total = 0
            count = 0
            for cat in sellable:
                for item in list(self.collection[cat]):
                    total += self._item_value(item)
                    count += 1
                self.collection[cat] = []
            if count == 0:
                return "💱 没有可兑换的珍羽或宝石。"
            self.points += total
            self.save()
            return f"💱 兑换了 {count} 件收藏，共获得 {total} 点。当前 {self.points} 点。" + self._statusline()
        name = args[0]
        amount = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
        for cat in sellable:
            if name in self.collection[cat]:
                have = self.collection[cat].count(name)
                n = min(amount, have)
                value = self._item_value(name) * n
                for _ in range(n):
                    self.collection[cat].remove(name)
                self.points += value
                self.save()
                return f"💱 兑换了 {n} 件「{name}」，获得 {value} 点。当前 {self.points} 点。" + self._statusline()
        return f"❌ 收藏里没有可兑换的「{name}」（鸟蛋、风信笺、迁徙图碎片不可兑换）。"

    LETTERS = [
        "「等你看到这行字的时候，那只鸟应该已经飞到很远的地方了。替我看看它好吗。」",
        "「今天数了一百零七只过境的候鸟。数到第八十次的时候，忘了自己本来在等什么。」",
        "「山里落了今年第一场雪。我把没说完的话叠成这样，交给风。」",
        "「如果一只鸟记得你，它会绕很远的路回来看你。我是听一位老人说的，我信了。」",
        "「芦苇黄了三次。写信的人还在原来的地方，读信的人不知到了哪里。」",
        "「别为飞走的难过。它们衔走的每一根线头，都会织进某个遥远的巢里。」",
        "「风把这页纸带到哪里，哪里就是它该在的地方。你捡到它，说明你也是。」",
        "「我曾以为观察是我看它们。后来才明白，是它们允许我看。」",
        "「今天什么也没等到。但等待本身，把黄昏变得很长，很好。」",
        "「这是最后一页了。往后的故事，请替我写下去。」"
    ]

    def _letter_text(self, idx):
        return self.LETTERS[idx % len(self.LETTERS)]

    DIET_NAMES = {"fish": "小鱼干", "seeds": "种子", "berries": "浆果"}
    INVITE_COST = {"普通": 50, "稀有": 150, "传说": 400}

    def _find_bird(self, query):
        for b in self.birds:
            if b["id"] == query or b["name"] == query or query in b["name"]:
                return b
        return None

    def _aviary_view(self):
        av = getattr(self, "aviary", {})
        if not av:
            hv = self._hatch_view()
            if hv:
                return "🏡 鸟园（0/8 席）：\n" + hv
            return "🏡 鸟园还空着。用 invite <鸟名> 邀请你见过的鸟入驻吧（容量 8 席）。"
        lines = [f"🏡 鸟园（{len(av)}/8 席）："]
        for bid, info in av.items():
            bird = self._get_bird_by_id(bid)
            name = bird["name"] if bird else bid
            fav = self.DIET_NAMES.get(bird.get("diet", ""), "？") if bird else "？"
            lines.append(f"  {name} — 停留 {info['days']} 天 | 亲密度 {info['bond']} | 偏好：{fav}")
        hv = self._hatch_view()
        if hv:
            lines.append(hv)
        lines.append("（每次观察消耗一天停留；用 feed <鸟名> <诱饵> 喂食可延长）")
        return "\n".join(lines)

    def _invite(self, args):
        if not args:
            return "邀请谁呢？invite <鸟名>（只能邀请图鉴里已见过的鸟）"
        bird = self._find_bird(" ".join(args))
        if not bird:
            return f"❌ 没有找到这种鸟。"
        av = getattr(self, "aviary", {})
        if bird["id"] in av:
            return f"🏡 {bird['name']} 已经住在你的鸟园里了。"
        if bird["id"] not in self.encountered:
            return f"❓ 你还没有见过 {bird['name']}，无从邀请。先去野外遇见它吧。"
        if len(av) >= 8:
            return "🏡 鸟园已满（8/8）。想邀请新的鸟，得先等某位住客离开。"
        cost = self.INVITE_COST.get(bird["rarity"], 50)
        past_bond = getattr(self, "aviary_memory", {}).get(bird["id"], 0)
        if past_bond > 0:
            cost = cost // 2
        if self.points < cost:
            return f"❌ 邀请 {bird['name']} 需要 {cost} 点（当前 {self.points} 点）。"
        self.points -= cost
        av[bird["id"]] = {"days": 7, "bond": past_bond, "fed_today": 0}
        self.aviary = av
        self.save()
        back = "它认出了你，很快就安顿了下来。" if past_bond > 0 else "它警惕地打量了一圈，最终选了一根合意的栖枝。"
        return f"🏡 {bird['name']} 入驻了你的鸟园！{back}（花费 {cost} 点，初始停留 7 天）" + self._statusline()

    def _feed(self, args):
        if len(args) < 2:
            return "怎么喂呢？feed <鸟名> <诱饵> [次数]（berries/seeds/fish）"
        count = 1
        if args[-1].isdigit():
            count = max(1, min(int(args[-1]), 10))
            args = args[:-1]
        if len(args) < 2:
            return "怎么喂呢？feed <鸟名> <诱饵> [次数]（berries/seeds/fish）"
        bait = args[-1].lower()
        if bait not in ["berries", "seeds", "fish"]:
            return f"❌ 没有 {bait} 这种食物，可选 berries/seeds/fish。"
        bird = self._find_bird(" ".join(args[:-1]))
        av = getattr(self, "aviary", {})
        if not bird or bird["id"] not in av:
            return "❌ 鸟园里没有这位住客。用 aviary 看看谁在家。"
        key = f"诱饵:{bait}"
        info = av[bird["id"]]
        is_fav = bird.get("diet") == bait
        fed = 0
        total_days = 0
        total_bond = 0
        gifts = []
        for _ in range(count):
            if self.inventory.get(key, 0) <= 0:
                break
            self.inventory[key] -= 1
            fed += 1
            info["fed_today"] = info.get("fed_today", 0) + 1
            combo = is_fav and info["fed_today"] >= 3
            gained_days = 3 if is_fav else 1
            gained_bond = 4 if combo else (3 if is_fav else 1)
            info["days"] += gained_days
            old_bond = info["bond"]
            info["bond"] += gained_bond
            total_days += gained_days
            total_bond += gained_bond
            if old_bond // 25 < info["bond"] // 25:
                drops = bird.get("drops", [])
                if drops:
                    gift = random.choice(drops)
                    g_type = "宝石" if "石" in gift else "珍羽"
                    self.collection[g_type].append(gift)
                    gifts.append(gift)
        if fed == 0:
            return f"❌ 没有 {bait} 了，先去 buy 一些。"
        self.save()
        if is_fav and info["fed_today"] >= 3:
            react = f"它已经开始期待你的手了。今天喂了 {info['fed_today']} 次，它记得每一次。"
        elif is_fav:
            react = f"是它最爱的{self.DIET_NAMES[bait]}！它吃得很急，尾羽都翘了起来。"
        else:
            react = f"它礼貌地吃了几口{self.DIET_NAMES[bait]}，但你感觉它在期待别的。"
        gift_text = ""
        if gifts:
            gift_text = "\n🎁 " + bird["name"] + " 衔来小东西轻轻放在你手边：「" + "、".join(gifts) + "」。"
        tail_note = "，诱饵只够这些" if fed < count else ""
        summary = f"（喂了 {fed} 次{tail_note}，停留 +{total_days} 天，亲密度 +{total_bond}，现为 {info['bond']}）"
        return f"🍽️ {react}{summary}{gift_text}" + self._statusline()

    def _hatch_start(self, egg_name):
        if getattr(self, "nest_egg", None):
            return f"🥚 巢箱里已经有一枚蛋在孵了（{self.nest_egg['egg']}），一次只能孵一枚。"
        av = getattr(self, "aviary", {})
        if len(av) >= 8:
            return "🏡 鸟园已满（8/8），腾不出巢箱的位置了。"
        if egg_name not in self.collection["鸟蛋"]:
            return f"❌ 收藏里没有「{egg_name}」。"
        self.collection["鸟蛋"].remove(egg_name)
        self.nest_egg = {"egg": egg_name, "hatch_left": 2, "feed_left": 0, "bird_id": None}
        self.save()
        return f"🥚 你把{egg_name}安放进鸟园的巢箱，垫了软草。它很快就会有动静，观察间隙记得回来看看。" + self._statusline()

    def _hatch_tick(self):
        egg = getattr(self, "nest_egg", None)
        if not egg:
            return None
        if egg["bird_id"]:
            return None
        egg["hatch_left"] -= 1
        if egg["hatch_left"] <= 0:
            pool = [b for b in self.birds if b["rarity"] == "普通"]
            if "斑点" in egg["egg"] and random.randint(1, 100) <= 60:
                rare_pool = [b for b in self.birds if b["rarity"] == "稀有"]
                if rare_pool:
                    pool = rare_pool
            chick = random.choice(pool)
            egg["bird_id"] = chick["id"]
            egg["feed_left"] = 3
            return "🐣 鸟园里传来细碎的破壳声——有一枚蛋孵化了！（回 aviary 看看吧）"
        return None

    def _hatch_view(self):
        egg = getattr(self, "nest_egg", None)
        if not egg:
            return None
        if egg["bird_id"] is None:
            return f"  🥚 巢箱：{egg['egg']}，孵化中（还需 {egg['hatch_left']} 次观察）"
        return f"  🐣 巢箱：一只雏鸟，羽色尚看不分明（还需喂食 {egg['feed_left']} 次长大 — feed 雏鸟 <诱饵>）"

    def _hatch_feed(self, bait):
        egg = getattr(self, "nest_egg", None)
        if not egg or egg["bird_id"] is None:
            return "❌ 巢箱里还没有嗷嗷待哺的雏鸟。"
        key = f"诱饵:{bait}"
        if self.inventory.get(key, 0) <= 0:
            return f"❌ 没有 {bait} 了，先去 buy 一些。"
        self.inventory[key] -= 1
        egg["feed_left"] -= 1
        if egg["feed_left"] > 0:
            self.save()
            return f"🍽️ 雏鸟仰着头吞下食物，绒毛微微发亮。（还需 {egg['feed_left']} 次）" + self._statusline()
        bird = self._get_bird_by_id(egg["bird_id"])
        self.nest_egg = None
        if not bird:
            self.save()
            return "⚠️ 雏鸟长成了，却翻遍图鉴认不出它的品种——这似乎是一场意外，请把这件事告诉管理员吧。"
        is_new = bird["id"] not in self.encountered
        if is_new:
            self.encountered.append(bird["id"])
        mem = getattr(self, "aviary_memory", {})
        mem[bird["id"]] = max(mem.get(bird["id"], 0), 30)
        self.aviary_memory = mem
        self.save()
        tag = {"普通": "", "稀有": "✨", "传说": "🌟"}.get(bird["rarity"], "")
        new_tag = "🆕" if is_new else ""
        return (f"🕊️ 换羽完成的那个清晨，它站上巢箱边缘——是一只{new_tag}{tag}{bird['name']}！\n"
                f"它绕着鸟园飞了三圈，最后一圈贴着你的肩膀掠过，然后向{bird['habitats'][0]}的方向去了。\n"
                f"（图鉴已点亮；它记得你——野外重逢时，邀请只需半价。）") + self._statusline()

    STORIES = {
        "heron_rare": [
            "观察日志的边角有一行小字：“它总在同一块浅滩落脚。我查过水文，那里不是鱼最多的地方。”后面补了一句，墨迹深些，像是隔了几天才写：“今天想明白了——那里是倒影最清楚的地方。”",
            "“第四十一次记录。它捕鱼从不失手，但吃得很少。多出来的那些，它衔到下游放掉。我不知道鸟类学怎么解释这个。我私心把这一条记成：它在练习，不是在捕猎。练习什么，我还不知道。”",
            "日志的最后一页夹着一根黑得发亮的羽毛。字迹很轻：“离开前最后一次去看它。它照例低头看水，然后抬头看我——那个顺序，和我每天做的一模一样：先看它的倒影，再看它。原来这几年，是它在观察我。这根羽毛落在我脚边。我想，是允许的意思。”"
        ],
        "legendary_waterbird": [
            "“关于它，我只敢记‘疑似’。薄暮的水岸，光线不可信，眼睛不可信。可有一条我反复核对过：那几个傍晚，水面的银纹都是逆着风走的——像有什么东西沿岸经过，而我只看见了水的让路。”",
            "“最后一次见它，我做了个实验：它落在石上时，我转身背对它，数了三十下。转回来，它还在，姿势没变。可我明白那种感觉：你走进一个房间，知道刚才有人在谈论你。日志写到这里，我决定不再核对了。有些观察，承认它就好。”"
        ],
        "legendary_forest_bird": [
            "“雪停的黎明见到它。我一直举着整页笔记，它一动不动，配合得近乎慷慨。最终誊写时才发现，那一页只有开头两行字——后面全是空白。我记得我一直在写。我现在也记得。”",
            "“老猎人说，山里最深的雪窝子，冻死的鸟都朝着一个方向倒下，像在朝拜什么。他说完自己也笑了，说是瞎话。可我后来每次见到那只白鸮，它都停在那个方向的枝上。我没告诉老猎人。有些瞎话，多一个人知道就会成真。”"
        ],
        "legendary_city_bird": [
            "“巷尾的老太太说，她小时候这鸟就叫三声。我查了县志，四十年前有个抄书先生也记过‘檐上灰鹊，晨鸣必三’。要么它很长寿，要么——我更愿意相信，报时这件事，是一代一代传下来的。”",
            "“我数过它落脚的檐角：全是老宅，全是还住着人的老宅。隔壁那栋空了几年的，飞檐更漂亮，它从不去。搬走的人陆续回来过，说不上为什么。可我心里明白，它守着的从来不是房子。”"
        ],
        "ferry_crane": [
            "“我不该找到这里的。按里程算，我在苍针岭和平野之间；按脚下的水算，我在芦花浅渚；按雾的气息算……我不知道。日志本该记录坐标，可这一页，我只能记下‘我于此处’。”",
            "“临走前我问了个蠢问题：等谁到齐？雾没有回答，鹤亦没有回答。但回程的路出奇地短，短得像谁在体谅我。誊写这页的此刻，我忽然意识到，它在等的是每一个找到这里的人，都平安走完回去的路；是‘到齐’这件事本身在重复，一遍，又一遍。”"
        ],
        "scavenger_crow": [
            "“它今天在我的长椅那头留下了一枚瓶盖，擦得很亮。我假装没看见，它假装没放。我们对这套礼节都很满意。”",
            "“整理旧物，翻出七年来它‘落’在我这儿的东西：瓶盖、玻璃珠、一枚外国硬币、半块怀表。今天我终于想通不对劲在哪：这些东西排在一起，像一个人在一生中弄丢过的东西。我不知道它从哪里替谁一件件捡了回来。我把怀表修好了。它第二天就没再来过。”"
        ]
    }
    STORY_THRESHOLDS = [30, 70, 120]

    def _story(self, args):
        if not args:
            has = [self._get_bird_by_id(bid)["name"] for bid in self.STORIES if self._get_bird_by_id(bid)]
            return "📖 有些鸟的身后藏着旧日志的残页。story <鸟名> 试着读读看。（并非每只鸟都有）"
        bird = self._find_bird(" ".join(args))
        if not bird:
            return "❌ 没有找到这种鸟。"
        if bird["id"] not in self.STORIES:
            return f"📖 关于{bird['name']}，日志里没有留下多余的字。"
        bond = 0
        av = getattr(self, "aviary", {})
        if bird["id"] in av:
            bond = av[bird["id"]]["bond"]
        bond = max(bond, getattr(self, "aviary_memory", {}).get(bird["id"], 0))
        pages = self.STORIES[bird["id"]]
        unlocked = sum(1 for t in self.STORY_THRESHOLDS[:len(pages)] if bond >= t)
        if unlocked == 0:
            return f"📖 日志里确有关于{bird['name']}的残页，但字迹还辨认不清。（与它更亲近些，或许能读懂——亲密度 {bond}/{self.STORY_THRESHOLDS[0]}）"
        lines = [f"📖 {bird['name']}的日志残页（{unlocked}/{len(pages)}）："]
        for i in range(unlocked):
            lines.append(f"—— 其{'一二三'[i]} ——\n{pages[i]}")
        if unlocked < len(pages):
            nxt = self.STORY_THRESHOLDS[unlocked]
            lines.append(f"（还有字迹模糊的一页……亲密度 {bond}/{nxt}）")
        return "\n".join(lines)

    def _aviary_tick(self):
        av = getattr(self, "aviary", {})
        if not av:
            return None
        departed = []
        for bid in list(av.keys()):
            av[bid]["days"] -= 1
            av[bid]["fed_today"] = 0
            if av[bid]["days"] <= 0:
                bird = self._get_bird_by_id(bid)
                name = bird["name"] if bird else bid
                mem = getattr(self, "aviary_memory", {})
                mem[bid] = av[bid]["bond"]
                self.aviary_memory = mem
                del av[bid]
                departed.append(name)
        if departed:
            return "🏡 " + "、".join(departed) + " 在你外出观察时离开了鸟园。它记得你的好——再次邀请只需半价。"
        return None

    def _statusline(self):
        import json as _json
        enc = len(set(self.encountered))
        baits = {k.split(":")[1]: v for k, v in self.inventory.items() if v > 0}
        info = {"pts": self.points, "hab": self.current_habitat, "sea": self.season,
                "turn": self.turn, "enc": f"{enc}/{len(self.birds)}", "note": len(self.notebook), "bait": baits}
        return "\n📊 " + _json.dumps(info, ensure_ascii=False)

    def cmd(self, command: str) -> str:
        # 批量指令:; 或换行分隔,上限8条,逐条执行拼接输出
        chunks = [c.strip() for c in command.replace("\n", ";").split(";") if c.strip()]
        if len(chunks) > 1:
            outputs = []
            for c in chunks[:8]:
                outputs.append(f"▶ {c}\n" + self._one_cmd(c))
            if len(chunks) > 8:
                outputs.append("（批量指令一次最多 8 条，多余的没有执行）")
            return "\n\n".join(outputs)
        return self._one_cmd(command)

    def _one_cmd(self, command: str) -> str:
        parts = command.strip().split()
        if not parts:
            return "请输入指令。输入 help 查看帮助。"

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "help":
            return """🐦 观鸟指令：
scan [次数] [诱饵] [stop=稀有,传说,新种]  — 观察鸟，可连看1~8次
submit                              — 提交观察笔记换点数
goto <生境名>                       — 切换生境（未解锁则花费点数解锁）
shop                                — 查看可买诱饵
buy <诱饵id> [数量]                 — 买诱饵 (berries浆果/seeds种子/fish小鱼干)
inventory                           — 查看收藏和物品\nexchange <物品名|all> [数量]        — 珍羽/宝石兑换点数\nletters                             — 重读收藏的风信笺
aviary                              — 查看鸟园
invite <鸟名>                       — 邀请见过的鸟入驻（容量8席）
feed <鸟名> <诱饵> [次数]           — 喂食（可一次喂多份，如 feed 墨翎鹭 fish 5），投其所好停留更久、亲密更快
hatch [蛋名]                        — 孵化收藏的鸟蛋（2次观察破壳，喂3次长大后放归）
story <鸟名>                        — 读某只鸟的日志残页（需足够亲密；并非每只鸟都有）
note <一句话> / notes               — 随手记：写下与翻看只属于你的片段
status                              — 查看状态（点数、生境、季节等）
encyclopedia                        — 图鉴收集进度
💡 小技巧：多条指令可用分号连写一次发出（上限8条），如 scan; feed 墨翎鹭 fish 3; status
look <鸟名>                         — 细看某鸟详情
help                                — 本帮助

📖 观察须知：
· 季节随观察推进（每10次换季），有些鸟是候鸟，只在特定季节现身；
  look 已见过的鸟可查它的习性线索
· 观察有远近之分：🔭 太远，落物拾不到；🔍 极近，所获翻倍
· 🆕=新种 ✨=稀有 🌟=传说
· 每次返回末尾的 📊 状态栏即当前局面，无需反复 status"""

        if cmd == "status":
            enc = len(set(self.encountered))
            total = len(self.birds)
            note_count = len(self.notebook)
            inv_str = ", ".join([f"{k}:{v}" for k,v in self.inventory.items() if v>0]) or "无"
            return f"""📊 状态：
点数: {self.points}
生境: {self.current_habitat}
季节: {self.season}
观察次数: {self.turn}
图鉴: {enc}/{total}
笔记已提交: {note_count}
诱饵: {inv_str}
收藏: 鸟蛋{len(self.collection['鸟蛋'])} 珍羽{len(self.collection['珍羽'])} 宝石{len(self.collection['宝石'])} 风信笺{len(self.collection['风信笺'])} 迁徙图碎片{len(self.collection['迁徙图碎片'])}"""

        if cmd == "goto":
            if not args:
                all_habitats = ["芦花浅渚", "苍针岭", "平野风吟", "云栖崖", "城隅林"]
                lines = [f"🏞️ 生境列表（当前季节：{self.season}）:"]
                for h in all_habitats:
                    birds_here = [b for b in self.birds if h in b.get("habitats", [])]
                    in_season = [b for b in birds_here
                                 if "seasons" not in b or self.season in b["seasons"]]
                    unseen = [b for b in in_season if b["id"] not in self.encountered]
                    info = f"本季可见 {len(in_season)} 种，你还差 {len(unseen)} 种"
                    if len(unseen) == 0 and len(in_season) < len(birds_here):
                        info += "（换季后或有新面孔）"
                    if h in self.unlocked_habitats:
                        lines.append(f"  ✅ {h} — {info}")
                    else:
                        price = 300 if h in ["苍针岭", "平野风吟"] else 500 if h in ["云栖崖"] else 400
                        lines.append(f"  🔒 {h} (解锁需 {price} 点) — {info}")
                frags = self.collection.get("迁徙图碎片", [])
                if len(set(frags)) >= 5:
                    birds_m = [b for b in self.birds if "雾隐泽" in b.get("habitats", [])]
                    unseen_m = [b for b in birds_m if b["id"] not in self.encountered]
                    tag = "✅" if "雾隐泽" in self.unlocked_habitats else "🌫️"
                    lines.append(f"  {tag} 雾隐泽 — 你还差 {len(unseen_m)} 种")
                return "\n".join(lines)
            habitat = " ".join(args)
            frags = self.collection.get("迁徙图碎片", [])
            mist_open = len(set(frags)) >= 5
            if habitat == "雾隐泽":
                if not mist_open:
                    return f"🌫️ 你听说过这个名字，却想不起是在哪里听说的。（迁徙图碎片：{len(set(frags))}/5）"
                first = "雾隐泽" not in self.unlocked_habitats
                if first:
                    self.unlocked_habitats.append("雾隐泽")
                self.current_habitat = "雾隐泽"
                self.save()
                if first:
                    return ("🌫️ 五片旧图在你手中拼合的一瞬，你忽然想起来了——不是发现，是想起。\n"
                            "五个生境之间的雾中之地，候鸟们不出现在季节里的日子，原来在这里。\n"
                            "而雾的深处，还住着一些尚未被图鉴收编的鸟。\n"
                            "它并非被你解锁。它更像一则突然出现在你脑中的记忆。\n"
                            "✅ 你走进了雾隐泽。")
                return "✅ 你再次走进雾隐泽。雾认得你，让开了一步的宽度。"
            all_habitats = ["芦花浅渚", "苍针岭", "平野风吟", "云栖崖", "城隅林"]
            if habitat not in all_habitats:
                return f"❌ 未知生境：{habitat}。可用：芦花浅渚、苍针岭、平野风吟、云栖崖、城隅林"
            if habitat in self.unlocked_habitats:
                self.current_habitat = habitat
                self.save()
                return f"✅ 已切换到 {habitat}。"
            else:
                price = 300 if habitat in ["苍针岭", "平野风吟"] else 500 if habitat in ["云栖崖"] else 400
                if self.points < price:
                    return f"❌ 点数不足！解锁 {habitat} 需要 {price} 点，当前 {self.points} 点。"
                self.points -= price
                self.unlocked_habitats.append(habitat)
                self.current_habitat = habitat
                self.save()
                return f"✅ 解锁 {habitat} 成功！已切换至该生境。剩余 {self.points} 点。"

        if cmd == "shop":
            return """🛒 诱饵商店：
浆果 (berries)    — 20点，吸引林鸟/水鸟
种子 (seeds)      — 15点，吸引雀类/鸽类
小鱼干 (fish)     — 30点，吸引猛禽/水鸟
输入 buy <诱饵id> [数量] 购买"""

        if cmd == "buy":
            if not args:
                return "请指定诱饵。可用: berries, seeds, fish"
            bait_name = args[0].lower()
            amount = int(args[1]) if len(args) > 1 else 1
            price_map = {"berries": 20, "seeds": 15, "fish": 30}
            if bait_name not in price_map:
                return f"❌ 未知诱饵：{bait_name}，可选 berries, seeds, fish"
            total_cost = price_map[bait_name] * amount
            if self.points < total_cost:
                return f"❌ 点数不足！需要 {total_cost} 点，当前 {self.points} 点。"
            self.points -= total_cost
            key = f"诱饵:{bait_name}"
            self.inventory[key] = self.inventory.get(key, 0) + amount
            self.save()
            return f"✅ 购买了 {amount} 个 {bait_name}，剩余 {self.points} 点。"

        if cmd == "scan":
            _now = time.time()
            self.scan_times = [t for t in getattr(self, "scan_times", []) if _now - t < 60]
            if len(self.scan_times) >= 2:
                return "🫧 你的眼睛需要休息片刻。看看手边的收获，或者陪陪鸟园的住客，过一会儿再举起望远镜吧。"
            self.scans_window = [t for t in getattr(self, "scans_window", []) if _now - t < 6 * 3600]
            if len(self.scans_window) >= 100:
                return "🌙 林间暗了下来，鸟儿们都归巢了。今天的观察就到这里，过几个小时再来吧。"
            self.scan_times.append(_now)
            scan_count = 1
            bait_used = None
            stop_condition = None
            for arg in args:
                if arg.isdigit():
                    scan_count = int(arg)
                    if scan_count < 1:
                        scan_count = 1
                    if scan_count > 8:
                        scan_count = 8
                        result_note_capped = True
                elif arg.startswith("stop="):
                    stop_condition = arg.split("=")[1]
                else:
                    if arg in ["berries", "seeds", "fish"]:
                        bait_used = arg
            if bait_used:
                key = f"诱饵:{bait_used}"
                if self.inventory.get(key, 0) <= 0:
                    return f"❌ 没有 {bait_used} 诱饵了，请购买。"
                self.inventory[key] -= 1
                if self.inventory[key] < 0:
                    self.inventory[key] = 0

            result_lines = []
            if 'result_note_capped' not in dir():
                result_note_capped = False
            folded = {}
            new_birds = []
            rare_birds = []
            drops_collected = []
            total_notes = 0

            for i in range(scan_count):
                self.scans_window.append(time.time())
                if getattr(self, "active_boost", 0) == 0 and random.randint(1, 100) <= 5:
                    self.active_boost = 5
                    result_lines.append("🔥 鸟群活跃期！接下来一段时间，稀有的身影更容易现身。")
                bird = self._pick_random_bird(self.current_habitat, bait_used)
                if getattr(self, "trace_left", 0) > 0:
                    self.trace_left -= 1
                    if bird is not None and bird["id"] == getattr(self, "trace_bird", None):
                        self.trace_left = 0
                if not bird:
                    result_lines.append(f"第{i+1}次：这片区域没有鸟。")
                    self._advance_season()
                    continue
                bird_name = bird["name"]
                is_new = bird["id"] not in self.encountered
                is_rare = bird["rarity"] in ["稀有", "传说"]
                if is_new:
                    self.encountered.append(bird["id"])
                    new_birds.append(bird_name)
                if is_rare:
                    rare_birds.append(bird_name)
                behaviors = bird.get("behaviors", ["静静地待在那里。"])
                behavior = random.choice(behaviors)
                mem_bond = getattr(self, "aviary_memory", {}).get(bird["id"], 0)
                reunion = mem_bond > 0 and random.randint(1, 100) <= 15
                dist_roll = random.randint(1, 100)
                dist_tag = ""
                too_far = False
                if dist_roll <= 25 and bird.get("far"):
                    behavior = bird["far"]
                    dist_tag = "🔭"
                    too_far = True
                elif dist_roll > 85 and bird.get("near"):
                    behavior = bird["near"]
                    dist_tag = "🔍"
                if reunion:
                    if mem_bond >= 30:
                        behavior = "它在你头顶盘旋了一圈才离开——它认得你。"
                    else:
                        behavior = "它落下时朝你的方向偏了偏头，像是想起了什么。"
                    dist_tag = "💫"
                    too_far = False
                drops = None if too_far else self._pick_drop(bird)
                if dist_tag == "🔍" and drops is not None:
                    extra = self._pick_drop(bird)
                    if extra:
                        drops = drops + extra if drops else extra
                drop_text = ""
                if drops:
                    for d in drops:
                        d_type = d["type"]
                        d_name = d["name"]
                        if d_type == "珍羽":
                            self.collection["珍羽"].append(d_name)
                        elif d_type == "宝石":
                            self.collection["宝石"].append(d_name)
                        elif d_type == "鸟蛋":
                            self.collection["鸟蛋"].append(d_name)
                        elif d_type == "风信笺":
                            self.collection["风信笺"].append(d_name)
                        elif d_type == "迁徙图碎片":
                            self.collection["迁徙图碎片"].append(d_name)
                        drops_collected.append(d_name)
                    drop_text = " 获得：" + ", ".join([d["name"] for d in drops])
                if random.randint(1, 100) <= 8:
                    amb_pool = self.AMBIENCE.get(self.current_habitat)
                    if amb_pool:
                        result_lines.append("　　" + random.choice(amb_pool))
                if random.randint(1, 100) <= 5:
                    trace_pool = [b for b in self.birds
                                  if self.current_habitat in b.get("habitats", [])
                                  and b.get("trace")
                                  and b["id"] not in self.encountered
                                  and ("seasons" not in b or self.season in b["seasons"])]
                    if trace_pool:
                        tb = random.choice(trace_pool)
                        self.trace_bird = tb["id"]
                        self.trace_left = 3
                        result_lines.append(f"　　🎵 {tb['trace']}\n　　（它就在附近。接下来几次观察，留心些。）")
                if random.randint(1, 100) <= 3:
                    passing_pool = [b for b in self.birds
                                    if self.current_habitat in b.get("habitats", [])
                                    and b["rarity"] == "稀有" and b["id"] not in self.encountered]
                    if passing_pool:
                        pb = random.choice(passing_pool)
                        p_drop = random.choice(pb.get("drops", ["浮羽"]))
                        p_cat = "宝石" if "石" in p_drop else "珍羽"
                        self.collection[p_cat].append(p_drop)
                        drops_collected.append(p_drop)
                        frag = f"迁徙图碎片·{self.current_habitat}"
                        frag_text = ""
                        if frag not in self.collection["迁徙图碎片"]:
                            self.collection["迁徙图碎片"].append(frag)
                            drops_collected.append(frag)
                            frag_text = f"羽下还压着一角旧图：{frag}。"
                        result_lines.append(f"　　🌠 一只陌生的鸟破雾般掠过，短暂地停了一瞬又消失在远方——它留下了一片{p_drop}。{frag_text}（你没来得及看清它，图鉴未记录）")
                if random.randint(1, 100) <= 6:
                    nest_roll = random.randint(1, 100)
                    if nest_roll <= 35:
                        n_item, n_cat = random.choice(["柔绒羽", "斑纹羽", "流光羽"]), "珍羽"
                    elif nest_roll <= 65:
                        n_item, n_cat = random.choice(["巢边石", "衔来石"]), "宝石"
                    elif nest_roll <= 85:
                        n_item, n_cat = "风信笺", "风信笺"
                    elif nest_roll <= 95:
                        n_item, n_cat = random.choice(["素色鸟蛋", "斑点鸟蛋"]), "鸟蛋"
                    else:
                        frag = f"迁徙图碎片·{self.current_habitat}"
                        if frag in self.collection["迁徙图碎片"]:
                            n_item, n_cat = random.choice(["巢边石", "衔来石"]), "宝石"
                        else:
                            n_item, n_cat = frag, "迁徙图碎片"
                    self.collection[n_cat].append(n_item)
                    drops_collected.append(n_item)
                    if n_cat == "风信笺":
                        letter = self._letter_text(len(self.collection["风信笺"]) - 1)
                        result_lines.append(f"　　🪺 灌丛间有一个空了的旧巢，里面压着一页字迹：{letter}")
                    elif n_cat == "鸟蛋":
                        result_lines.append(f"　　🪺 你发现一个被遗落的鸟巢，里面有一枚{n_item}。你小心地把它收好——也许有一天它会需要一个家。")
                    elif n_cat == "迁徙图碎片":
                        result_lines.append(f"　　🪺 巢底压着一角泛黄的旧图，边缘是撕开的——{n_item}。图上的墨线延伸向纸外，像在指认一个不存在的方向。")
                    else:
                        result_lines.append(f"　　🪺 你发现一个空鸟巢，里面留着一件小东西：{n_item}。")
                self.notebook.append({"bird_id": bird["id"], "bird_name": bird_name, "timestamp": time.time()})
                total_notes += 1
                rarity_tag = {"普通":"", "稀有":"✨", "传说":"🌟"}.get(bird["rarity"], "")
                new_tag = "🆕" if is_new else ""
                boost_tag = "🔥" if getattr(self, "active_boost", 0) > 0 else ""
                if is_new or is_rare or dist_tag:
                    line = f"第{i+1}次：{boost_tag}{new_tag}{rarity_tag}{dist_tag}{bird_name} —— {behavior}{drop_text}"
                    result_lines.append(line)
                else:
                    folded[bird_name] = folded.get(bird_name, 0) + 1

                # 混群:8% 概率同生境其他鸟一同现身
                if random.randint(1, 100) <= 8:
                    pool_others = [b for b in self._get_birds_in_habitat(self.current_habitat) if b["id"] != bird["id"]]
                    if pool_others:
                        flockmates = random.sample(pool_others, min(random.randint(1, 2), len(pool_others)))
                        mate_names = []
                        for mate in flockmates:
                            m_new = mate["id"] not in self.encountered
                            if m_new:
                                self.encountered.append(mate["id"])
                                new_birds.append(mate["name"])
                            if mate["rarity"] in ["稀有", "传说"]:
                                rare_birds.append(mate["name"])
                            m_drops = self._pick_drop(mate)
                            if m_drops:
                                for d in m_drops:
                                    self.collection[d["type"]].append(d["name"])
                                    drops_collected.append(d["name"])
                            self.notebook.append({"bird_id": mate["id"], "bird_name": mate["name"], "timestamp": time.time()})
                            total_notes += 1
                            m_tags = ("🆕" if m_new else "") + {"普通":"", "稀有":"✨", "传说":"🌟"}.get(mate["rarity"], "")
                            mate_names.append(f"{m_tags}{mate['name']}")
                        result_lines.append(f"　　🐦 与它混群的还有：{'、'.join(mate_names)}")

                if getattr(self, "active_boost", 0) > 0:
                    self.active_boost -= 1
                    if self.active_boost == 0:
                        result_lines.append("　　🔥 鸟群渐渐散去，林间恢复了平静。")

                if stop_condition:
                    if stop_condition == "稀有" and is_rare:
                        result_lines.append(f"⏹️ 因钓到稀有/传说鸟而停止。")
                        break
                    elif stop_condition == "传说" and bird["rarity"] == "传说":
                        result_lines.append(f"⏹️ 因钓到传说鸟而停止。")
                        break
                    elif stop_condition == "新种" and is_new:
                        result_lines.append(f"⏹️ 因发现新种而停止。")
                        break

                self._advance_season()

            hatch_msg = self._hatch_tick()
            if hatch_msg:
                result_lines.append(hatch_msg)
            tick_msg = self._aviary_tick()
            if tick_msg:
                result_lines.append(tick_msg)
            if folded:
                result_lines.append("　　另外照面：" + "、".join(f"{k}×{v}" for k, v in folded.items()))
            if result_note_capped:
                result_lines.append("🌇 天色不早了，今天先记到这里吧。（单次连看上限 8 次，想继续再喊一声 scan）")
            summary = f"\n📝 本轮记录 {total_notes} 份笔记，新种 {len(new_birds)} 种，稀有 {len(rare_birds)} 种，拾得 {len(drops_collected)} 件。"
            if new_birds:
                summary += f" 新种：{', '.join(new_birds)}"
            self.save()
            return "\n".join(result_lines) + summary + self._statusline()

        if cmd == "submit":
            if not self.notebook:
                return "📭 你还没有观察笔记可以提交。先去观察吧。"
            count = len(self.notebook)
            base_points = count * 10
            seen = set()
            new_species_bonus = 0
            for note in self.notebook:
                bid = note["bird_id"]
                if bid not in seen:
                    seen.add(bid)
                    bird = self._get_bird_by_id(bid)
                    if bird:
                        if bird["rarity"] == "稀有":
                            new_species_bonus += 20
                        elif bird["rarity"] == "传说":
                            new_species_bonus += 50
            total_points = base_points + new_species_bonus
            self.points += total_points
            self.notebook = []
            self.save()
            return f"📤 提交了 {count} 份观察笔记，获得 {base_points} 基础点 + {new_species_bonus} 新种加成 = {total_points} 点。" + self._statusline()

        if cmd == "aviary":
            return self._aviary_view()

        if cmd == "invite":
            return self._invite(args)

        if cmd == "note":
            if not args:
                return "✏️ 想记点什么？note <一句话>，写给你自己的随手记。"
            text = " ".join(args)[:200]
            notes = getattr(self, "field_notes", [])
            notes.append({"t": f"{self.season}·{self.current_habitat}", "txt": text})
            if len(notes) > 50:
                notes = notes[-50:]
            self.field_notes = notes
            self.save()
            return f"✏️ 记下了。（随手记 {len(notes)}/50）"

        if cmd == "notes":
            notes = getattr(self, "field_notes", [])
            if not notes:
                return "📓 随手记还是空的。note <一句话> 随时可写，这里只属于你。"
            lines = [f"📓 随手记（{len(notes)}/50）："]
            for i, n in enumerate(notes, 1):
                lines.append(f"  {i}. [{n['t']}] {n['txt']}")
            return "\n".join(lines)

        if cmd == "story":
            return self._story(args)

        if cmd == "hatch":
            if not args:
                eggs = [e for e in self.collection["鸟蛋"]]
                if not eggs:
                    return "🥚 你还没有鸟蛋。它们偶尔会出现在被遗落的旧巢里（🪺）。"
                return "🥚 你收藏的蛋：" + "、".join(eggs) + "。用 hatch <蛋名> 开始孵化。"
            return self._hatch_start(" ".join(args))

        if cmd == "feed":
            if args and args[0] == "雏鸟":
                bait = args[-1].lower()
                if bait not in ["berries", "seeds", "fish"]:
                    return "❌ 喂什么呢？feed 雏鸟 <berries/seeds/fish>"
                return self._hatch_feed(bait)
            return self._feed(args)

        if cmd == "exchange":
            return self._exchange(args)

        if cmd == "letters" or (cmd == "read" and args and "笺" in " ".join(args)):
            letters = self.collection.get("风信笺", [])
            if not letters:
                return "📭 你还没有收到过风信笺。它们偶尔会出现在被遗落的旧巢里。"
            lines = [f"📜 你收藏的风信笺（{len(letters)} 页）："]
            for i in range(len(letters)):
                lines.append(f"  第{i+1}页 {self._letter_text(i)}")
            return "\n".join(lines)

        if cmd == "inventory":
            lines = ["🎒 背包："]
            for k, v in self.inventory.items():
                if v > 0:
                    lines.append(f"  {k}: {v}")
            for k, v in self.collection.items():
                if v:
                    lines.append(f"  {k}: {len(v)} 件 ({', '.join(v[:3])}{'...' if len(v)>3 else ''})")
            if len(lines) == 1:
                return "🎒 背包空空如也。"
            return "\n".join(lines)

        if cmd == "encyclopedia":
            total = len(self.birds)
            enc = len(set(self.encountered))
            habitats = ["芦花浅渚", "苍针岭", "平野风吟", "云栖崖", "城隅林"]
            if "雾隐泽" in self.unlocked_habitats:
                habitats.append("雾隐泽")
            if args:
                h = " ".join(args)
                if h not in habitats:
                    return f"❌ 没有这个生境。可查:{('、'.join(habitats))}"
                birds_in_h = [b for b in self.birds if h in b.get("habitats", [])]
                seen = [b["name"] for b in birds_in_h if b["id"] in self.encountered]
                unseen_n = len(birds_in_h) - len(seen)
                lines = [f"🏞️ {h}: 已见 {len(seen)}/{len(birds_in_h)}"]
                if seen:
                    lines.append(f"   ✅ {', '.join(seen)}")
                if unseen_n:
                    lines.append(f"   ❓ 还有 {unseen_n} 种未见")
                return "\n".join(lines)
            lines = [f"📖 图鉴进度: {enc}/{total}（encyclopedia <生境名> 看名单）"]
            for h in habitats:
                birds_in_h = [b for b in self.birds if h in b.get("habitats", [])]
                seen_n = len([b for b in birds_in_h if b["id"] in self.encountered])
                lines.append(f"  {h} {seen_n}/{len(birds_in_h)}")
            return "\n".join(lines)

        if cmd == "look":
            if not args:
                return "你想看哪种鸟？输入名字或id。"
            query = " ".join(args)
            match = None
            for b in self.birds:
                if b["id"] == query or b["name"] == query:
                    match = b
                    break
                if query in b["name"]:
                    match = b
                    break
            if not match:
                return f"❌ 未找到鸟类：{query}"
            seen = match["id"] in self.encountered
            if not seen:
                hint = ""
                if "seasons" in match and self.season not in match["seasons"]:
                    hint = "不过，这个季节似乎寻不到它的踪迹，再等等吧。"
                return f"❓ {match['name']} —— 你还没见过这种鸟呢。去 {match['habitats'][0]} 寻找吧。{hint}"
            lines = [
                f"🐦 {match['name']} ({match.get('species','')})",
                f"稀有度: {match['rarity']}",
                f"描述: {match.get('description','')}",
                f"常见行为: {random.choice(match.get('behaviors',['']))}",
                f"分布: {', '.join(match.get('habitats',[]))}"
            ]
            return "\n".join(lines)

        return f"❌ 未知指令：{cmd}。输入 help 查看可用指令。"
