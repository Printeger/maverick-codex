# Maverick Forge

**AGY 掌舵，五个 Codex 人格独立思考和动手。**

Maverick Forge 是原 Maverick Codex 的独立分支版本。AGY 直接承担 Maverick，
使用 **Gemini 4 Neon · high**，给 Rebel、Inventor、Hacker、Scientist、Producer
分派任务，接收真实返回，选择研发路线，再沿原会话继续开发。

保留原来的六种个性、跨学科机制库、项目记忆和贡献报告。
没有第七个“管理者”，没有 Research / Execution 分流，也不自动切换模型。

- **当前产品：Forge 0.1.0**，分支 [`maverick-forge`](https://github.com/Printeger/maverick-codex/tree/maverick-forge)。
- 原版 Maverick Codex 保留在 [`main`](https://github.com/Printeger/maverick-codex/tree/main)。
- 运行环境：macOS / Linux / WSL，Python 3.11+、AGY CLI、Codex CLI；两个客户端使用你已有的登录。

## 一条命令安装

在**要开发的项目目录**执行：

```bash
curl -fsSL https://raw.githubusercontent.com/Printeger/maverick-codex/maverick-forge/scripts/install.sh | bash -s -- --project "$PWD"
```

然后启动：

```bash
./.maverick/forge/start
```

也可以直接带任务：

```bash
./.maverick/forge/start '结合前两轮训练的代码、日志和结果，找出当前瓶颈，选一个值得验证的机制并完成下一轮改进。'
```

安装器把运行时完整复制进项目；下载目录随后可以删除。
缺少 CLI、登录或指定模型时会说明实际缺口，不换模型冒充成功。
详细安装、初始化、升级和排错见 [INSTALL.md](INSTALL.md)。

## 六种人格都保留了什么

六份 [`personas/`](personas/) 原文沿用原版。每个 Codex 回合实际装入对应全文和项目偏好，
不是只把任务名字改成“Rebel”。AGY 主控技能要求读取完整 Maverick。

| 人格 | 脾气与思考习惯 | 执行者 / 固定模型 |
|---|---|---|
| **Maverick** | 有品味、有主见，讨厌形式主义；听完最强异议后拍板 | AGY · `gemini-4-neon-high` · high |
| **Rebel** | 不接受现成答案；先问限制来自自然规律、用户还是历史实现 | Codex · `gpt-6.2-sol` · high |
| **Inventor** | 爱折腾、好奇，把远处的机制带到眼前的问题 | Codex · `gpt-6.2-sol` · high |
| **Hacker** | 技术自信、直接，对多余包装层没有耐心 | Codex · `gpt-6.2-sol` · medium |
| **Scientist** | 好奇又诚实，证据足够就继续，不追求无穷确定性 | Codex · `gpt-6.2-sol` · high |
| **Producer** | 对浪费敏感，先去掉让成果不能使用的真实阻塞 | Codex · `gpt-6.2-sol` · medium |

人格决定怎样思考、取舍和说话；项目知识决定掌握哪些事实。
Inventor 的 [`knowledge/`](knowledge/INDEX.md) 保留控制、信息、认知、实验、网络、物理和生物适应的机制入口，
进入新领域时按需迁移、查证，不被单个项目的专业背景取代。

## 每个任务怎样推进

1. **AGY 准备共同事实。** 目标、真实边界、前几轮结果、证据和未解问题；已有方案只是候选。
2. **五个独立 Codex 首轮。** 各自先判断，不先接收 Maverick 的标准答案。桥接默认同时运行两个，其余排队。
3. **Maverick 综合并决定。** 选哪种机制，谁的意见改变了选择，哪个替代暂不采用；不等待全员一致。
4. **沿原会话开发。** 给相关角色新证据和下一步，不重复完整历史，不每次重新开五人会。
5. **按实际成果汇报。** 参与事实来自真实会话返回，贡献等级来自已经发生的作用。

同一目标的编译修复、进度问答、断点恢复不重新开始首轮。
角色完成判断可以支持已有路线，不要求每人造一个新方案。
独立首轮是任务安排，**不使用只读操作系统沙箱**。

### 这次专门修正的研发习惯

**先选择有价值的机制，再缩小验证它的实现。** “最小实现”不能被偷偷解释成“只敢调一个参数”。
AGY 决定算法语义、目标函数、有效工作区间和主要研发路线；Codex 自主完成实现细节。

历史代码的保守门限不自动成为用户约束。若新增门限、时序契约或回退会削弱选定机制，
Codex 要把影响交给 AGY 判断，而非为了假想审稿意见悄悄加上。AGY 可以直接决定并继续执行。
必要校验保留，检查只回答当前具体问题；没有额外评测 Agent 或人格 benchmark。

## 权限已经按完整开发配置

启动器使用：

```text
agy --model gemini-4-neon-high --effort high --mode accept-edits --dangerously-skip-permissions
```

同时合并 AGY 的设置：自动执行工具、关闭终端沙箱、允许访问工作区外文件、自动处理 artifact review。
Codex 子进程固定使用 `--dangerously-bypass-approvals-and-sandbox`；当前 CLI 支持时同时使用
`--dangerously-bypass-hook-trust`。没有额外只读层，也不逐项批准正常开发操作。

权限设置位于 `~/.gemini/antigravity-cli/settings.json`，其他设置和已有显式规则保留。
这是当前系统账户可用的操作权限，不会修改操作系统管理策略或替用户提权。
具体参数依据 [AGY CLI](https://antigravity.google/docs/cli/reference/) 和
[Agent settings](https://antigravity.google/docs/agent-settings/)；
Codex 参数由本地 `codex exec --help` / `codex exec resume --help` 检查。

## 协调和上下文成本

MCP 的 dispatch/resume 配成 AGY 后台工具。桥接等待 Codex 回合结束后返回，AGY 再继续；
等待过程不靠模型轮询。完成结果只回传结论、证据、会话身份和产物路径，异常时才读原始日志。

每个人格绑定真实 Codex session ID，续接不能换人格或并发写进同一会话。
AGY 可以关闭后重新进入：从 `STATE.md`、当前任务状态和保存的会话恢复。
模型会话本身仍有上下文限制；保存会话并不意味着无限上下文，也不是永远在线的守护进程。

## 贡献怎么记

桥接为真正完成的首轮自动记 `reviewed`，**不自动打分**。
`forge_decide` 保存 Maverick 的选择。AGY 观察到意见实际改变路线、实现或判断后，
再用 `forge_record` 记录方向、实施或纠错贡献，等级 1 / 2 / 3；没有确认影响就留空。

`forge_report` 同时显示真实参与与实际贡献，区分独立 Codex 会话和主控直接工作。
失败、空报告、刚派发的任务不算已参与；同一 session 不能改名顶替另一人格。
总账继续使用 `.maverick/contributions.jsonl`，不按调用量、耗时或代码行评分。

## 已有 Maverick 项目怎么升级

在原项目再执行上面的安装命令即可。安装器会：

- 保留项目 `PROJECT.md`、`STATE.md`、知识、人格偏好和旧贡献账本。
- 将旧安装中实际使用的人格与机制卡迁入 Forge，包括手工强化的内容。
- 用明确的 AGY 主控 / Codex worker 身份路由替换旧托管根协议，并保留该旧块。
- 保留原 `.codex/` 配置与原版技能，合并新 MCP 项而不删除其他服务。
- 更新未改动的托管文件；有本地修改时保留，给出新版本候选文件路径。

旧任务不会补造五份过去并未发生的判断。新产品使用 `maverick-forge` 名称，不抢占旧 skill 名。
人格 `update` 仍由用户主动触发；安装升级不自动重写人格习惯。

## 开发与验证

```bash
python3 tests/forge_bridge_smoke.py
python3 tests/forge_install_smoke.py
python3 tests/smoke.py
```

前两项使用真实子进程配合 fake Codex/AGY 可执行文件，验证 MCP、参数、续接、取消、迁移和启动。
它们不调用收费模型，**不等于现场 AGY → Codex → AGY 推理验证**。
`doctor` 另检实际 CLI、登录、模型列表和 MCP 握手；现场回传需在装有 AGY 的环境运行一次真实任务。
实现细节见 [桥接协议](docs/forge-architecture.md)。

本版发布环境验证（2026-11-28）：桥接 3 组检查、安装迁移 8 个用例、旧版 17 个用例均通过。
真实 Codex CLI 探针在模型请求前被该托管环境的权限要求拒绝（不允许 `danger-full-access`），
没有退回只读或改用其他模型；本环境也没有 AGY。真实模型返回和 AGY 后台唤醒因此尚未现场通过。

## 参考

通信方式参考 [JAY201368/codex-castor](https://github.com/JAY201368/codex-castor)：
AGY 通过 MCP 调度本地 Codex，异步接收结果，沿原 session 继续。
Forge 另实现六人格绑定、项目迁移和真实参与记录，保留本仓库的人格体系。
上游许可与来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
