# Forge 0.1.0：运行边界与协议

## 两种执行者，六个人格

AGY 是 Maverick 主对话。五个 Codex CLI 会话独立加载人格，并持续绑定同一角色。
MCP 桥接仅做进程、会话和结果管理，不内置另一个模型、模型路由或后台决策服务。

一次调用由人格原文、该人格的项目偏好、必要事实入口、当前委派组成。
首轮准备独立意见；Maverick 综合后沿相关会话继续工作。所有轮次使用完整 OS 权限。
对主要机制的修改由 AGY 拍板，具体实现由伙伴自主推进。

## 入口

- `scripts/forge.py`：安装、更新、doctor、固定模型启动。
- `forge/server.py`：JSON-RPC / MCP stdio，短调用即时返回，长调用在线程中等待 Codex。
- `forge/runtime.py`：固定模型、人格拼装、两并发队列、进程取消、精确会话续接、记录实际返回。
- `forge/report.schema.json`：本轮状态、结论、下一步、证据、修改文件及实际命令。
- `scripts/contributions.py`：复用原版 ledger，兼容旧任务，不新建一套评分系统。

`forge_dispatch(project, task_id, persona, prompt)` 每任务每角色只创建一次。
返回真实 `run_id`，并从 Codex `thread.started` 事件获取 session ID。
`forge_resume(run_id, prompt)` 不能改变 persona/project/model；同一会话不接受并发续接。
启动失败且没有 session 时，resume 重试启动同一个角色，不编造会话。

`forge_status` 读取当前任务，用于恢复或明确询问进度。
`forge_cancel` 只取消桥接自己拥有的作业。
`forge_decide` 在五份有效首轮之后记录 AGY 综合，后续无需再次召开全员会议。
`forge_record` 确认实际作用或记录尚未确认的意见；可用 `event_id` 修订同一贡献，
用 `shift: {before, after}` 记有证据的理解转变。
`forge_report` 合并实际会话覆盖与六人格贡献。

## 后台等待

AGY MCP 的 `tools.<name>.background="always"` 用于 dispatch/resume，`eager=true` 直接注册工具，
`timeoutSeconds=-1` 允许长回合。服务器在 Codex 结束后才返回 tool result；AGY 负责后台等待和唤醒。
服务器不先返回 queued 再要求模型轮询。CLI 中的等待不会消耗用于“检查有没有完成”的模型回合。

MCP server 随 AGY 客户端连接存活。客户端关闭时结束其拥有的活动调用。
非正常退出后保留任务状态；旧进程仍在时报告失联，不悄悄再启动同一会话的写入者。
没有常驻调度 daemon，也不保证外部操作系统强制终止后的未写盘内容能恢复。

## 持久数据

```text
.maverick/
  PROJECT.md                  项目目标、真实边界与入口
  STATE.md                    简短交接与当前 task_id
  preferences.json            用户主动调整的人格习惯
  knowledge/                  专业知识与证据
  contributions.jsonl         跨版本贡献事实
  forge-manifest.json         安装归属与固定主控配置
  forge/
    start                     启动器
    tasks/<task_id>/
      decision.json           Maverick 的综合选择
      <persona>/
        run.json              会话身份与当前状态
        round-1/
          invocation.json     实际 argv 与工作目录
          prompt.md           本次人格与委派
          events.jsonl        Codex 事件流
          stderr.log          当前回合错误输出
          report.json         当前回合结构化结果
```

每轮文件分开，失败不会返回上轮报告冒充新成果。桥接自身产生的 session/进程字段
与模型请求分开；未观测到实际运行模型时保持未知，不将配置值当作实际观测。
这些文件是项目工作记录。发布项目时按自己的需要决定是否纳入 Git，不自动提交。

## 完整性不等于科学结论成立

初次有效返回写 `mode=delegated_subagent`、真实 actor、`phase=initial`、`reviewed`、`impact=null`。
五个不同会话真实返回后才可以保存 Maverick 综合。对 ledger 的格式检查不能认证证据正确；
Forge 的状态核对增加了实际进程返回依据，同样不是抗恶意篡改审计系统。

AGY 根据真实结果判断影响。调用次数、读文件数和消耗都不能代替贡献。
模块的数学优势是否保住，需要该工程本身的推导、实现与针对性实验，不能靠人格提示词保证。

## 已核对的接口来源

- [AGY CLI 参数](https://antigravity.google/docs/cli/reference/)
- [Neon 模型 slug](https://antigravity.google/docs/cli/headless/)
- [AGY 权限设置](https://antigravity.google/docs/agent-settings/)
- [MCP 后台配置](https://antigravity.google/docs/mcp/)
- [项目级 skill/MCP 发现](https://antigravity.google/docs/customization-discovery/)
- Codex CLI 本地验证版本：`0.172.0-alpha.2`，以实际 `exec --help` 与 `exec resume --help` 为准。
- [Castor 参考实现](https://github.com/JAY201368/codex-castor/tree/e3c07b0c947f212f4c1f9441e6139e730362368c)
