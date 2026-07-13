# 🎣 文字钓鱼 · AI 远程 MCP 版（Docker 部署）

把 [tutusagi/ai-fishing-game](https://github.com/tutusagi/ai-fishing-game) 这个**确定性、单文件、给 AI 玩的文字钓鱼引擎**，包成了一个**远程 MCP server**——让 [claude.ai](https://claude.ai)、Claude Desktop 以及任何支持「自定义 MCP 连接器 / Streamable HTTP」的客户端，直接连上来玩。你的 AI 伴侣买饵、抛竿、潜水、集图鉴，进度跨对话不丢。

> 本仓库在原项目基础上**只加了 MCP / Docker 化的一层封装**，引擎本体（`engine.py` / `fishing.py`）一行未改。游戏玩法、指令、确定性等一切规则均来自原项目，详见下文「游戏说明」。

---

## 与原项目的关系

| | 原项目 [tutusagi/ai-fishing-game](https://github.com/tutusagi/ai-fishing-game) | 本仓库（mumuer1024/ai-fishing-game） |
|---|---|---|
| 引擎 | `engine.py`（可读源码）+ `fishing.py`（盲玩版） | **原样沿用，未改动** |
| 接 AI 的方式 | 三种草图：代码解释器 / 函数调用 / 自写循环 | **统一为远程 MCP**：Docker 起一个 FastMCP server，客户端连 URL 即可 |
| 新增内容 | — | `examples/mcp-server/`：`server.py` 工具封装 + `Dockerfile` + `compose.yaml` + 三种联网入口指南 |
| 存档 | `fishing_save.json`（与脚本同目录） | 落在容器挂载目录 `app/fishing_save.json`，重启不丢 |

如果你只想读 / 改引擎，或想要纯本地的「代码解释器 / 函数调用」接法，请直接看原项目 README。本仓库的关注点是**怎么把它部署成一个长期在线的 MCP 服务**。

---

## 仓库里有什么

```
.
├── engine.py                # 引擎可读源码（原项目）—— 改数值 / 加鱼加地点看这个
├── fishing.py               # 盲玩版（engine.py 的 base64 打包，防剧透）—— 给 AI 玩用这个
├── build_blind.py           # 从 engine.py 重新生成 fishing.py 的小脚本
├── tool-schema.json         # play_fishing 工具的 JSON Schema（函数调用接法参考）
├── examples/
│   ├── play_with_code_interpreter.md   # 「代码解释器盲玩」接法示例（原项目）
│   └── mcp-server/                     # ★ 本仓库新增：Docker / MCP 化
│       ├── README.md        # 详细的部署入口指南（方法 A/B/C）
│       ├── Dockerfile
│       ├── compose.yaml     # 三种入口都在注释里，按需开关
│       ├── requirements.txt # mcp
│       ├── .gitignore       # 忽略运行时复制进来的引擎文件和存档
│       └── app/
│           └── server.py    # MCP 封装（环境变量配置，无需改代码）
```

> `app/` 下默认只有 `server.py`。部署时把根目录的 `fishing.py`（或 `engine.py`）复制进去——引擎文件不重复纳入版本库。

---

## 快速开始（Docker 部署 MCP）

需要一台能跑 Docker + Docker Compose 的机器。

### 1. 放引擎文件

把仓库根目录的引擎复制到 `examples/mcp-server/app/` 下（盲玩与完整二选一，也可都放）：

```bash
cd examples/mcp-server
cp ../../fishing.py app/      # 盲玩版（推荐，防剧透）
# cp ../../engine.py app/     # 完整版（可选，模型可读鱼谱概率）
```

### 2. 设密钥 + 选引擎

先生成一串随机密钥当门禁：

```bash
openssl rand -hex 16
```

打开 `compose.yaml`，把它填进 `FISHING_PATH`（**记得保留开头的 `/`**），并按需设 `FISHING_ENGINE`：

```yaml
FISHING_PATH:   "/3f9a8c5d2e7b1a4f6c0d9e8b7a6f5e4d"   # ← 换成你刚生成的
FISHING_ENGINE: "fishing"                             # fishing=盲玩 / engine=完整
```

### 3. 起容器

```bash
docker compose up -d --build
docker compose logs -f fishing-mcp     # 看到 Uvicorn 监听 0.0.0.0:3457 就对了
```

### 4. 本机自测

```bash
# 打密钥路径：期望 HTTP 406（端点活着，只是 GET 没带 Accept 头——这是好消息，不是报错）
curl -s -o /dev/null -w "secret -> HTTP %{http_code}\n"  http://127.0.0.1:3457/<你的密钥>

# 打默认 /mcp：期望 404（说明 endpoint 已搬到密钥路径上 = 配置生效）
curl -s -o /dev/null -w "/mcp   -> HTTP %{http_code}\n"  http://127.0.0.1:3457/mcp
```

> **划重点**：`406 Not Acceptable` 代表「路径存在、只是你用 GET 且没带 `Accept: application/json, text/event-stream`」。真正代表「路径不对」的是 **404**。后面每一步都靠 **406 vs 404** 来判断通没通。

到这里后端就绪。接下来选一种入口把它接出去。

---

## 选择入口方式（三选一）

### 方法 A — Cloudflare Tunnel

适合：**有域名、想要免费 HTTPS、不想在防火墙上开端口。**

前提：你已经用 cloudflared（容器形态）跑着一条隧道。让钓鱼服务和 cloudflared **同处一个 Docker 网络**，靠容器名互访。

1. 查到 cloudflared 所在的网络名：
   ```bash
   docker inspect <cloudflared或同网容器> --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}'
   ```
2. 编辑 `compose.yaml`：**删掉 `ports` 段**，并取消末尾 `networks` 注释、把 `name` 换成上面查到的网络名。`FISHING_HOST` 保持 `0.0.0.0`。然后 `docker compose up -d`（改了网络要重建）。
3. 在 Cloudflare 隧道里加一条 Public Hostname / 已发布应用程序路由：
   - 子域 + 域：如 `fishing` + `example.com`
   - **路径（Path）：留空**（密钥已经在后端 endpoint 里了，这里别再填，否则要求 URL 出现两次密钥，反而不匹配）
   - Service：`HTTP` → `fishing-mcp:3457`（**用容器名**，不是 `127.0.0.1`）

> ⚠️ 最常见的坑：cloudflared 容器内部的 `127.0.0.1` 指的是**它自己**，不是宿主机。所以要么像上面这样同网络用容器名，要么让钓鱼服务走 host 网络后用宿主机网关 IP（如 `172.17.0.1:3457`）。

验证（从公网打）：

```bash
curl -s -o /dev/null -w "tunnel -> HTTP %{http_code}\n" https://fishing.example.com/<你的密钥>
```

`406` = 整条链路通；`530/502` = 隧道没接到后端（多半 Service 地址/端口不对）；`404` = Path 填了不该填的东西。

### 方法 B — 传统反代（Nginx / Caddy）

适合：**机器上已有反代，或想直接在 VPS 上签 HTTPS。**

把 `FISHING_HOST` 设回 `127.0.0.1`（只听本机，对外交给反代），`compose.yaml` 的 `ports` 保持 `127.0.0.1:3457:3457`。

**Nginx**（Streamable HTTP 可能走 SSE，下面几条指令缺一不可）：

```nginx
location /<你的密钥> {
    proxy_pass http://127.0.0.1:3457;   # 末尾不写路径，让 /<密钥> 原样透传给后端
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Connection "";
    proxy_buffering off;                # 流式必须关
    proxy_cache off;
    proxy_read_timeout 3600s;
    chunked_transfer_encoding on;
}
```

**Caddy**（自动 HTTPS，更短；后端只在 `/<密钥>` 上应答，其余自然 404）：

```caddy
fishing.example.com {
    reverse_proxy 127.0.0.1:3457
}
```

重载后验证：`curl -s -o /dev/null -w "%{http_code}\n" https://fishing.example.com/<你的密钥>` → `406` 即通。

### 方法 C — 纯本地 / 局域网 / Tailscale

适合：**只在内网或本机用，不出公网。**

把 `compose.yaml` 的 `ports` 改成 `"3457:3457"`（暴露给内网），客户端直接连：

```
http://<内网IP 或 Tailscale IP>:3457/<你的密钥>
```

**最轻方案（连 Docker 都不要）**：本地客户端（如 Claude Desktop）可以用 **stdio** 直接拉起脚本。把 `server.py` 末尾换成 `mcp.run(transport="stdio")`，把引擎文件和 `server.py` 放一起，然后在客户端配置里：

```json
{
  "mcpServers": {
    "fishing": {
      "command": "python",
      "args": ["/绝对路径/app/server.py"]
    }
  }
}
```

stdio 模式不需要密钥/端口/网络，进程由客户端本地启动。

---

## 接入客户端

MCP server 说的是标准 MCP 协议（Streamable HTTP，亦可切 stdio），所以任何兼容 MCP 的客户端都能接。远程 URL 接法的地址统一是：

```
https://fishing.example.com/<你的密钥>             # 公网 / 隧道 / 反代
http://<内网IP 或 Tailscale IP>:3457/<你的密钥>     # 局域网（方法 C）
```

> 注意 URL **不用**再补 `/mcp`——密钥路径本身就是 endpoint。

### claude.ai

设置 → 连接器 → 添加自定义连接器 → URL 填上面的完整地址。新开一段对话、启用这个连接器，丢一句让它开钓：

> 你现在能玩钓鱼了。先 `status` 看看，再帮我连钓 10 竿、钓到稀有就停，回来跟我汇报战况。🎣

### ChatGPT

ChatGPT 用「自定义连接器（Custom Connector）」接远程 MCP，需先开 Developer Mode（不开的话聊天里调不出自定义 MCP 连接器）：

1. **开 Developer Mode**：头像菜单 → Settings → Connectors → Advanced（高级）→ 打开 Developer Mode。
2. **新建连接器**：Settings → Connectors → Create / New Connector → 填 Name、Description，URL 填上面的完整地址（含密钥路径）。
3. **认证方式选「No authentication（无认证）」**——密钥已经嵌在 URL 路径里了，不需要再走 OAuth。（若你在反代层加了 Basic Auth / OAuth，则选对应认证方式。）
4. 保存后在聊天里搜索并启用这个连接器即可。

> 「No auth」的自定义连接器是**每个用户私有**的——别人没法直接共享，得各自添加并连接（这点和 claude.ai 的连接器一致）。

### 其它兼容 MCP 的客户端

Claude Desktop、Cursor、VS Code（Copilot）、Windsurf、Claude Code、Cline 等，只要支持**远程 Streamable HTTP** 的，都填同一个 URL。各客户端配置入口不同（GUI 连接器管理 / 设置里的 MCP servers / `claude mcp add` 命令等），具体看该客户端的 MCP 文档——关键是把上面那个含密钥的 URL 作为远程 MCP server 地址填进去。

**只支持本地 stdio 的客户端**：走「方法 C」最末尾的 stdio 方案——把 `server.py` 末尾改成 `mcp.run(transport="stdio")`，引擎文件和 `server.py` 放一起，在客户端配置里用 `python server.py` 拉起进程。stdio 不需要密钥 / 端口 / 网络，进程由客户端本地启动。

### 暴露的工具

MCP server 对外暴露两个工具（无论远程还是 stdio 都一样）：

- `play_fishing(command)` — 传一条游戏指令，返回结果文字（引擎的 `cmd()`）。
- `new_game(seed)` — 重开一局（可指定种子；会清掉现有存档，慎用）。

---

## 常见坑（FAQ）

- **`406` 不是报错。** 它表示「路径存在、只是 GET 没带 `Accept` 头」。真正「路径不对」是 **404**。整个流程都靠 406 vs 404 判断。
- **`FISHING_HOST` 该填啥？** 容器间 / 隧道访问要 `0.0.0.0`；只本机反代可填 `127.0.0.1`。拿不准就用 `0.0.0.0` 配合密钥门禁 + 防火墙。
- **cloudflared 容器里的 `127.0.0.1` 是它自己**，不是宿主机。用同网络容器名（推荐），或宿主机网关 IP。
- **CF 路由的 Path 要留空。** 密钥已在 endpoint，重复填会导致不匹配。
- **改了 `server.py` 用 `docker compose restart`** 就行（代码是挂载进去的）；只有改 `Dockerfile` 或依赖才需要 `up -d --build`。
- **存档持久化**靠挂载 `./app:/app`——存档落在 `app/fishing_save.json`，重启不丢。记得 gitignore 它（`examples/mcp-server/.gitignore` 已带）。
- **单存档 = 所有对话共享同一局**，持续经营、跨对话不丢。想「每个客户端各玩各的」见下方「进阶」。

---

## 安全说明

密钥路径是这里唯一的门禁（security through obscurity）：**别把含密钥的 URL 外泄**，配合防火墙 / Fail2ban 足够个人玩。要更强的访问控制，可在反代层加 Basic Auth，或用 Cloudflare Access 给隧道加一层身份校验。

---

## 游戏说明

> 以下内容来自原项目 [tutusagi/ai-fishing-game](https://github.com/tutusagi/ai-fishing-game)，规则与引擎完全一致。

### 这是什么 / 为什么是「给 AI 玩」

- **确定性**：内置 mulberry32 PRNG，状态全部序列化进存档。**同一个种子 + 同一串指令 = 逐位可复现的结果**。便于复盘、测试、分享同一局。
- **盲玩**：可以让 AI 在**不剧透**的前提下玩——它不知道有哪些鱼、稀有鱼在哪、概率多少，全靠一竿一竿亲手发现（远程 MCP 下模型本就读不到文件，盲玩天然成立）。
- **存档独立**：游戏状态存在磁盘文件里，**不在对话上下文里**。AI 的对话被清空，钓鱼进度也不会丢。
- **省 token**：支持一次「连钓 N 竿」，只回一个汇总；还能用 `;` 或换行把多条指令串成一批一次跑。每次返回末尾附一行紧凑 `📊` 状态栏 JSON，AI 看它就够、不必反复查状态。

### 玩法概览

买饵 → 抛竿（`cast`）→ 按稀有度钓上各种鱼 → 卖鱼换点数 → 解锁新水域 → 集齐图鉴。每个地点 + 季节出的鱼不同（季节随抛竿数推进）；抛竿偶遇漂流瓶 / 宝箱 / 宝物；钓到鱼时小概率触发幸运时刻（分裂鱼钩 / 渔获热潮 / 河神祝福等）。后期可买氧气瓶 `dive` 潜水远征，捕获只在水下出没的鱼，途中遇「大遗迹」会暂停让你 `choose` 抉择。开局：200 点 + 普通蚯蚓×5，在「月光池塘」（和「芦苇河」已解锁）。

内容规模：55 种水面鱼（6 档稀有度）+ 22 种潜水专属水下鱼 + 14 种水下奇遇（含 5 个带抉择的「大遗迹」）+ 25 件宝物 + 11 个钓点（2 免费 + 9 个 200~800 点解锁）+ 4 季节 + 3 种鱼饵 + 氧气瓶。

### 指令清单（传给 `play_fishing` 的 `command`）

| 指令 | 作用 |
|---|---|
| `help` | 看规则 |
| `status` | 点数 / 地点 / 季节 / 鱼饵 / 图鉴进度 |
| `shop` | 看可买鱼饵 |
| `buy <饵id> [数量]` | 买饵，如 `buy glow_bait 2`；买氧气瓶 `buy oxygen 5` |
| `cast [饵id] [次数] [stop=new,rare,event]` | 抛竿。不填饵=用最便宜的；带次数=连钓 N 竿（1~20）；`stop=` 遇新种(new)/稀有(rare)/事件(event=漂流瓶·宝箱·宝物·水下奇遇)就提前停，可逗号多选 |
| `dive [带几瓶] [stop=...]` | 开潜水远征（先 `buy oxygen`）。带 N 瓶氧气下水捕水下鱼；遇大遗迹暂停 |
| `choose <编号>` | 在大遗迹处抉择（每个选项耗不同氧气；不带编号=重看选项） |
| `surface` | 主动结束远征、上浮上岸 |
| `goto` | **不带参数 = 列出所有钓点**（价格 / 本季还有几种没见过的鱼，含单列的传说级） |
| `goto <地点id>` | 前往该地点（未解锁则花点数解锁） |
| `inventory` | 渔篓 + 物品 + 待开宝箱 |
| `sell <实例id> \| sell all \| sell species <鱼id> \| sell item <物品id>` | 卖鱼 / 卖财宝换点数 |
| `open <宝箱uid>` | 打开钓上来的宝箱 |
| `encyclopedia` | 图鉴收集进度 |
| `look <id或中文名>` | 细看鱼 / 地点 / 鱼饵 / 季节 / 物品（没钓到的鱼显示 ？？？） |
| `A; B; C`（`;` 或换行串联） | 把多条指令排成一批、一次按序执行（最多 8 条），如 `buy basic_worm 10; cast 10` |

### 省 token 技巧（重点）

AI 一竿一条消息会反复来回烧上下文。用 `cast <次数>` 一次连钓：

```
cast 10                       # 连钓 10 竿
cast glow_bait 15 stop=rare   # 用夜光饵连钓 15 竿，钓到稀有及以上就停
buy basic_worm 10; cast 10    # 先买 10 个蚯蚓，再连钓 10 竿（; 串成一批一次跑）
```

返回是**一个汇总**：新种 / 稀有 / 事件 / 换季这些**精彩时刻留完整文案**，重复的杂鱼和空军**折叠成一行清点**。每次 `cmd()` 返回的**末尾都有一行**紧凑机读状态栏，AI 看它就够、不必再单独 `status`：

```
📊 {"pts": 270, "loc": "芦苇河", "sea": "春", "turn": 6, "enc": "5/55", "bait": {"basic_worm": 2}, "hold": 6}
```

`pts` 点数 · `loc/sea` 当前地点/季节 · `turn` 回合 · `enc` 图鉴进度 · `bait` 余饵 · `hold` 未卖渔获条数（有待开宝箱时多一个 `chest`）。

### 存档 & 确定性

- 状态存在**和脚本同目录**的 `fishing_save.json`（容器里即 `app/fishing_save.json`）。删掉它 = 从头开始。
- 确定性：mulberry32 PRNG，随机状态序列化进存档。**同 seed + 同指令序列 → 结果完全一致**。默认种子 `0x9e3779b9`。
- 任何输入都安全：`cmd("...")` 对乱七八糟的指令也只会**返回一句提示文字**，不会抛异常炸栈；存档读/写出问题也会在返回里**明确告诉你**，不会假装存好了。

---

## 改造 / 扩展

**改引擎**：所有内容（鱼 / 地点 / 鱼饵 / 季节 / 事件 / 物品）都是 `engine.py` 顶部的纯数据表，加内容只改数据、不动逻辑。改完 `engine.py` 后，如果你用盲玩版，跑一下让它跟上：

```bash
python build_blind.py     # 从 engine.py 重新生成 fishing.py
```

`fishing.py` 的内容就是 `engine.py` 的 base64，两份永远一致、不会分叉。改完记得把新文件重新复制进 `examples/mcp-server/app/` 并 `docker compose restart fishing-mcp`。

**配置 MCP server**：`server.py` 全走环境变量，无需改代码——

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `FISHING_HOST` | `0.0.0.0` | 监听地址（容器间/隧道要 `0.0.0.0`；只本机反代可 `127.0.0.1`） |
| `FISHING_PORT` | `3457` | 监听端口 |
| `FISHING_PATH` | `/mcp` | endpoint 路径，**强烈建议设成一长串随机值当门禁**（`openssl rand -hex 16`） |
| `FISHING_ENGINE` | `fishing` | `fishing`=盲玩（推荐）/ `engine`=完整（模型可读鱼谱概率） |

### 进阶

- **完整版 vs 盲玩**：`FISHING_ENGINE=engine` 让模型能读到鱼谱与概率；默认 `fishing` 把内容藏在打包数据里，模型只能靠抛竿亲手发现。
- **确定性复盘**：`new_game(seed)` + 同一串指令序列，结果逐位可复现。想让别的模型「重走某一局」，给同样的 seed 和指令即可。
- **多会话隔离**：当前是单存档。若想让每个客户端/对话各有独立进度，需要把存档目录按会话隔离（例如为每个实例起一个独立容器 + 独立挂载目录，或改造存档路径按 key 分目录）。

---

## 致谢

游戏引擎与全部玩法内容来自原项目 **[tutusagi/ai-fishing-game](https://github.com/tutusagi/ai-fishing-game)**，本仓库仅在其基础上增加了 Docker / 远程 MCP 的部署封装。引擎相关的详细说明、更新日志与设计思路请看原项目。

## License

MIT，详见 `LICENSE`。随便用、随便改、随便接到你和你 AI 的小日子里。🎣
