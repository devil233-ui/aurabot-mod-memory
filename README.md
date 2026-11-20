# aurobot-mod-memory

Aurabot（DSH 的 QQ 插件 `dsh-aurabot-qq`）的「记忆」模块**本地版**：**写入走本地记忆库，召回由 MC 与本地库合并给出**。

## 它和内置版的差别

以内置 `src/modules/memory/index.js`（552 行版本）为底，做五件事：

1. **写入留在本地**：`/memory/add|update|delete|restore|import`、`/memory/graph/*`、`/profiles/save` 等 51 条路由全部保留，写的是 `plugins-data/aurabot` 下的本地记忆库（`features/memory.js` 的 `createMemoryStore`）。
2. **注册 `api.context`（常驻记忆）**：每轮把 `memory.contextFor()`（面板「常住记忆上限」，默认 1200 字）挂进运行时上下文快照；它与 prompt 通道并存，判重时把常驻块也算作「已注入」。
3. **注册 `api.on('prompt')`，但与 `mc-recall` 并列注入时先去重**：宿主的 `prompt` 是链式 filter，`mc-recall`（模块 id 排序在前）先把 MC 片段塞进 `content`，本模块再读这份 `content` 逐行比对——整条被已有行包含、或 3-gram Jaccard ≥ 0.5 的本地条目直接跳过，跳过的条数写进日志。开关：`memory.dedupeAgainstPrompt`（默认 `true`）。
4. **保留 `recall_memory`，改成合并召回**：一次同时查 MC 的 `/api/recall` 与本地库，按「归一化后整条包含 / 3-gram Jaccard ≥ 0.5」去重，返回带【MC 记忆库】【本地记忆】标注的文本，并给出 `dropped`（被合并掉的本地条数）；两边都空时明说「没查到相关记忆」。
5. **注册 `api.every(60_000, memory.tick)`**：每分钟检查一次，只有到面板设的整理时间才真正调模型。

工具四个：`lookup_person`、`chat_impression`、`remember`、`recall_memory`。其中 `recall_memory` 由本模块独占（合并 MC 与本地库）；`mc-recall` 的同名工具已用 `ext["mc-recall"].tool=false` 关掉，它仍负责每轮把 MC 片段注入 `prompt`。

## 为什么召回还留着 MC

理由是**入库质量**，不是习惯：

- MC 的每条记忆都从**逐条消息**长出来：Scribe 只提取「最小完整语义观察 + 主体 + 逐字引文 + 消息 ID/指纹」，主体限定 `user/assistant/third_party/unknown`，assistant 的自述不会被当成 user 的事实；随后 `claim_review_a` 与 `claim_review_b` 两个独立审查在同一 revision/输入指纹上一致才发布成 Claim，分歧进 `needs_review`；再按 duty 十类与时间状态分类；Profile 的 Facts/Status/Judgment 各自差量更新、可单独回滚。指纹、revision、租约任一不符就 fail-closed，不允许"差不多就写进去"。
- 本地库是对话级抽取、直接写入：没有引文、没有双审、没有回滚，也拿不到"这句话是谁说的、什么时候说的"的原始锚点。它擅长的是「谁说过什么」「口吻、称呼、关系亲疏」这类印象层内容。
- 因此分工：**事实与态度的召回走 MC，本地库只补 MC 不产出的印象层**（这也是合并去重里保留那批条目的原因——多为主人转述、他人看法、说话口气）。
- 不搬 MC 的数据（红线）：搬进本地会丢掉引文、主体和 revision，等于把可审计的记忆降级成一段不可追溯的文本。

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
