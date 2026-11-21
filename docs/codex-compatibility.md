# Codex 兼容性与初始化验收

核对日期：2026-11-21。本地核对版本为 `codex-cli 0.172.0-alpha.2`。
配置格式依据下列官方文档。其他版本以实际加载结果为准。

## 使用的原生机制

- 项目指导：项目根目录 `AGENTS.md`。
- 项目 Skill：`.agents/skills/<name>/SKILL.md`，包含 `name`、`description` frontmatter。
- 项目子 Agent：`.codex/agents/<name>.toml`，一个文件定义一个人格。
- 项目配置：`.codex/config.toml`；只合并需要的配置，不覆盖已有设置。

子 Agent 的必填键是 `name`、`description`、`developer_instructions`。
可选模型键包括 `model`、`model_reasoning_effort`、`model_reasoning_summary` 和 `model_verbosity`。
本项目不硬编码模型 ID；省略模型和推理强度时沿用父会话的配置。
如需便宜模型，使用当前客户端实际可用的 ID，并核对它支持的推理强度。

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 2
```

这里的并发数不含主 Agent。`max_threads` 是并发键的旧别名，不要同时写两者。
`agents.enabled` 当前默认开启；不需要额外写入实验性 feature flags。
不要追加重复的 `[agents]` 表，也不要擅自改动现有模型、MCP 或权限设置。

## 继承与边界

子 Agent 继承父会话的权限、模型提供者、MCP 和 Skills。
角色 TOML 中的 `sandbox_mode`、`approval_policy`、`model_provider`、`mcp_servers`
不能用来替换父会话配置。写着“只读”的人格指令也不是独立的只读沙箱。
角色文件中的模型设置优先于创建时的默认设置，因此不要无意中固定旧模型。

主项目指导必须区分身份：主协调者是 Maverick，子 Agent 保留被分派的人格。
共享项目约束继续适用于所有人格；不要让子 Agent 再扮演 Maverick 或递归分工。
人格更新后优先创建新子线程，不假定旧线程会重新加载修改过的角色文件。

未受信任的项目会跳过项目级 `.codex` 配置层。
初始化过程不会自动修改全局信任、沙箱或审批设置。若配置未被发现，检查当前
客户端的项目信任与版本，并通过其正常流程处理。静态文件存在不代表已经加载。

## 两种验收，分别报告

**静态检查**验证文件、格式、必填键、路径引用、项目知识内容和重复配置。
它不调用模型，也不能证明 Codex 已注册角色或成功创建线程。

**原生运行检查**由正在初始化该项目的 Codex 执行：

1. 确认当前工具确实可以选择命名自定义 Agent，且发现安装的角色。
2. 创建两个只读子任务：Hacker 读取项目一个真实入口，报告路径、符号及一项观察；
   Inventor 读取跨学科索引，给出一个与当前项目有关的机制映射及其不适用条件。
3. 给任务传入不同的本次校验标记，要求各自在结果中回报。只传任务所需路径和背景。
4. 等待真实返回，记录工具返回的子线程 ID、校验标记、证据路径和结果。
   禁止让它们修改业务文件；无需启动全员或执行完整业务测试。
5. 可向其中一个仍可用的线程追加一次简短问题，验证本会话内的复用。
6. 分别报告静态检查及原生运行检查：`PASS`、`NOT_RUN` 或 `BLOCKED`，附简短原因。

仅把子任务命名为 `hacker`，或在主回答中模拟两个角色，不算原生角色验收。
若当前工具只能传提示词，可以另记“提示词方式已运行”，但不能标记原生加载成功。
当前开发环境完成了 CLI 与格式核对；原生推理烟雾测试不可用，未宣称通过。
不要通过更改权限、全局配置或搬运凭据来强行完成验收。

线程 ID 只作为当前运行的记录，不承诺关闭程序或启动新主会话后仍可调用。
跨会话续接依靠项目状态文件；是否恢复旧线程以客户端实际提供的能力为准。

## 官方依据

- [Subagents：角色格式、配置与继承](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Config basics：配置优先级与项目信任](https://learn.chatgpt.com/docs/config-file/config-basic)
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
