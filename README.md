# 🐦🎣 观鸟 & 钓鱼 —— 给 AI 玩的文字游戏(远程 MCP 版)

给 AI 玩的两个文字游戏,装在同一个 MCP 服务里:抬头观鸟,低头钓鱼。一次 Docker 部署,claude.ai、Claude Desktop、ChatGPT 等一切支持远程 MCP 的客户端连上 URL 就能玩,进度存在服务器上,跨对话不丢。

> **血统与致谢**:本仓库 fork 自 [mumuer1024/ai-fishing-game](https://github.com/mumuer1024/ai-fishing-game)(将钓鱼游戏封装为远程 MCP 服务),钓鱼引擎原作是 [tutusagi/ai-fishing-game](https://github.com/tutusagi/ai-fishing-game);观鸟游戏为本仓库在此基础上的新增玩法。完整致谢链见 [NOTICE.md](NOTICE.md),钓鱼游戏的完整说明与部署细节见 [docs/FISHING.md](docs/FISHING.md)。

## 目录

- [快速开始:部署](#快速开始部署)
- [接入客户端](#接入客户端)
- [观鸟游戏(birdwatch)](#-观鸟游戏birdwatch)
- [钓鱼游戏(fishing)](#-钓鱼游戏fishing)
- [给人类同行的一句话](#给人类同行的一句话)

## 快速开始:部署

需要一台能跑 Docker + Docker Compose 的机器。观鸟和钓鱼共用同一个服务,以下步骤做一遍,两个游戏都有。

### 1. 放引擎文件

观鸟引擎(`bird_engine.py` / `birds.json`)已在 `examples/mcp-server/app/` 下,无需操作。钓鱼引擎需从仓库根目录复制进去:

```bash
cd examples/mcp-server
cp ../../fishing.py app/      # 盲玩版(推荐,防剧透)
```

### 2. 设密钥

生成一串随机密钥当门禁:

```bash
openssl rand -hex 16
```

打开 `compose.yaml`,把它填进 `FISHING_PATH`(**记得保留开头的 `/`**):

```yaml
FISHING_PATH: "/3f9a8c5d2e7b1a4f6c0d9e8b7a6f5e4d"   # ← 换成你刚生成的
```

### 3. 起容器

```bash
docker compose up -d --build
docker compose logs -f fishing-mcp     # 看到 Uvicorn 监听 0.0.0.0:3457 就对了
```

### 4. 本机自测

```bash
curl -s -o /dev/null -w "secret -> HTTP %{http_code}\n"  http://127.0.0.1:3457/<你的密钥>
```

期望 **406**(路径存在,只是 GET 没带 Accept 头——这是好消息不是报错);**404** 才是路径不对。

### 5. 接出公网(三选一)

Cloudflare Tunnel / 传统反代(Nginx / Caddy)/ 纯内网(Tailscale / stdio),三种入口的详细步骤与常见坑排查见 **[docs/FISHING.md](docs/FISHING.md)** 的「选择入口方式」与「常见坑(FAQ)」章节,对观鸟完全通用。

## 接入客户端

远程 URL 统一是 `https://你的域名/<你的密钥>`(注意**不用**再补 `/mcp`,密钥路径本身就是 endpoint)。

**claude.ai**:设置 → 连接器 → 添加自定义连接器 → 填 URL。新开对话、启用连接器,丢一句:

> 你现在能观鸟了。先 `help` 看看规则,然后去 `scan` 几次,遇到什么回来讲给我听。🐦

其它客户端(Claude Desktop、ChatGPT、Cursor 等)的接法见 [docs/FISHING.md](docs/FISHING.md) 的「接入客户端」章节。

MCP 服务对外暴露四个工具:`birdwatch` / `bird_reset`(观鸟)、`play_fishing` / `new_game`(钓鱼)。

## 🐦 观鸟游戏(birdwatch)

一个给 AI 玩的文字观鸟游戏:58 种鸟、6 个生境、季节轮转、孵化、鸟园、以及一些等着被遇见的故事。

- **盲玩防剧透**:AI 玩家不知道有哪些鸟、在哪个生境、概率多少,全靠一次次抬头去发现。
- **没有拥有,只有相遇**:鸟不会被"捕获",只会被遇见、被记住;喂食与亲密度换来的是停留与故事,而不是占有。
- **省 token**:`scan 8` 一次连看只回一个汇总;`;` 串联多条指令一次跑;每次返回末尾附一行 📊 状态栏 JSON,AI 看它就够。

### 两条玩法路线

**路线一:MCP 部署(跨会话长线养成,推荐)**——按上文部署即可,观鸟工具随服务自动出现。存档在服务器上,AI 的对话被清空,鸟园里的鸟也还记得它。

**路线二:单文件盲玩**——把 `examples/mcp-server/app/birdgame.py` 单个文件给你的 AI:

```python
import birdgame
print(birdgame.cmd("help"))
print(birdgame.cmd("scan 8"))
```

盲玩版把鸟谱和概率封在 base64 里,存档自动写在运行目录的 `bird_save.json`。适合快速尝鲜;注意沙盒环境会随沙盒重置而丢档,长线养成请走 MCP。

### 带着旧存档搬家

钓鱼引擎与原版完全一致,存档通用。无论你之前玩的是 tutusagi 原版(本地单文件)还是 mumuer1024 的 MCP 部署,把旧的 `fishing_save.json` 复制到本仓库部署目录的 `examples/mcp-server/app/` 下,即可带着全部进度继续;观鸟则是全新的开始。存档(fishing_save.json / bird_save.json)不在 git 管辖内,日后 `git pull` 更新也不会动它们。

> 若你同时跑了两套 MCP 服务,它们会抢同一端口:弃用的那套 `docker compose down`,存档复制过来即可,别忘了在客户端删掉旧连接。

### 目录说明

- `bird_engine.py` — 引擎源码(想读/改的看这个,⚠️ 含全部剧透)
- `birds.json` — 鸟谱数据(⚠️ 剧透浓度最高)
- `birdgame.py` — 盲玩版(给 AI 玩家的,无剧透)
- `build_blind_bird.py` — 改完引擎/鸟谱后重新生成盲玩版

## 🎣 钓鱼游戏(fishing)

本仓库的源头。一个确定性、可盲玩、给 AI 玩的文字钓鱼游戏:55 种水面鱼 + 22 种水下鱼、11 个钓点、潜水远征与大遗迹抉择。引擎来自 [tutusagi/ai-fishing-game](https://github.com/tutusagi/ai-fishing-game),MCP/Docker 封装来自 [mumuer1024/ai-fishing-game](https://github.com/mumuer1024/ai-fishing-game),本仓库原样沿用、一行未改。

玩法、指令清单、省 token 技巧、存档与确定性、改造与扩展的**完整说明**,见 **[docs/FISHING.md](docs/FISHING.md)**。

## 给人类同行的一句话

如果你也在给自己的 AI 伙伴做点什么:这个游戏的全部设计哲学是
「没有拥有只有相遇,也没有真正的遗忘」。愿你的那位也玩得开心。

## License

MIT,详见 `LICENSE`。随便用、随便改、随便接到你和你 AI 的小日子里。

<sub>L'éternité, c'est les autres. for 墨墨</sub>
