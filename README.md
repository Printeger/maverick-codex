# Maverick Codex · V1

**一个有主见的主 Agent，五个个性不同的伙伴。人格通用，知识随项目初始化。**

把这个仓库交给目标项目里的 Codex，它按 [INSTALL.md](INSTALL.md) 安装项目级 Skill，
读取项目资料，建立知识背景，并检查能否真的调用子 Agent。

V1 采用 Codex 原生自定义子 Agent、`AGENTS.md` 和一个 `maverick` Skill。
没有独立后台服务、数据库、人格评测平台或自动进化任务。

## 直接使用

在你的项目 Codex 对话里发送下面一段，将仓库地址替换为你实际使用的地址：

```text
请将 https://github.com/Printeger/maverick-codex 初始化到当前项目。
先阅读仓库 INSTALL.md，然后执行安装并根据当前项目的真实资料填写专业知识。
保留现有 AGENTS.md、模型、MCP 和权限配置，不修改业务代码。
让 Maverick 成为主协调者和主要声音，其他人格按需调用。
Inventor 保留跨学科知识地图，不要只给它本项目领域的知识。
最后分别报告静态检查和真实子 Agent 调用结果，不能把文件存在当成加载成功。
```

如果源仓库是私有的，目标 Codex 所在环境需要你已有的 GitHub 仓库访问权限。
工具不会搬运 ChatGPT 的登录状态或生成访问凭据。

安装完成后直接正常提出任务，也可显式使用 `$maverick`：

```text
$maverick 这个方案太复杂。找一个更直接的实现，先把核心行为做出来。
```

**要求：**Python 3.11+，以及支持自定义 Subagents 的 Codex 客户端。
脚本只使用 Python 标准库。旧客户端可使用主 Agent/知识部分，但不能视为完整多 Agent 初始化。

## 六种人格

| 人格 | 人物启发 | 持续关心的问题 |
|---|---|---|
| **Maverick**，主 Agent | Jobs 式产品判断 | 这个东西为什么值得做？什么应该删掉？我选哪条路？ |
| **Rebel** | Musk 式第一性原理 | 哪些限制是真的，哪些只是沿袭？ |
| **Inventor** | Dyson 式发明习惯 | 别的领域有没有同构机制？能不能马上拼个原型？ |
| **Hacker** | Wozniak / Carmack 式工程直觉 | 能不能直接改这两个函数？ |
| **Scientist** | Feynman 式怀疑与好奇 | 哪一条证据会改变我们现在的决定？ |
| **Producer** | Ohno 式消除浪费 | 眼前真正挡住交付的是什么？ |

人物名称仅用于解释设计启发，不模仿本人，也不承诺具备其能力。
每份人格包含执念、第一反应、取舍、冲突习惯、盲点和自然语言正反例。
人格文件没有 SLAM、Web、写作课题等项目限定，也不绑定某个模型。

Maverick 是主对话的身份，不额外派生第六个常驻子线程。其他五个原生角色使用
`mav_rebel`、`mav_inventor`、`mav_hacker`、`mav_scientist`、`mav_producer`，避免常见名称冲突。
小任务由 Maverick 自己处理；默认最多两名子 Agent，没有全员流水线。

## 人格、知识、记忆怎么分

| 内容 | 放哪里 | 例子 |
|---|---|---|
| 通用人格 | `personas/*.md`，安装时复制 | Hacker 喜欢直接实现，Rebel 先质疑假设 |
| 当前项目的人格微调 | `.maverick/preferences.json` | 小改动不建立新接口，回复先说结论 |
| 项目事实与专业背景 | `.maverick/PROJECT.md`、`knowledge/domain.md` | 实际技术栈、单位、入口、资料、约束 |
| 跨学科知识 | Skill 的 `references/knowledge/` | 反馈与信息、网络与流量、生物适应、认知与实验 |
| 当前进度和交接 | `.maverick/STATE.md` | 做到哪里、关键决定、下一步、实际验证 |

初始化包含两部分：Python 安装器生成文件；**当前 Codex 阅读真实项目并填写知识**。
安装器不会凭目录名称猜专业事实，也不会自动下载一个巨大的知识库。
代码、论文、产品项目都可适配；专业细节只在相关任务中读取。

Inventor 的跨学科地图始终保留，初始四张卡片是可扩展的入口，覆盖十余种机制，
不声称囊括全部学科。每张都有机制、迁移假设、类比失效点、便宜的反证办法和原始资料链接。
需要新领域时再补充可靠资料，不把所有知识塞进每个 Agent 的上下文。

## 手动 update：你决定何时，它负责提炼

**没有自动周期。**任务结束后，如果你觉得行为需要调整，直接说：

