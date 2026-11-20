逐级读取上一级提示词至最高层为止。

# aurabot-mod-memory

DSH QQ 插件 `dsh-aurabot-qq` 的「记忆」模块本地版。改这里之前先读 `docs/recall-pipeline.md`——链路图、三处开关、判重标定和踩坑都在那儿，本文件只列不能踩的。

- **不把 MC 数据迁进本地库**：MC 的记忆带逐字引文、主体、消息指纹与双审 Claim，搬进来会把这些锚点丢掉，等于把可审计的记忆降级成不可追溯的文本。分工是「事实与态度走 MC，本地补印象层」。
- **`recall_memory` 归本模块独占**：MC 那边的 `ext["mc-recall"].tool` 保持 `false`；两边都注册时后注册的静默不挂，只有 debug 级一行日志。
- **判重逐行做，归一化用 `\p{L}\p{N}`**：`\W` 不含中日韩，用它会把整段中文剥成空串；整块算 Jaccard 会被长段落稀释。
- **`api.context` / `api.on('prompt')` / `api.every` 必须显式注册**：删掉对应代码就是永久失效，不是「暂时不跑」。改完文件宿主会热重载模块，不必重启宿主。
- **重跑 `tools/make_fork.py` 会覆盖四处加回的能力**（常驻块、并列注入去重、`tick()`、合并版 `recall_memory`）：先开分支跑脚本，再 `git diff` 手动移植。
- **提交身份用 `69190444+devil233-ui@users.noreply.github.com`**：仓库公开，不写真实邮箱，也不把会话里的账号信息带进提交信息。
