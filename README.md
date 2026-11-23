# Maverick Codex · V1.2.0

**调用 Maverick，就让六个人格真实参与：先独立判断，由 Maverick 综合取舍，再动手完成。**

把本仓库交给项目里的 Codex，它按 [INSTALL.md](INSTALL.md) 安装项目级 Skill，读取真实项目，
建立专业知识背景，并检查子 Agent 是否真正运行。人格通用，知识随项目初始化。

V1.2 将六人格参与从可选调度改为每个用户任务的默认约定，不区分 Research Mode / Execution Mode。
Maverick 负责主对话和最终决定，Rebel、Inventor、Hacker、Scientist、Producer 都须实际返回初始判断。
首轮之后，按当前问题继续执行或追问相关伙伴。沿用现有贡献账本，没有后台调度服务或人格评测系统。

## 直接使用

在目标项目的 Codex 对话里发送：

```text
请将 https://github.com/Printeger/maverick-codex 初始化到当前项目。
先阅读 INSTALL.md，安装 V1.2.0，并根据真实项目资料填写专业知识。
若已经安装旧版，从新版源目录执行 upgrade，保留项目知识、状态、偏好和贡献账本。
保留现有 AGENTS.md、MCP 和权限设置，按固定配置更新模型，不修改业务代码。
调用 Maverick 即使用六人格：五个真实子 Agent 先独立判断，Maverick 综合后推进。
Inventor 保留跨学科知识地图。完成五个短只读子任务，分别报告静态与实际调用结果。
不能把文件存在、任务名称或主线程模拟视角当成角色真正加载。
```

之后正常提出任务即可，也可显式使用 `$maverick`：

```text
$maverick 根据已有结果继续改进这个项目。目标和边界见项目说明，先形成判断，再实现值得尝试的方案。
```

需要 Python 3.11+；安装脚本只用标准库。完整协作需要当前 Codex 能创建真实子 Agent。
优先使用原生自定义角色；只有提示词委派能力时，明确记录实际使用方式。

### 已有项目的升级 prompt

将下面这段交给**已经安装 Maverick 的目标项目**中的 Codex：

```text
请将当前项目的 Maverick 升级到 https://github.com/Printeger/maverick-codex 的 V1.2.0。
先取得新版源仓库并阅读 INSTALL.md，从新版源目录运行 upgrade；不要用 init 重置已有项目。
保留项目知识、STATE、人格偏好、调整记录和 contributions.jsonl，保留无关配置与用户文件。
重读新 Skill、主协调规则和相关人格。六人格全部参与初始判断，不区分模式；后续按需复用。
旧 STATE 中“可以省略角色”等框架规则已过时，但保留其中的事实、任务进展和用户明确要求。
如果保留的人格或偏好与新规则冲突，列出具体冲突，不擅自删除用户指令。
模型保持 gpt-6.2-sol：Maverick/Rebel/Inventor/Scientist high，Hacker/Producer medium。
运行 doctor，并用五个短只读子任务检查实际参与，记录真实返回、线程 ID、证据和调用方式。
运行 report --require-full-team 检查本次记录，明确区分静态检查、记录完整性与实际运行结果。
原生角色未加载时如实报告；可用真实提示词委派时明确标注，不能冒充原生加载成功。
不重跑业务实验，不修改业务实现，不自动执行人格 update。最后汇报升级结果和剩余问题。
```

## 六种人格，各有自己的取舍

| 人格 | 人物启发 | 持续关心的问题 |
|---|---|---|
| **Maverick**，主 Agent | Jobs 式产品判断 | 值不值得做？我们是不是绕远了？我选哪条路？ |
| **Rebel** | Musk 式第一性原理 | 哪些限制是真的，哪些只是沿袭？ |
| **Inventor** | Dyson 式发明习惯 | 别的领域有没有同构机制？能不能马上拼个原型？ |
| **Hacker** | Wozniak / Carmack 式工程直觉 | 能不能直接改这两个函数？ |
| **Scientist** | Feynman 式怀疑与好奇 | 哪一条证据会改变现在的决定？ |
| **Producer** | Ohno 式消除浪费 | 眼前真正挡住交付的是什么？ |

人物名称只解释设计启发，不模仿本人，也不承诺具备其能力。人格包含执念、取舍、盲点和语言习惯，
不限定专业领域或工种。Hacker 可以提出新机制，Inventor 也可以发现实现错误。

Maverick 是主对话身份，不另建一个主控子线程。五个原生角色名为
`mav_rebel`、`mav_inventor`、`mav_hacker`、`mav_scientist`、`mav_producer`。

## 一个任务怎样推进

1. **统一事实，独立判断。** Maverick 明确目标、真实边界和证据路径，将同一份简短背景交给五个伙伴。
   首轮不把自己偏好的方案当成定论，也不先给伙伴灌入其他角色的结论。
   每人返回一个具体判断、依据及建议；可以支持直接方案，无需硬造反对意见或新点子。
