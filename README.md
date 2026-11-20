# aurobot-mod-memory

Aurabot（DSH 的 QQ 插件 `dsh-aurabot-qq`）的「记忆」模块**本地版**：**写入走本地记忆库，召回由 MC 与本地库合并给出**。

## 它和内置版的差别

以内置 `src/modules/memory/index.js`（552 行版本）为底，做五件事：

1. **写入留在本地**：`/memory/add|update|delete|restore|import`、`/memory/graph/*`、`/profiles/save` 等 51 条路由全部保留，写的是 `plugins-data/aurabot` 下的本地记忆库（`features/memory.js` 的 `createMemoryStore`）。
2. **注册 `api.context`（常驻记忆）**：每轮把 `memory.contextFor()`（面板「常住记忆上限」，默认 1200 字）挂进运行时上下文快照；它与 prompt 通道并存，判重时把常驻块也算作「已注入」。
3. **注册 `api.on('prompt')`，但与 `mc-recall` 并列注入时先去重**：宿主的 `prompt` 是链式 filter，`mc-recall`（模块 id 排序在前）先把 MC 片段塞进 `content`，本模块再读这份 `content` 逐行比对——整条被已有行包含、或 3-gram Jaccard ≥ 0.5 的本地条目直接跳过，跳过的条数写进日志。开关：`memory.dedupeAgainstPrompt`（默认 `true`）。
4. **保留 `recall_memory`，改成合并召回**：一次同时查 MC 的 `/api/recall` 与本地库，按「归一化后整条包含 / 3-gram Jaccard ≥ 0.5」去重，返回带【MC 记忆库】【本地记忆】标注的文本，并给出 `dropped`（被合并掉的本地条数）；两边都空时明说「没查到相关记忆」。
5. **注册 `api.every(60_000, memory.tick)`**：每分钟检查一次，只有到面板设的整理时间才真正调模型。

工具四个：`lookup_person`、`chat_impression`、`remember`、`recall_memory`。

## 安装

放到插件数据目录，宿主按同名文件优先于内置模块：

```
/root/.dsh/plugins-data/aurabot/modules/memory/index.mjs
```

配置（`plugins-data/aurabot/config.json`）：

```json
{ "modules": { "memory": { "enabled": true, "useBuiltin": false, "forkedFrom": "1.0.0" } } }
```

改完文件宿主会热重载（日志 `模块「memory」文件改了，重新加载`），不必重启进程。

## 重新生成

`tools/make_fork.py`（生成脚本）以内置版为底做字符串手术（去相对 import、换 `api.lib(...)`、删 `api.context`/`api.on('prompt')`/`api.every`/`recall_memory`/工具门限制）。升级插件后如需要，重新跑一次再肉眼过一遍 diff：

```bash
python3 tools/make_fork.py   # 输入路径见脚本顶部的 SRC
```

## 注意

- `api.lib('features/memory.js')`、`api.lib('features/memory-graph.js')`、`api.lib('tools/tools.js')` 是插件提供的加载器；改成相对 import 在 `plugins-data` 下会解析失败。
- 模块市场/插件升级**不会**覆盖这个文件（它在 `plugins-data` 下），但也不会自动跟进内置版的新功能。
