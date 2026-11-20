# aurobot-mod-memory

Aurabot（DSH 的 QQ 插件 `dsh-aurabot-qq`）的「记忆」模块 fork：**写入走本地记忆库，召回交给 `mc-recall`（MemoryConstellations）**。

## 它和内置版的差别

以内置 `src/modules/memory/index.js`（552 行版本）为底，做四件事：

1. **写入留在本地**：`/memory/add|update|delete|restore|import`、`/memory/graph/*`、`/profiles/save` 等 51 条路由全部保留，写的是 `plugins-data/aurabot` 下的本地记忆库（`features/memory.js` 的 `createMemoryStore`）。
2. **不注册 `api.context` / `api.on('prompt')`**：每轮自动注入只由 `mc-recall` 负责，避免同一轮塞两段记忆。
3. **删掉 `recall_memory` 工具**：召回统一走 `mc-recall`（它查 MC 的 `/api/recall`）。
4. **不注册 `api.every(60_000, memory.tick)`**：本地库的每分钟自动整理不跑（省模型调用）；面板上的整理入口仍在。

工具保留三个：`lookup_person`、`chat_impression`、`remember`。

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

`tools/make_fork.py` 以内置版为底做字符串手术（去相对 import、换 `api.lib(...)`、删 `api.context`/`api.on('prompt')`/`api.every`/`recall_memory`/工具门限制）。升级插件后如需要，重新跑一次再肉眼过一遍 diff：

```bash
python3 tools/make_fork.py   # 输入路径见脚本顶部的 SRC
```

## 注意

- `api.lib('features/memory.js')`、`api.lib('features/memory-graph.js')`、`api.lib('tools/tools.js')` 是插件提供的加载器；改成相对 import 在 `plugins-data` 下会解析失败。
- 模块市场/插件升级**不会**覆盖这个文件（它在 `plugins-data` 下），但也不会自动跟进内置版的新功能。