2. **综合后决定。** 五个伙伴真实返回后，Maverick 说明选择什么、采纳了哪些意见、哪些未采用及理由。
   只追问会改变决定的分歧，不等全员一致。完整记录首轮后，使用 `report --require-full-team` 检查是否漏人。
3. **集中执行，遇到问题再换思路。** 分配明确工作和文件范围。持续有进展就继续；失败、矛盾或复杂化时，
   追问合适的已有伙伴，必要时创建新线程。最终方案可以很简单，改动大小不代表研究价值。
4. **如实汇报。** 任务结束检查参与记录，说明结果、实际验证、各人格的作用，以及是否发生关键思维转变。
   参与但尚无确认影响的角色可以没有分值。

“一个任务”指用户提出的完整目标或明确新里程碑。同一任务的继续、恢复、工具调用、编译修复和状态询问，
不重新召集全员；沿用任务 ID 和已有初始记录。目标或边界发生实质变化时，再判断是否需要新的完整首轮。

默认最多同时运行两个子 Agent，五人可以分批完成。全员参与不等于全员始终在线。
每个角色只读相关知识，交接只传目标、必要事实、证据路径和工作范围；返回尽量简短，不复制全部历史。
同一文件只交给一个写入者。线程仍相关且可用时复用；无法恢复时用项目状态续接，不假定跨会话线程常驻。

### 首轮之后，谁来决定追问谁？

仍由 Maverick 根据实际阻力决定：

| 当前阻力 | 值得追问的方向 |
|---|---|
| 同一修复连续无效；简单目标需要大重构 | Rebel 重新审视假设，Scientist 区分解释 |
| 分析很久，没有新的可执行结论 | Hacker 做一个最小实现或实验 |
| 局部方案越来越复杂 | Inventor 寻找替代机制，Rebel 删除假约束 |
| 结果与预期冲突 | Scientist 找能改变决定的证据 |
| 核心成果完成，交付仍卡住 | Producer 清除具体阻塞 |

这些是提醒，不是固定轮值或计时器。Maverick 在执行中也可借用其他人格的视角，
但这种行为不能替代五个伙伴的真实初始参与。复用 Hacker 线程不等于它变成了 Rebel。

## 参与和贡献分别报告

沿用 `.maverick/contributions.jsonl`，由 Maverick 统一写入，子 Agent 不争写账本。
V1.2 增加可选 `phase: "initial"`，标记真实返回的初始判断；增加无分值状态 `reviewed`，
表示判断已完成，但没有确认其对结果的影响。旧账本无须重写，也不补造历史参与。

每条初始记录包含实际结论、结果和证据引用。子人格须为真实子 Agent，`actor` 使用工具返回的线程 ID。
Maverick 用 `direct` 记录综合决定。主线程的 `perspective` 不计入独立初始参与；同一线程不能冒充多个初始人格。

| 报告内容 | 规则 |
|---|---|
| 初始参与 | 显示已记录完成的角色、缺少的角色及记录冲突 |
| 参与方式 | 区分主线程、原生子角色、提示词委派和实际复用 |
| 贡献类型 | 方向、实施、纠错，同等重要 |
| 影响等级 | 仅已确认影响有等级：3 关键、2 实质、1 辅助；其余为 `—` |
| 未确认判断 | `reviewed` / `proposed` / `unknown`；未采用为 `not_adopted`，都不自动得分 |
| 关键转变 | 原来怎样理解，后来怎样理解，依据是什么 |

不按调用次数、token、耗时或代码量排名，不计算总和 100% 的份额，也不默认给 Maverick 领导分。
没有记录表示未记录，不能据此断言角色从未参与。未采用的意见只有实际帮助排除路线或纠错时，才能确认贡献。
判断被实际用于选路、实现或验证，也可以确认贡献，不要求证明“别人想不到”或独立增益。
只被提及或收到则仍可保留 `reviewed`；不应把所有贡献只归给最终写代码的人。

### 初始记录示例

下面是**虚构的格式示例**。真实使用必须填写实际线程 ID 和返回证据：

```json
{
  "id": "rebel-initial",
  "task": "demo-parser-fix",
  "phase": "initial",
  "persona": "rebel",
  "mode": "delegated_subagent",
  "actor": "example-thread-id",
  "trigger": "本任务的独立初始判断",
  "kind": "direction",
  "contribution": "检查适配层是否必要，建议直接复用现有入口",
  "status": "reviewed",
  "outcome": "判断已返回，等待 Maverick 综合选择",
  "evidence": ["example: 该线程的实际返回及 src/parser.py 入口"],
  "impact": null
}
```

同一 `task` 与 `id` 可以追加后续结果，报告使用最新修订。确认影响后才填写 `confirmed` 和等级；
有证据的关键转变可加 `shift: {"before": "原来理解", "after": "新的理解"}`。
只在真实复用时填 `reused: true`。调用已发出但尚未返回，不能记成完成初始判断。

