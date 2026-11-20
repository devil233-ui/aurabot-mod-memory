#!/usr/bin/env python3
"""以内置 memory 模块为底，生成 plugins-data 下的 fork：
- 不注册 api.context / api.on('prompt') / api.every（召回交给 mc-recall）
- 去掉 recall_memory 工具与它专用的 parsePeriod
- 工具门放开（任何会话都能记）
- 其余写路由与工具原样保留；import 改成 api.lib(...)
"""
import sys

SRC = "/root/.dsh/profiles/web/node_modules/dsh-aurabot-qq/src/modules/memory/index.js"
DST = "/root/.dsh/plugins-data/aurabot/modules/memory/index.mjs"

text = open(SRC, encoding="utf-8").read()
orig_len = len(text)


def cut(s, marker, end_marker, label):
    i = s.find(marker)
    if i < 0:
        sys.exit(f"锚点缺失: {label}")
    j = s.find(end_marker, i)
    if j < 0:
        sys.exit(f"锚点结尾缺失: {label}")
    return s[:i] + s[j + len(end_marker):]


# 1) 去掉相对 import 与 re-export（node:fs 保留）
for line in [
    "import { createMemoryStore, memoryLine, looksLikeRuleMemory, parseValidityDate } from '../../features/memory.js'\n",
    "export { looksLikeRuleMemory } from '../../features/memory.js'\n",
    "import { buildEdges, layoutGraph3d, brightness, regionOf, FADING_THRESHOLD, LAYOUT_VERSION, toStarTier, toHostTier, STAR_TIER_LABEL } from '../../features/memory-graph.js'\n",
    "import { defineTool, str } from '../../tools/tools.js'\n",
]:
    if line not in text:
        sys.exit(f"import 行未命中: {line[:60]}")
    text = text.replace(line, "", 1)

# 2) 去掉只给 recall_memory 用的 parsePeriod
text = cut(text, "/** 把「2026-03-05」", "\n}\n", "parsePeriod")

# 3) setup 里改用 api.lib
anchor = "    const { hub, http } = api.core\n"
if anchor not in text:
    sys.exit("setup 锚点缺失")
inject = anchor + (
    "    // fork：内置库经 api.lib 取，避免相对路径在 plugins-data 下失效\n"
    "    const { createMemoryStore, memoryLine, looksLikeRuleMemory } = api.lib('features/memory.js')\n"
    "    const { buildEdges, layoutGraph3d, brightness, regionOf, FADING_THRESHOLD, LAYOUT_VERSION, toStarTier, toHostTier, STAR_TIER_LABEL } = api.lib('features/memory-graph.js')\n"
    "    const { defineTool, str } = api.lib('tools/tools.js')\n"
)
text = text.replace(anchor, inject, 1)

# 4) 摘掉每轮注入的两处钩子与后台整理
ctx_line = "    api.context(({ chat, sessionId }) => (chat.kind === 'system' ? '' : memory.contextFor(chat, sessionId)))\n"
if ctx_line not in text:
    sys.exit("api.context 锚点缺失")
text = text.replace(ctx_line, "", 1)
text = cut(text, "    api.on('prompt', async (content, info) => {", "\n    })\n", "api.on('prompt')")
tick_line = "    api.every(60_000, () => memory.tick(), '整理记忆')\n"
if tick_line not in text:
    sys.exit("api.every 锚点缺失")
text = text.replace(tick_line, "", 1)

# 5) 去掉 recall_memory 工具（召回由 mc-recall 负责）
before = text
text = cut(text, "        defineTool({\n          name: 'recall_memory',", "\n        }),\n", "recall_memory 工具")
if text == before:
    sys.exit("recall_memory 未改动")

# 6) 工具门放开
gate = "      if (!api.config().memory.enabled || chat.kind === 'system') return []\n"
if gate not in text:
    sys.exit("工具门锚点缺失")
text = text.replace(
    gate,
    "      // fork（2026-11-21）：写入走本地记忆库，任何会话都能记；召回仍由 mc-recall 负责\n",
    1,
)

if "recall_memory" in text and "name: 'recall_memory'" in text:
    sys.exit("recall_memory 残留，中止")

open(DST, "w", encoding="utf-8").write(text)
print(f"ok: {orig_len} -> {len(text)} bytes; {text.count(chr(10))} lines")
