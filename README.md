# Maverick Codex · V1.1

**一个有主见的主 Agent，五种个性鲜明的伙伴。根据问题的进展换思考方式，用实际成果说明贡献。**

把本仓库交给项目里的 Codex，它按 [INSTALL.md](INSTALL.md) 安装项目级 Skill，读取真实项目，
建立专业知识背景，并检查能否调用子 Agent。人格通用，知识随项目初始化。

V1.1 增加两件事：**问题驱动的思维切换**和**任务结束后的贡献汇报**。
继续使用 Codex 原生子 Agent、`AGENTS.md` 和一个 `maverick` Skill；没有后台调度、
数据库、新的评测 Agent 或人格 benchmark。人格调整仍由你明确发起 `update`。

## 直接使用

在目标项目的 Codex 对话里发送：

```text
请将 https://github.com/Printeger/maverick-codex 初始化到当前项目。
先阅读 INSTALL.md，安装 V1.1，并根据当前项目的真实资料填写专业知识。
若已经安装旧版，执行 upgrade，保留项目知识、状态与人格偏好。
保留现有 AGENTS.md、模型、MCP 和权限设置，不修改业务代码。
让 Maverick 成为主协调者和主要声音，根据问题进展切换视角，按需调用伙伴。
Inventor 保留跨学科知识地图。开发任务结束时汇报有证据的贡献和关键思维转变。
最后分别报告静态检查与真实子 Agent 调用结果，不能把文件存在当成加载成功。
```

之后正常提出任务即可，也可显式使用 `$maverick`：

```text
$maverick 这个方案太复杂。找一个更直接的实现，先把核心行为做出来。
```

要求 Python 3.11+，以及支持自定义 Subagents 的 Codex 客户端。脚本只用 Python 标准库。
旧客户端可以使用主 Agent 和项目知识，但不能视为完整多 Agent 初始化。

## 六种人格，各有自己的取舍

| 人格 | 人物启发 | 持续关心的问题 |
|---|---|---|
| **Maverick**，主 Agent | Jobs 式产品判断 | 值不值得做？我们是不是绕远了？我选哪条路？ |
| **Rebel** | Musk 式第一性原理 | 哪些限制是真的，哪些只是沿袭？ |
| **Inventor** | Dyson 式发明习惯 | 别的领域有没有同构机制？能不能马上拼个原型？ |
| **Hacker** | Wozniak / Carmack 式工程直觉 | 能不能直接改这两个函数？ |
| **Scientist** | Feynman 式怀疑与好奇 | 哪一条证据会改变现在的决定？ |
| **Producer** | Ohno 式消除浪费 | 眼前真正挡住交付的是什么？ |

人物名称只解释设计启发，不模仿本人，也不承诺具备其能力。每份人格有执念、第一反应、
取舍、冲突习惯、盲点和语言正反例；不限定项目领域，也不绑定某个模型。
V1.1 保留五个伙伴的人格核心，强化 Maverick 对停滞、矛盾和复杂度的判断。

Maverick 是主对话身份，不额外创建第六个常驻子线程。五个原生角色名为
`mav_rebel`、`mav_inventor`、`mav_hacker`、`mav_scientist`、`mav_producer`。
小任务可由主 Agent 完成，通常最多两名子 Agent，不要求全员参加。

## 谁决定什么时候换人？

**Maverick 决定，依据是当前问题和进展。**任务叫“修 Bug”，不意味着只能用 Hacker。
先做最直接的行动，在有意义的结果、失败或阶段转折后重新判断：

| 当前阻力 | 可考虑的视角 |
|---|---|
| 同一修复连续无效；简单需求却要求大重构 | Rebel 质疑问题和约束，Scientist 区分解释 |
| 分析很久，却没有新的可执行结论 | Hacker 做最小实现或实验 |
| 实现越来越绕，原有路线接近极限 | Inventor 寻找替代机制，Rebel 删除假约束 |
| 实验与预期冲突，缺一个会改变决策的事实 | Scientist 检查关键证据 |
| 核心工作已完成，交付仍卡住 | Producer 找到真正的阻塞 |
| 信息已经足够，路线仍未确定 | Maverick 作取舍 |

这些是软触发，不是固定流程。两次失败是重新判断的提醒，不是强制新建 Rebel 的计数器。
时间只辅助识别“投入增加、信息没有增加”；持续推进就继续。没有后台计时或轮询服务。

### 换视角不必创建新 Agent

