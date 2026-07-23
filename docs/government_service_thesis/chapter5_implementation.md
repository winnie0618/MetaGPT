# 第5章 基于 MetaGPT 的系统实现

## 5.1 项目目录

政务服务扩展模块位于 `metagpt/ext/government_service`。其中 `actions` 目录实现具体动作，`roles` 目录实现多智能体角色，`eval` 目录实现评测数据读取和指标计算，`knowledge_base.py` 实现政策知识库，`workflow.py` 提供统一系统入口。

## 5.2 核心模块

`schema.py` 定义 `ServiceIntent`、`PolicyEvidence`、`MaterialItem`、`ProcessStep`、`RiskAssessment`、`TraceRecord` 和 `ServiceResponse` 等数据结构。`knowledge_base.py` 提供关键词检索、本地 FAISS 检索和 TF-IDF 统计向量检索，其中 FAISS 索引持久化到 `workspace/government_service/rag`。`trace_record.py` 将执行过程写入 `workspace/government_service/traces`，并通过 `TraceRecordStore` 支持按 `trace_id` 查询和最近记录读取。

## 5.3 核心 Action

系统包含 `IntentRecognizeAction`、`PolicyRetrieveAction`、`MaterialChecklistAction`、`TaskPlanAction`、`RiskAssessAction`、`HumanReviewAction`、`AnswerGenerateAction` 和 `TraceRecordAction`。其中回答生成支持模板模式和 LLM 模式，当前默认使用模板模式保证离线可运行。

## 5.4 核心 Role

`PolicyExpert` 封装政策检索，`ProcessPlanner` 封装材料和流程生成，`RiskAuditor` 封装风险审核，`ServiceCoordinator` 负责整体调度和追溯记录。该结构体现了 MetaGPT 框架下的角色分工和动作编排。

为支持实验分析，`GovServiceWorkflow` 提供 `enable_process_planner`、`enable_risk_auditor` 和 `enable_trace_record` 配置项。正常系统运行时三者均开启；消融实验中可分别关闭某一模块，观察材料命中率、流程步骤命中率、风险准确率和追溯落盘率的变化。

## 5.5 运行方式

命令行演示：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.demo_cli
```

评测脚本：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_eval --dataset data\government_service\test_questions.jsonl --output workspace\government_service\eval_results.json
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_retrieval_compare --dataset data\government_service\test_questions.jsonl --output workspace\government_service\retrieval_compare.json
```

Web 演示在安装 Streamlit 后运行：

```powershell
venv\Scripts\streamlit.exe run metagpt/ext/government_service/web_demo.py
```

为了保证答辩展示不受可选依赖影响，系统还提供基于 Python 标准库的本地 Web 演示：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.local_web_demo --host 127.0.0.1 --port 8765
```

打开 `http://127.0.0.1:8765` 后，可在页面中切换 `FAISS`、`Keyword` 和 `TF-IDF` 三种检索后端，并查看最终回答、政策依据、材料清单、办理步骤、风险等级和 `trace_id`。页面还支持按 `trace_id` 查询追溯链路，展示执行动作序列、检索文档、风险判断和知识库状态。
