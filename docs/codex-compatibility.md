# Codex 兼容性与初始化验收

本版说明更新于 2026-11-23。配置格式沿用仓库原有机制；历史本地核对版本为
`codex-cli 0.172.0-alpha.2`（2026-11-21）。这不表示 V1.2 已在每个客户端完成原生角色推理实测。
客户端版本、模型权限和实际角色发现结果仍需在目标项目核对。

## 使用的配置机制

- 项目指导：项目根目录 `AGENTS.md` 中的受管理块。
- 项目 Skill：`.agents/skills/maverick/SKILL.md`，含 `name`、`description` frontmatter。
- 项目子 Agent：`.codex/agents/mav_*.toml`，五份独立人格配置。
- 项目配置：`.codex/config.toml`，合并所需设置并保留无关配置。

子 Agent 配置包含 `name`、`description`、`developer_instructions`，并显式设置
`model` 与 `model_reasoning_effort`。固定 `gpt-6.2-sol`；Maverick、Rebel、Inventor、Scientist
为 `high`，Hacker、Producer 为 `medium`。主 Agent 的两项设置位于项目配置顶层。

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 2
```

这里的并发上限不含主 Agent。`max_threads` 是仓库兼容的旧别名，不要同时写两个键。
保留项目已有并发设置；没有时默认 2。五个角色可以分批完成首轮，全员参与不要求同时运行。
不新增实验性 feature flags、后台守护进程或调度服务。

## 继承与实际加载

子 Agent 继承父会话的权限、模型提供者、MCP 与 Skills。人格说明中的“只读”不是单独的权限沙箱。
不在角色文件中尝试替换父会话的 `sandbox_mode`、`approval_policy`、`model_provider` 或 `mcp_servers`。

CLI/会话配置可能覆盖项目模型；已运行的主会话和子线程也不保证热加载新的配置。
升级后显式重读规则，使用新子线程；必要时在受信任的目标项目新会话检查实际发现与运行模型。
项目不受信任时项目配置可能不生效。通过客户端正常流程处理，不改全局信任、沙箱或审批来强行通过。

主协调者采用 Maverick，子 Agent 保留被分派的人格并遵守共同项目约束。
改任务名称不能改变线程已加载的人格。线程 ID 只是本次运行的记录，不能据此承诺跨主会话恢复。
续接依靠 PROJECT、STATE、账本与实际代码；线程相关且实际可用时再复用。

## 三件事分别检查

### 1. 静态安装

`doctor` 检查文件、格式、固定模型字段、角色生成结果、知识就绪标记、路径引用和账本格式。
它不调用模型，不能证明角色被客户端发现，也不能认证知识内容或证据引用正确。

### 2. 实际角色返回

初始化和升级时，为当前任务安排五个短只读子任务：

| 角色 | 可用的只读检查方向 |
|---|---|
| Rebel | 从实际项目说明指出一个需要区分的真实约束或默认假设 |
| Inventor | 从跨学科索引提出一个适用机制与不适用条件 |
| Hacker | 读取真实入口，指出一个符号与具体实现观察 |
| Scientist | 核对一个影响下一步的主张及其证据或未知项 |
| Producer | 根据现有入口指出如何开始使用，或一个实际交付阻塞 |

这些检查不是固定工种边界；各角色仍可从其他角度提出有用判断。
传入不同的本次校验标记、必要路径与共同目标，等待真实返回，记录工具线程 ID、标记和证据。
在五个返回之后，由 Maverick 综合是否已经可用。无需修改业务实现、执行业务训练或重复全员讨论。

工具能选择已发现的命名角色时，按实际情况记 `native_subagent`。
只能提示词委派时，真实加载对应人格、偏好和相关知识，使用五个独立子 Agent，记 `delegated_subagent`；
这可以完成真实协作，但不能宣称原生角色配置验收成功。完全没有子 Agent 工具时，报告六人格协作未完成。

仅命名任务为 `mav_rebel`，或主线程模拟五个人格的口吻，不构成独立角色返回。
同一模型的不同线程也不保证自然产生不同意见；首轮提供共同事实，避免先灌入主协调者或其他伙伴的结论。

### 3. 初始参与记录

V1.2 以现有账本的 `phase: "initial"` 标记已返回的判断，`reviewed` 表示已完成判断但尚无确认影响。
主线程的 `perspective` 不计入独立初始参与；同一个子线程不能冒充多个初始人格。

```bash
python3 .agents/skills/maverick/scripts/maverick.py report --project . \
  --task TASK_ID --require-full-team
```

记录齐全返回 0，不齐全返回 2，格式问题返回 1，均不等于对真实调用或证据的独立认证。
报告将缺失和冲突显示出来；没有记录不能倒推历史上从未参与。
普通 `report` 保留旧任务回顾能力，无须改写旧账本。

这只是已有 CLI 的记录检查，不是能拦截其他工具的运行时控制器。
必须先收到各角色判断、综合意见，再开始任务实施，这一顺序由 Skill 和主协调者遵守。

## 升级与行为边界

V1.2 保留固定模型、人格核心、项目知识结构和手动人格 `update`。
框架升级保留项目数据；遇到手工修改的核心文件冲突时先核对，不能静默覆盖。
本地修改的人格及偏好继续保留，若包含与新版协作约定相反的用户要求，应明确列出并按优先级处理。

STATE 保存事实与进展，不应继续把旧版“角色可省略”的框架说明当成当前调度规则。
同一任务的继续或恢复使用已有任务 ID 与初始记录；不要因一次编译、工具返回或状态询问召集全员。
新任务先全员独立判断，后续追问则由 Maverick 根据停滞、矛盾、复杂度或实际阻塞决定。
贡献只按真实影响报告，不强制所有角色得分，不触发自动人格演化。

## V1.2 的开发验证

2026-11-23 已运行 17 项安装与贡献功能检查。另从实际 V1.1.1 发布快照和 V1.0 源码分别升级
临时项目，确认项目资料保留、固定模型配置正确，重复升级无文件变化。

使用新安装的 Skill 完成了一次小型加权汇总修复：五个不同真实子线程分批返回只读判断，
主协调者记录综合并通过首轮完整性检查后才修改函数；原有样例实际输出 `4.0`，最终记录为 6/6。
该验证使用提示词委派，证明了这一任务中的实际协作流程；没有验证目标 Codex 原生 TOML 角色加载。
主协调者受本次会话模型覆盖，子线程请求固定模型档位；工具没有单独返回模型认证字段，
不把请求配置当成运行模型已核实，也不据单个任务保证后续所有任务都会遵守规则。

## 官方依据

以下是本仓库配置机制的文档入口，具体支持情况以目标客户端实际加载结果为准：

- [Subagents：角色格式、配置与继承](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Config basics：配置优先级与项目信任](https://learn.chatgpt.com/docs/config-file/config-basic)
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