1. **Maverick 自己借用视角。**一句质疑、一个类比能推进，就直接做。
2. **复用相关子 Agent。**它仍了解当前问题、原有人格仍适合，就继续追问。
3. **创建独立人格 Agent。**需要独立判断、深入探索或有意义的并行时才创建。

不必逐层走一遍，也不以露脸次数衡量人格。Rebel 式思考可以常出现，Rebel 子线程不必常创建。
复用不改变原有角色：不能把 Hacker 换个任务名就称为 Rebel。已有历史开始拖累时开新线程，
不承诺跨主会话复用，也不保证复用永远更便宜。

交接只传目标、必要背景、证据路径、文件范围、完成条件。子 Agent 回结论、产物和实际验证，
通常不超过 180 词；同一文件只给一个写入者，不全文传回内部分析或日志。

## 开发完成后，看到实际贡献

每个开发任务或明确里程碑使用一个稳定任务 ID。Maverick 只在有实质成果或重要决定时，
将简短事实记入 `.maverick/contributions.jsonl`，结束时汇报。小任务几行即可；复杂任务用六人格表格。

| 评价项 | 规则 |
|---|---|
| 贡献类型 | 方向、实施、纠错，同等重要 |
| 定性等级 | 3 关键、2 实质、1 辅助；无确认影响为 `—` |
| 依据 | 具体结果及现有文件、实际命令结果或决策引用 |
| 未确认建议 | 保留 `proposed` / `unknown`；未采用为 `not_adopted`，均不给成功等级 |
| 实际参与 | 分清主 Agent 借用视角、真正的原生子 Agent、普通提示词委派与线程复用 |
| 结束反思 | 原来如何理解问题，后来如何理解，什么证据促成了转变 |

不按 token、调用次数、耗时或代码量排名，不拆分总和 100% 的份额，不自动给主 Agent 加领导分。
未采用的方案只有确实帮助排除路线或纠错时，才有确认贡献。没有记录不能证明从未参与，
报告会写“未记录参与”。一项成果可有多人的不同贡献，等级不相加，也不是人格能力分数。

格式检查只判断记录是否符合约定，无法验证证据真假。Maverick 仍须核对实际结果。
“借用 Rebel 视角”明确归为 Maverick 的行为，不伪装成 Rebel 子 Agent 的独立观点。

### 最小记录示例

下面是**虚构的格式示例**，不是本仓库的真实开发成绩：

```json
{
  "id": "remove-unneeded-layer",
  "task": "demo-parser-fix",
  "persona": "rebel",
  "mode": "perspective",
  "actor": "maverick",
  "trigger": "简单修复开始要求额外的适配层",
  "kind": "direction",
  "contribution": "质疑适配层的必要性，改为复用现有入口",
  "status": "confirmed",
  "outcome": "采用直接修改现有入口的方案",
  "evidence": ["decision: 本任务已采纳直接修改入口的决定"],
  "impact": 2,
  "shift": {
    "before": "需要先增加一个适配层",
    "after": "现有入口已满足需求，可以直接修改"
  }
}
```

`record --event FILE` 接收一个 JSON 文件，`--event -` 接收标准输入，不要求创建临时报告文件。
同一 `task` 和 `id` 可以追加后续结果；汇报使用最新修订，避免先提案、后落实被重复计算。
真实子 Agent 用实际工具返回 ID 作 `actor`；仅真正复用时加 `reused: true`。
已确认的关键转变可填 `shift`，没有就不填。

自动汇报来自 Skill 的任务结束规则。CLI 负责记录、检查、整理，不是后台钩子，
也不会自动启动另一轮模型评测。**贡献汇报与人格 update 分开。**

## 人格、知识、记忆分别放哪里

| 内容 | 位置 |
|---|---|
| 通用人格 | 源仓库 `personas/*.md`，安装到 Skill 的 `references/personas/` |
| 当前项目的人格微调 | `.maverick/preferences.json` |
| 项目事实与专业背景 | `.maverick/PROJECT.md`、`.maverick/knowledge/` |
| 跨学科机制地图 | Skill 的 `references/knowledge/` |
| 当前进度、最近的重要思维转变、下一步 | `.maverick/STATE.md` |
| 有依据的贡献事件 | `.maverick/contributions.jsonl` |