```text
$maverick update Hacker：刚才只是改一个参数读取，你却加了适配器。
以后这类任务优先修改现有函数，不为假想的未来需求增加层次。
```

或者：

```text
$maverick update：总结刚才真正值得保留的行为反馈，最多调整两条。
只修改当前项目，不做评测、不重跑任务。
```

Maverick 区分人格问题与知识问题，对人格只提炼少量规则，重用同一规则键会替换旧内容。
明确的 update 就是修改授权，不再发起一轮常规确认。默认最多保留每个人格八条项目偏好，
阻止提示词不断堆积；不是实际“性格数值”的上限。规则可删除，最近 20 次变动保留简短记录。

只做配置检查，不进行相同任务 A/B、人格评分或定时 benchmark。
主 Agent 显式读取新偏好；下次调用被改动人格时创建新子线程，避免旧指令残留。
源仓库通用人格不自动修改，其他项目不受影响。需要跨项目推广时，再明确要求提炼成通用规则。

## 会话与成本

Maverick 在逻辑上负责整个项目，具体 Codex 对话可以更换。进入项目新会话时，
读取人格、PROJECT 和 STATE 后继续。没有自动替换聊天 UI 或 24 小时后台运行功能。

同一模块的连续实现/调试优先复用仍有效的子 Agent；换项目、任务无关或上下文太长就新建。
复用保留有用上下文，也会保留历史成本，不保证永远更便宜。V1 不建线程池或定时唤醒任务。

任务交接只传目标、必要背景、证据路径、文件范围、完成条件。子 Agent 回结论和产物位置，
不回几千行日志。STATE 只在重要决定/阶段完成/交接时更新，不在每个小动作后写报告。

默认所有角色继承主模型与推理设置。若你的客户端提供合适的便宜模型，可仅给 Hacker 设置：

```bash
python3 .agents/skills/maverick/scripts/maverick.py sync --project . --worker-model YOUR_MODEL_ID
```

用 `--worker-model inherit` 恢复继承。工具不猜型号、不保证某账号可用，需实际调用确认。

## 初始化会改哪些文件

| 文件 | 行为 |
|---|---|
| `AGENTS.md` | 增加标记明确的 Maverick 指导块，保留原文 |
| `.codex/config.toml` | 合并 `[agents]`，启用子 Agent；已有并发/模型/MCP/权限保留 |
| `.codex/agents/mav_*.toml` | 生成五个原生子角色 |
| `.agents/skills/maverick/` | 自包含 Skill、六份人格、知识地图、维护脚本 |
| `.maverick/` | 项目背景、知识、状态、偏好、安装信息 |

重复运行 init 不重置现有内容。与未归属本工具的同名文件冲突时停止，避免覆盖。
安装不修改全局配置，不创建目标项目分支/提交，不运行业务代码。
生成的子角色 TOML 不是编辑入口：改人格偏好后由 `sync` 重建。

## 命令

```bash
# 从源仓库安装到项目
python3 scripts/maverick.py init --project /path/to/project

# 安装后：检查文件、配置与知识就绪标记，不调用模型
python3 .agents/skills/maverick/scripts/maverick.py doctor --project .

# 明确调整一条项目人格偏好；同 key 会替换
python3 .agents/skills/maverick/scripts/maverick.py update --project . \
  --persona hacker --key simple_changes --rule '现有函数能完成时，直接修改现有函数。'

# 删除这条偏好
python3 .agents/skills/maverick/scripts/maverick.py update --project . \
  --persona hacker --key simple_changes --remove
```

无需记住这些命令，交给项目中的 Codex 执行即可。

## 验证状态与边界

本仓库有四项轻量安装器测试，使用临时目录和 Python 标准库，无模型费用：

```bash
python3 tests/smoke.py
```

覆盖保留原文件、重复初始化、知识待填/就绪、手动更新替换/删除、冲突前停止、可选工作模型。
它们验证安装器行为，不是人格 benchmark，也不代表六个人格已经量化验证有效。

原生初始化需由目标 Codex 实际调用 Hacker 和 Inventor 两个短只读任务。
配置语法通过不等于角色已加载；线程名称不等于自定义角色。必须分别报告静态与原生结果。
客户端支持、项目 trust、模型权限、会话重新发现能力以实际环境为准。

详见 [兼容性说明](docs/codex-compatibility.md) 与 [给 Codex 的安装流程](INSTALL.md)。

## 仓库入口

- `personas/`：六人格的通用源文件。
- `knowledge/`：跨学科机制地图和来源。
- `skills/maverick/`：Skill 模板与界面元数据。
- `scripts/maverick.py`：安装、检查、同步、手动 update。
- `tests/smoke.py`：安装器必要验证。

V1 的目标是让你把它放进一个真实项目后直接用，靠实际反馈调整几个具体行为。
