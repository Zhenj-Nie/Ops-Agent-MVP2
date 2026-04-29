# Ops Agent MVP：通用运营自动化多 Agent 控制台

我构建了一个通用运营自动化多Agent控制台项目，包含：

* 前端控制台：任务创建、触发、运行记录查看、通知测试
* 后端 API：FastAPI
* 多 Agent 调度：Planner / Executor / Verifier / Reporter
* 任务队列：SQLite 持久化队列 + 后台 Worker 轮询
* 飞书通知占位：默认写入数据库和日志；配置 Webhook 后可推送飞书群
* SQLite 数据库：任务、运行记录、队列、通知日志
* 示例业务：股票/指标监控任务，可作为运营自动化骨架改造为企业微信、飞书、多维表格、广告 API、CRM、BI 等

> 说明：项目默认不依赖真实行情 API，使用 MockMarketDataAdapter 生成模拟价格，保证本地直接跑通。后续你可以在 `app/adapters/market\_data.py` 中接入真实股票、广告投放、飞书多维表格、企业微信等 API。

\---

## 1\. 项目解决的核心痛点

运营、投放、销售、客服和业务团队常见问题是：

1. **数据源分散**：股票/投放/线索/表格/客服数据分布在多个平台，人工汇总耗时。
2. **重复监控成本高**：价格、预算消耗、转化率、异常订单、客户线索等指标需要持续盯盘。
3. **异常响应慢**：只有人工发现问题后才会通知，容易错过最佳处理时间。
4. **分析链路不标准**：不同人对异常判断、原因归因、行动建议的口径不一致。
5. **自动化难扩展**：单脚本能跑，但接入飞书、企业微信、广告 API、多维表格后容易变成不可维护的脚本堆。

本项目用多 Agent 和任务队列把流程拆成标准化模块：

* Planner Agent：把业务目标拆成执行计划。
* Executor Agent：调用外部 API 或内部工具获取数据。
* Verifier Agent：检查数据质量、异常阈值和风险。
* Reporter Agent：生成运营摘要、决策建议和通知内容。
* Notifier Adapter：把结果推送到飞书/企微/邮件等渠道。

\---

## 2\. 核心逻辑流：是否包含长链推理和多 Agent 协作

本 MVP 包含轻量级“长链任务拆解”和多 Agent 协作。逻辑链路如下：

```text
用户在前端创建任务
        ↓
FastAPI 写入 SQLite 任务表
        ↓
任务进入 SQLite 队列表
        ↓
后台 Worker 拉取待执行任务
        ↓
Planner Agent：分析任务目标、拆解步骤、确认数据源和阈值
        ↓
Executor Agent：读取股票/运营指标/广告/API 数据
        ↓
Verifier Agent：判断是否触发阈值、是否存在异常、数据是否可信
        ↓
Reporter Agent：生成结构化报告、行动建议、通知文案
        ↓
Notifier：飞书通知占位；可替换为飞书、企微、多维表格、广告平台回写
        ↓
运行结果写回 SQLite，前端控制台展示
```

这里的“长链推理”不是让一个大模型一次性完成所有步骤，而是将任务拆成多个可观测、可测试、可替换的 Agent 节点。这样做的好处是：

* 每一步都能落库，方便排查。
* 后续可以把任意 Agent 替换成真实 LLM、规则引擎或公司内部服务。
* 可以在 Verifier 阶段做风控，避免错误数据直接触发通知或自动操作。
* 可以控制 token 使用：只在 Planner/Reporter 需要生成文本时调用 LLM，Executor/Verifier 尽量用结构化规则完成。

\---

## 3\. 快速启动

### 3.1 创建环境

```bash
cd ops-agent-mvp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 3.2 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

浏览器打开：

```text
http://127.0.0.1:8080
```

### 3.3 一键创建示例任务

在前端点“创建股票监控 Demo”，或命令行：

```bash
curl -X POST http://127.0.0.1:8080/api/demo/stock-monitor
```

查看运行记录：

```bash
curl http://127.0.0.1:8080/api/runs
```

\---

## 4\. 飞书通知占位

默认不会真实发送，只会写入 `notifications` 表和日志。

如需接入飞书机器人 Webhook，在 `.env` 或环境变量里配置：

```bash
export FEISHU\_WEBHOOK\_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"
```

然后调用：

```bash
curl -X POST http://127.0.0.1:8080/api/notifications/test \\
  -H 'Content-Type: application/json' \\
  -d '{"text":"测试飞书通知"}'
```

\---

## 5\. 如何扩展到企业微信、飞书多维表格、广告 API

建议按 Adapter 方式接入：

```text
app/adapters/
  market\_data.py       股票/指标数据源
  feishu.py            飞书通知
  wecom.py             企业微信通知，可新增
  bitable.py           飞书多维表格，可新增
  ads\_api.py           巨量/腾讯/百度广告 API，可新增
```

然后在 `ExecutorAgent` 中根据 `task\_type` 调用对应 Adapter。

例如：

* `stock\_monitor`：监控股票价格或业务指标。
* `ads\_budget\_monitor`：监控广告消耗、ROI、转化成本。
* `lead\_followup`：从多维表格读取线索，提醒销售跟进。
* `content\_ops`：监控内容数据，生成选题和复盘建议。
* `customer\_service\_audit`：质检客服对话，推送高风险会话。

\---

## 6\. API 简表

|方法|路径|说明|
|-|-|-|
|GET|`/`|前端控制台|
|GET|`/api/health`|健康检查|
|POST|`/api/tasks`|创建任务|
|GET|`/api/tasks`|任务列表|
|POST|`/api/tasks/{task\_id}/enqueue`|手动触发任务|
|GET|`/api/runs`|运行记录|
|GET|`/api/runs/{run\_id}`|运行详情|
|POST|`/api/demo/stock-monitor`|创建股票监控 Demo|
|POST|`/api/notifications/test`|测试飞书通知占位|

\---

## 7\. 项目结构

```text
ops-agent-mvp/
  app/
    main.py
    config.py
    db.py
    queue.py
    orchestrator.py
    schemas.py
    agents/
      base.py
      planner.py
      executor.py
      verifier.py
      reporter.py
    adapters/
      feishu.py
      market\_data.py
      llm.py
    static/
      index.html
      app.js
      style.css
  data/
    ops\_agent.db   # 首次启动自动生成
  requirements.txt
  .env.example
  run.sh
  run.bat
```

\---

## 8\. 生产化建议

MVP 用 SQLite 队列方便本地跑通。生产环境建议逐步替换：

* SQLite → PostgreSQL
* 内置 Worker → Celery / RQ / Dramatiq
* MockMarketDataAdapter → 真实业务 API
* FeishuNotifier → 飞书/企业微信/邮件/SMS 多通道
* 简单规则 Verifier → LLM + 规则 + 数据质量检测
* 单机部署 → Docker Compose / Kubernetes