Python 安装器生成文件；当前 Codex 阅读真实资料并填写背景。它不会凭目录名猜专业知识。
代码、论文、产品项目都可适配，具体细节按需加载，不复制六份知识库。
Inventor 始终保留跨学科地图。初始四张卡是可扩展的机制入口，包含迁移假设、失效点、
便宜的反证办法和原始资料链接；新项目领域知识是一层补充。

Maverick 在逻辑上负责整个项目，具体对话可以更换。新会话从人格、PROJECT、STATE 和代码恢复。
STATE 尽量一屏，只在重要决定、阶段完成或交接时更新，不将全部聊天和贡献历史读回上下文。

## 手动 update：你决定何时，它负责提炼

```text
$maverick update Hacker：刚才只是改一个参数读取，你却加了适配器。
以后优先修改现有函数，不为假想的未来需求增加层次。
```

或者：

```text
$maverick update：从刚才的真实反馈中提炼最多两条行为调整。
只修改当前项目，不做评测、不重跑任务。
```

没有自动周期。明确请求即授权，默认只改当前项目。Maverick 区分知识问题与人格问题，
只提炼少量规则；同 key 替换旧规则，支持删除，每个人格最多八条项目偏好，避免无限堆积。
最近 20 次调整保留简短记录。只做配置检查，不跑相同任务 A/B 或人格 benchmark。

主 Agent 显式重读新偏好，被修改人格下次用新子线程。通用人格和其他项目不自动改变。
需要跨项目推广时，再明确要求提炼通用规则。

## 安装与升级命令

```bash
# 从源仓库安装到目标项目
python3 scripts/maverick.py init --project /path/to/project

# 从新版源仓库升级已安装的框架，保留项目知识、状态和偏好
python3 scripts/maverick.py upgrade --project /path/to/project

# 安装后：检查文件、配置、贡献格式与知识就绪标记，不调用模型
python3 .agents/skills/maverick/scripts/maverick.py doctor --project .

# 记录一项实际贡献；也可用 --event - 从标准输入提交 JSON
python3 .agents/skills/maverick/scripts/maverick.py record --project . --event event.json

# 回顾指定任务，输出 Markdown；不额外创建报告文件
python3 .agents/skills/maverick/scripts/maverick.py report --project . --task TASK_ID

# 明确调整项目人格；同 key 替换，--remove 删除
python3 .agents/skills/maverick/scripts/maverick.py update --project . \
  --persona hacker --key simple_changes --rule '现有函数能完成时，直接修改现有函数。'

# 可选：只给 Hacker 指定当前客户端实际提供的模型；inherit 恢复继承
python3 .agents/skills/maverick/scripts/maverick.py sync --project . --worker-model YOUR_MODEL_ID
```

不指定模型时沿用主会话配置；工具不猜便宜模型 ID，也不保证某账号可用。
`upgrade` 更新框架，`update` 调整人格，`sync` 重建角色配置，三者用途不同。

初始化只增加受标记管理的 AGENTS 指导块、项目 Skill、五份角色和 `.maverick/` 数据，
合并所需 agents 配置，保留已有模型、MCP、权限和并发设置。重复 `init` 不重置内容。
升级保留项目背景、知识、STATE、偏好及已有贡献；用户改过的人格/知识地图文件保留并报告。
手工改过的 Skill 或维护脚本有冲突时先停止，不静默覆盖。生成的角色 TOML 由 `sync` 重建，
不作为手工编辑入口。安装和升级不修改业务代码，不自动创建目标项目分支或提交。

## 验证状态与边界

```bash
python3 tests/smoke.py
```

这些轻量测试使用临时目录和标准库，验证安装、数据保留、升级、记录修订和贡献归因，
不调用模型，也不证明人格效果已经量化验证。
原生初始化仍需目标 Codex 实际调用 Hacker、Inventor 两个短只读任务，分别报告静态与原生结果。
客户端支持、项目 trust、模型权限、会话重新发现能力以实际环境为准。
当前开发环境未宣称通过原生角色推理测试，详见 [兼容性说明](docs/codex-compatibility.md)。

## 仓库入口

- [INSTALL.md](INSTALL.md)：目标 Codex 的初始化、升级流程。
- `personas/`：六人格源文件；`knowledge/`：跨学科机制及来源。
- `skills/maverick/`：主协调者的行为规则与元数据。
- `scripts/maverick.py`：安装、升级、检查、同步、手动 update 与贡献命令入口。
- `scripts/contributions.py`：贡献记录及报告，不调用模型。
- `tests/`：必要的功能验证。
