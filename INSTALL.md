# 安装与使用 Maverick Forge

## 1. 准备客户端

支持 macOS、Linux 和 WSL。需要 Python 3.11+、可运行的 `agy` 与 `codex`，以及两个客户端各自的登录。
安装框架不搬运凭据，也不代替首次账号登录。

AGY 官方安装入口：

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

安装说明见 [AGY Getting started](https://antigravity.google/docs/getting-started?tab=cli)。
Codex 按已有安装方式使用；先用 `codex --version`、`codex login status` 确认可用。
`agy models` 应列出 `gemini-4-neon-high`；实际账号没有该模型时不会改用别的模型。

## 2. 在目标项目一条命令安装

```bash
curl -fsSL https://raw.githubusercontent.com/Printeger/maverick-codex/maverick-forge/scripts/install.sh | bash -s -- --project "$PWD"
```

已有源码 checkout 时可直接运行：

```bash
python3 scripts/forge.py install --project /absolute/path/to/your-project
```

不要把路径误指向框架仓库，除非要开发的就是框架自身。
网络不便时把这个分支下载到本地，同样运行上述 Python 命令；运行时复制进项目，不依赖该下载位置。

安装写入的内容：

| 位置 | 用途 |
|---|---|
| `.agents/skills/maverick-forge/` | 完整主控 skill、六个人格、跨学科库、Python 桥接与安装脚本 |
| `.agents/mcp_config.json` | 本项目 Forge MCP 服务，保留其他服务 |
| `AGENTS.md`、`GEMINI.md` 中 Forge 托管块 | 主控/worker 身份、旧协议迁移，保留用户正文 |
| `.maverick/forge-manifest.json` | 版本、文件归属、固定主控配置与 CLI 路径 |
| `.maverick/forge/start` | 固定 Neon high 和完整权限的启动入口 |
| `.maverick/forge/tasks/` | 实际任务、会话与每轮结果，首次运行后产生 |
| `.maverick/PROJECT.md`、`STATE.md`、`knowledge/`、`preferences.json`、`contributions.jsonl` | 项目事实、记忆、偏好与账本；已有内容保留 |
| `~/.gemini/antigravity-cli/settings.json` | 合并用户要求的完整开发权限，保留其他字段 |

安装器只使用 Python 标准库。`--agy-bin /path/to/agy` 和 `--codex-bin /path/to/codex`
可在安装时明确客户端路径。`FORGE_PYTHON=/path/to/python3` 可选择 bootstrap 使用的解释器。
`FORGE_SOURCE=/path/to/checkout` 可让 `scripts/install.sh` 使用本地来源而不下载。

## 3. 启动与项目适配

```bash
./.maverick/forge/start
```

首次给 AGY 这段提示词即可：

```text
使用 Maverick Forge 初始化当前项目。
你是 Maverick 主控，保留完整人格和已有项目资料；模型固定 Gemini 4 Neon high。
先检查 Forge 安装和 CLI，然后从真实代码、文档与已有实验整理项目知识。
Inventor 保留通用跨学科机制库，同时获得本项目的专业背景。
让五个独立 Codex 人格各做一次简短的项目判断，再由你综合。
将真实会话、知识适配和实际回传的验证结果分别报告，保存 STATE，给出六人格贡献摘要。
普通已授权开发自主进行，不再逐项请求操作批准。
```

如果已完成适配，直接给开发目标，不需要每次重新初始化。
AGY 界面也可在该项目使用 `/maverick-forge`，但通过其他入口启动时，当前会话模型与权限
由该客户端实际设置决定；推荐上述启动器固定所需参数。

## 4. 检查安装

```bash
python3 .agents/skills/maverick-forge/scripts/forge.py doctor --project .
```

`--static` 只查包、权限设置和 MCP 握手，不查账号或模型列表。
输出区分 `installed`、`project_knowledge_ready`、`runtime_ready` 与 `live_roundtrip`。
知识 READY 标签表示资料已标就绪，不代替阅读其真实内容；`live_roundtrip` 在 doctor 中始终是
`NOT_TESTED_BY_DOCTOR`。一次真实六人格任务才检查实际模型调用和后台回传。

退出码：0 表示本次检查项目通过，2 表示安装/运行/知识仍有缺项，1 表示配置或执行错误。
静态检查返回 0 只表示静态项通过。

## 5. 继续任务、更新框架、调整人格

关掉 AGY 后可以重新运行 `.maverick/forge/start`，告诉它“继续 STATE 中的任务”。
AGY 读取当前 `task_id`，查一次保存的结果，复用相同人格的 Codex session。
上下文不会跨账户、丢失的 Codex 会话或不同机器自动迁移。

**更新框架：** 再运行安装命令，或在新 checkout 运行：

```bash
python3 scripts/forge.py update --project /absolute/path/to/your-project
```

`update` 从当前这份源码安装，不自行猜远端版本。重复运行相同安装不会重复添加规则。
保留用户修改；有冲突时新文件在 `.maverick/forge/incoming/`，由 AGY 对照合并。
原版 `.codex/` 不删除；旧人格正文会迁到实际加载的新目录。

**调整人格：** 在 AGY 里说：

```text
update Hacker：强化厌繁倾向。先保住我们选择的机制，再缩小实现；不要把开放研究退回参数微调。
用本次实际多余设计补一个短反例，只更新这条习惯，保留其他个性和专业知识。
```

偏好写 `.maverick/preferences.json`，下一次该角色调用读取新偏好，不自动重跑任务或 benchmark。

## 常见实际阻塞

- **找不到客户端：** 安装 CLI 后重跑安装/doctor。实际客户端路径可用安装参数指定。
- **模型不可用或未登录：** 运行 `agy models`、`codex login status` 检查；按客户端完成登录，保持固定模型。
- **没有 Forge 工具：** 在项目目录启动 AGY，检查 `.agents/mcp_config.json`，重新加载项目 MCP/skills 或重开会话。
- **某个角色失败：** 读取其本轮 stderr/report，用 `forge_resume` 沿保存的 run 重试；不要重复创建假角色。
- **旧桥接意外退出：** 查状态。仍有旧作业存活时先确认其状态；不并发续接同一 session，也不随意杀其他进程。
- **安装冲突：** 本地改动保留，查看 installer 的 `preserved_local_edits` 和 `incoming_candidates` 后合并。

`--gemini-dir` 仅用于隔离安装检查或预配置；实际 AGY 启动使用当前用户的 `~/.gemini`，
不能把写到其他目录的设置当成已被客户端加载。
