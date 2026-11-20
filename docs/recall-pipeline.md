# 召回链路（MC + 本地）

> 2026-11-21 落地时写。描述 `plugins-data/aurabot` 下「记忆」与「记忆库召回（MC）」两个模块如何分工，以及改这套东西时容易踩的坑。

## 一图流

```
用户这轮的消息
  ├─ mc-recall  api.on('prompt')   → 查 MC /api/recall，注入 MC 片段
  ├─ memory     api.on('prompt')   → 本地召回，逐行与上面已注入的内容去重后注入
  ├─ memory     api.context        → 常驻记忆块（面板「常住记忆上限」，默认 1200 字）
  └─ 模型

模型主动查记忆
  └─ memory     recall_memory 工具 → 一次查 MC + 本地，合并去重，带【MC 记忆库】【本地记忆】标注
```

宿主 `prompt` 是**链式 filter**：每个 listener 拿到上一个改完的 `content`，返回新值继续传。模块按 id 排序加载，`mc-recall` < `memory`，所以本地钩子能看到 MC 已经注入的内容——这是「不引入共享缓存也能去重」的前提。顺序变了，去重会失效（不会报错，只是重复变多）。

## 三处开关

| 开关 | 位置 | 作用 |
|---|---|---|
| `memory.enabled` | `config.json` 顶层 | 总闸。为 `false` 时：注入为空、常驻块为空、`tick()` 不整理，但工具仍注册 |
| `memory.dedupeAgainstPrompt` | 同上 | 默认 `true`；关掉后本地注入不再与 MC 比对 |
| `ext['mc-recall'].tool` | `config.json` → `ext` | 默认 `true`；线上设 `false`，把 `recall_memory` 让给 memory 模块的合并版 |

面板上「记忆 memory · 用的是你的版本」只说明**模块**启用了（`modules.memory.enabled` + `useBuiltin:false`），和上面的 `memory.enabled` 是两回事——排查「明明开着却没反应」时先看这一位。

## 判重规则

归一化：NFKC → 只保留 `\p{L}\p{N}`（JS 的 `\W` 不含中日韩，用它会把整段中文剥成空串）。

逐行比对，命中任一即丢弃本地这一条：

1. 整条被已有行包含，且归一化后 ≥ 8 字；
2. 3-gram Jaccard ≥ 0.5，且 ≥ 12 字。

标定（2026-11-21，本地 44 条 × MC 886 条）：规则 1 砍 20 条、规则 1c（逐字但实体无关、±2 天）砍 11 条、规则 2 砍 1 条，**保留 12 条**——都是「主人说过某话」的转述、他人对鱼鱼的看法、说话口气，属印象层，MC 的 duty 不产出。

## 工具归属与重名

两个模块都注册 `recall_memory` 时，后注册的那个**静默不挂**，日志只有：

```
[debug] [modules] 工具 recall_memory 重名，模块「memory」的没挂
```

所以合并版上线时把 `ext['mc-recall'].tool` 设成了 `false`，并让 memory 重载一次。想回到「只查 MC」的老行为：`mc-recall.tool=true`，同时把 memory 的 `recall_memory` 移除或改名。

## 踩坑清单

- **`\W` 陷阱**：见上，必须用 Unicode 属性类。
- **整块 Jaccard 会被稀释**：拿几百字的 MC 段落和一条 30 字本地记忆算相似度，永远不达标；必须逐行。
- **`mcSource` 合并层**：旧 fork 把 MC 片段并进 `list()`，星图因此显示 10 月底以来的 886 条；删掉合并层后星图只剩本地 44 条 + 十余条档案，报错 `mcSource.list is not a function` 也随之消失。
- **热重载**：模块文件改完宿主自动重载（日志 `模块「memory」文件改了，重新加载`），不需要重启宿主；但 `api.context`、`api.on('prompt')`、`api.every` 都必须**显式注册**，删掉对应代码就是永久失效，不是「暂时不跑」。
- **`tick()` 只在到点调模型**：`consolidateTimes`（默认 04:00/16:00）到点才 `consolidate()`，否则只在 `extractIdleMinutes > 0` 时跑 `extractIdle()`；平时那一次检查几乎零成本。

## 红线

**不把 MC 的数据迁移进本地库。** MC 的记忆带逐字引文、主体、消息指纹与双审 Claim（`claim_review_a/b`），搬进本地会丢掉这些锚点，等于把可审计的记忆降级成不可追溯的文本。两边的分工是「事实与态度走 MC，本地补印象层」。