`report --require-full-team` 在首轮综合后和任务结束时检查六人格初始记录。
它打印报告，记录齐全返回 0，不齐全返回 2，记录格式错误返回 1。
普通 `report` 仍可回顾旧任务，不把历史缺失强制改成新格式。

**完整性检查只能检查记录，不能认证真实调用、独立上下文或证据真假。**
Maverick 必须核对工具返回与成果。CLI 不拦截训练或其他工具，执行先后由 Skill 规则要求，
也不会另起评分模型。贡献报告与人格 `update` 分开。

## 固定模型配置

六人格统一使用 `gpt-6.2-sol`，不自动切换模型。

| 人格 | 模型 | 推理强度 |
|---|---|---|
| Maverick 主 Agent | `gpt-6.2-sol` | `high` |
| Rebel | `gpt-6.2-sol` | `high` |
| Inventor | `gpt-6.2-sol` | `high` |
| Hacker | `gpt-6.2-sol` | `medium` |
| Scientist | `gpt-6.2-sol` | `high` |
| Producer | `gpt-6.2-sol` | `medium` |

安装和升级将主配置写入项目 `.codex/config.toml`，子配置写入五个 `.codex/agents/mav_*.toml`。
覆盖模型与推理档位，保留无关 MCP、权限和并发设置。CLI 参数、项目信任、模型可用性和已启动的会话
仍可能影响实际加载；文件检查通过不等于当前对话已经采用该模型。

## 人格、知识和记忆

| 内容 | 位置 |
|---|---|
| 通用人格 | 源仓库 `personas/*.md`，安装到 Skill 的 `references/personas/` |
| 当前项目的人格微调 | `.maverick/preferences.json` |
| 项目事实与专业背景 | `.maverick/PROJECT.md`、`.maverick/knowledge/` |
| 跨学科机制地图 | Skill 的 `references/knowledge/` |
| 当前任务 ID、进度、决定和下一步 | `.maverick/STATE.md` |
| 初始判断及有依据的贡献 | `.maverick/contributions.jsonl` |

项目背景由当前 Codex 阅读真实资料后填写，不凭目录名猜测。知识按需加载，不复制六份。
Inventor 保留跨学科地图；项目专业背景是在其上增加的一层。类比是可验证的假设，不是可行性证明。

Maverick 在逻辑上负责整个项目，对话可以更换。续接时读 PROJECT、STATE 和相关证据，
按当前任务生成报告即可，不必重读全部贡献历史。STATE 尽量一屏，记录重要进展和初始协作是否完成。

## 手动 update

```text
$maverick update Hacker：刚才只是改一个参数读取，你却加了适配器。
以后优先修改现有函数，不为假想的未来需求增加层次。
```

人格调整由用户明确发起，无自动周期。默认只改当前项目，提炼少量规则；同 key 替换旧规则，
支持删除，每个人格最多八条项目偏好，日志保留最近 20 次。不重跑相同任务作 A/B 或人格 benchmark。
重读新偏好，被修改人格使用新子线程；通用人格及其他项目不会自动改变。

## 命令入口

```bash
# 在源目录安装或升级目标项目
python3 scripts/maverick.py init --project /path/to/project
python3 scripts/maverick.py upgrade --project /path/to/project

# 以下在目标项目执行
python3 .agents/skills/maverick/scripts/maverick.py doctor --project .
python3 .agents/skills/maverick/scripts/maverick.py record --project . --event event.json
python3 .agents/skills/maverick/scripts/maverick.py report --project . --task TASK_ID --require-full-team

# 普通报告可回顾旧任务；record --event - 可从标准输入接收 JSON
python3 .agents/skills/maverick/scripts/maverick.py report --project . --task OLD_TASK_ID

# 明确调整人格；同 key 替换，--remove 删除
python3 .agents/skills/maverick/scripts/maverick.py update --project . \
  --persona hacker --key simple_changes --rule '现有函数能完成时，直接修改现有函数。'
python3 .agents/skills/maverick/scripts/maverick.py sync --project .
```

`upgrade` 更新框架，`update` 调整人格，`sync` 重建角色配置。重复 `init` 不重置项目，也不代替升级。
升级保留背景、知识、STATE、偏好与账本；保留本地修改的人格和知识卡片，并列出保留项。
手工修改的 Skill 或维护脚本发生冲突时，先报告具体差异。普通任务不会自动创建提交、分支或发布。

## 验证与边界

```bash
python3 tests/smoke.py
```

这些功能检查使用临时目录与标准库，覆盖安装、升级、数据保留、记录和归因，不调用模型。
目标项目初始化和升级还需五个短只读子任务，记录实际返回、线程 ID 与证据。
原生角色实测、提示词委派实测和静态检查应分别报告；完全没有子 Agent 工具时，六人格协作未完成。
详细规则见 [INSTALL.md](INSTALL.md) 和 [兼容性说明](docs/codex-compatibility.md)。
