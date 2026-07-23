# GovTrace-Agent 第二阶段开发计划

## 阶段目标

第一阶段已经完成规则版闭环：意图识别、政策检索、材料清单、流程规划、风险判断、人工复核和追溯日志都能跑通。

第二阶段目标是把系统升级为毕业论文可用版本：

1. 接入 MetaGPT RAG / FAISS，替换简单关键词检索。
2. 接入可配置大语言模型，用于生成更自然、更完整的政务服务回答。
3. 构造实验数据集，支持对比实验。
4. 增加评测指标和实验脚本。
5. 增加 Web 或 Streamlit 演示界面。
6. 固化论文第 4、5、6 章可写内容。

## 总体路线

```text
第一阶段规则原型
  -> 政务数据集扩充
  -> RAG / FAISS 知识库
  -> LLM 生成增强
  -> 多智能体协同稳定化
  -> 实验数据集与评价指标
  -> Web 演示
  -> 论文材料沉淀
```

## 第 1 步：整理真实政务数据

### 目标

把 `data/government_service/raw_docs/` 从示例文件扩展为真实或半真实的政务文档集合。

### 建议数据规模

先准备 20 到 50 个 `.txt` 或 `.md` 文件。

### 文档类型

```text
办事指南
申请条件
申请材料说明
办理流程
常见问题
政策原文
地方补贴通知
窗口办理说明
线上平台办理说明
```

### 推荐目录

```text
data/government_service/
  raw_docs/
    policy_001_高校毕业生就业创业补贴政策.txt
    guide_001_高校毕业生创业补贴办理指南.txt
    faq_001_就业创业补贴常见问题.txt
  processed_docs/
```

### 验收标准

1. 至少 20 个政策/指南/FAQ 文档。
2. 文件统一 UTF-8 编码。
3. 每个文件标题清楚。
4. 不包含隐私信息。

## 第 2 步：升级知识库为 RAG / FAISS

### 目标

在保留 `SimplePolicyKnowledgeBase` 的基础上，新增一个 `RAGPolicyKnowledgeBase`。

### 建议新增文件

```text
metagpt/ext/government_service/rag_knowledge_base.py
```

### 功能要求

1. 支持从 `raw_docs` 构建 FAISS 索引。
2. 支持索引持久化。
3. 支持相似度检索 top_k。
4. 返回统一的 `PolicyEvidence`。
5. 如果 RAG 初始化失败，自动回退到 `SimplePolicyKnowledgeBase`。

### 建议接口

```python
class RAGPolicyKnowledgeBase:
    def __init__(self, raw_docs_dir=None, persist_dir=None):
        ...

    def build_index(self) -> None:
        ...

    def retrieve(self, query: str, top_k: int = 3) -> list[PolicyEvidence]:
        ...
```

### 验收标准

1. 能从多篇政策文档构建索引。
2. 能保存索引。
3. 再次运行时能加载索引。
4. 检索结果比关键词 fallback 更准确。

## 第 3 步：增加 LLM 生成增强

### 目标

当前回答是模板式的。第二阶段需要加入 LLM 生成，使回答更接近真实政务助手。

### 建议新增 Action

```text
actions/answer_generate.py
```

### 输入

```text
用户问题
意图
政策依据
材料清单
办理步骤
风险评估
人工复核提示
```

### 输出

```text
结构化中文回答
```

### 生成约束

必须要求模型：

1. 只能基于给定政策依据回答。
2. 不得承诺审批结果。
3. 不得编造补贴金额。
4. 涉及高风险事项必须保留人工复核提示。
5. 输出包括“办理建议、政策依据、材料清单、风险提示”。

### 第一版可选方案

如果本地暂时没有模型，可以先保留模板生成，同时把 `AnswerGenerateAction` 做成可插拔：

```text
use_llm=False -> 模板回答
use_llm=True  -> 调用 MetaGPT LLM
```

### 验收标准

1. 模板模式可用。
2. LLM 模式可配置。
3. 高风险问题不会输出最终审批结论。

## 第 4 步：完善多智能体协同结构

### 目标

现在 `workflow.py` 已经串起了 Action，但 Role 层还比较薄。第二阶段要让论文里的“多智能体协同”更站得住。

### 建议优化

1. `ServiceCoordinator` 负责主流程调度。
2. `PolicyExpert` 负责政策检索和依据解释。
3. `ProcessPlanner` 负责流程步骤和材料清单。
4. `RiskAuditor` 负责风险判断和人工复核。

### 代码要求

让 `workflow.py` 不再直接调用所有 Action，而是通过 Role 或 Role-like service 调用：

```text
ServiceCoordinator
  -> PolicyExpert
  -> ProcessPlanner
  -> RiskAuditor
```

### 验收标准

1. Role 文件不再只是空壳。
2. 每个 Role 至少封装 1 到 2 个 Action。
3. trace 日志记录 Role 与 Action 执行链路。

## 第 5 步：构造实验数据集

### 目标

准备论文第 6 章实验。

### 建议文件

```text
data/government_service/test_questions.jsonl
```

每条样本格式：

```json
{
  "id": "q001",
  "query": "高校毕业生创业补贴需要哪些材料？",
  "intent": "material_checklist",
  "expected_answer_contains": ["身份证明", "毕业证书", "创业证明"],
  "expected_risk_level": "low",
  "expected_human_review_required": false,
  "expected_evidence_keywords": ["申请材料", "毕业证书"]
}
```

### 数据规模

第一版 50 条，论文版扩展到 100 到 200 条。

### 分类建议

```text
政策咨询类：20%
申请条件类：20%
材料清单类：20%
办理流程类：20%
高风险决策类：10%
复杂组合类：10%
```

### 验收标准

1. 至少 50 条测试问题。
2. 每条有 expected_risk_level。
3. 每条有 expected_answer_contains。
4. 高风险样本不少于 10 条。

## 第 6 步：完善评测指标

### 目标

把 `eval/metrics.py` 从简单 contains 扩展为论文可用指标。

### 指标设计

```text
answer_keyword_hit_rate：回答关键词命中率
evidence_keyword_hit_rate：政策依据命中率
risk_accuracy：风险等级准确率
human_review_accuracy：人工复核触发准确率
material_hit_rate：材料清单命中率
process_step_hit_rate：流程步骤命中率
average_latency：平均响应时间
```

### 对比方法

```text
Baseline 1：规则/模板直接回答
Baseline 2：关键词检索 + 模板回答
Ours：RAG + 多智能体协同 + 风险复核 + 可追溯
```

如果接入 LLM 后，再加：

```text
Baseline 3：LLM 直接回答
Baseline 4：LLM + RAG
```

### 验收标准

1. `python -m metagpt.ext.government_service.eval.run_eval --dataset ...` 可运行。
2. 输出每个指标。
3. 输出整体平均结果。
4. 结果能保存为 JSON 或 CSV。

## 第 7 步：增加 Web 演示界面

### 目标

答辩时能直观看到系统。

### 推荐方案

优先用 Streamlit，最快。

新增：

```text
metagpt/ext/government_service/web_demo.py
```

### 页面功能

1. 输入政务服务问题。
2. 显示最终回答。
3. 显示政策依据。
4. 显示材料清单。
5. 显示办理步骤。
6. 显示风险等级。
7. 显示是否需要人工复核。
8. 显示 trace_id。

### 验收标准

运行：

```text
streamlit run metagpt/ext/government_service/web_demo.py
```

能打开页面并完成一次问答。

## 第 8 步：论文材料沉淀

### 目标

每做完一个模块，就同步沉淀论文材料，避免最后补论文时手忙脚乱。

### 建议新增目录

```text
docs/government_service_thesis/
  chapter3_requirements.md
  chapter4_method.md
  chapter5_implementation.md
  chapter6_experiment.md
  figures.md
```

### 必画图

1. 系统总体架构图。
2. 多智能体协同流程图。
3. RAG 政策检索流程图。
4. 风险分级与人工复核流程图。
5. 可追溯日志结构图。
6. 实验流程图。

### 验收标准

1. 每个核心模块都有论文说明文字。
2. 每张图都有图题和解释。
3. 第 4、5、6 章可以直接扩写。

## 推荐开发顺序

```text
1. 扩充真实政策数据
2. 改造 RAG / FAISS 知识库
3. 新增 AnswerGenerateAction
4. 强化 Role 层协同
5. 构造 50 条测试集
6. 扩展 eval 指标
7. 做 Streamlit Web Demo
8. 沉淀论文第 4、5、6 章材料
```

## 给 Copilot 的下一阶段提示词

### 提示词 1：新增 RAG 知识库

```text
请在 metagpt/ext/government_service/rag_knowledge_base.py 中实现 RAGPolicyKnowledgeBase。

要求：
1. 优先复用 MetaGPT examples/rag/rag_pipeline.py 和 metagpt.rag.engines.SimpleEngine。
2. 从 data/government_service/raw_docs/*.txt 加载政策文档。
3. 使用 FAISSRetrieverConfig 构建检索。
4. retrieve(query, top_k) 返回 schema.PolicyEvidence 列表。
5. 如果 RAG 初始化失败，回退到 SimplePolicyKnowledgeBase。
6. 不要破坏现有 SimplePolicyKnowledgeBase。
```

### 提示词 2：新增回答生成 Action

```text
请新增 metagpt/ext/government_service/actions/answer_generate.py，实现 AnswerGenerateAction。

要求：
1. 继承 MetaGPT Action。
2. 支持 use_llm=False 的模板生成模式。
3. 支持 use_llm=True 的 LLM 生成模式。
4. 输入 query、intent、evidences、materials、process_steps、risk_assessment、human_review_message。
5. 输出中文政务服务回答。
6. 高风险问题必须包含人工复核提示。
7. 回答必须引用政策依据，不得编造审批结果或补贴金额。
```

### 提示词 3：强化 Role 层

```text
请重构 metagpt/ext/government_service/roles 下的角色实现。

要求：
1. ServiceCoordinator 负责任务调度。
2. PolicyExpert 封装 PolicyRetrieveAction。
3. ProcessPlanner 封装 TaskPlanAction 和 MaterialChecklistAction。
4. RiskAuditor 封装 RiskAssessAction 和 HumanReviewAction。
5. workflow.py 通过这些 Role 完成流程，而不是直接调用所有 Action。
6. 保持现有测试通过。
```

### 提示词 4：扩展评测数据结构

```text
请扩展 metagpt/ext/government_service/eval/dataset.py 和 metrics.py。

要求：
1. 支持读取 jsonl 数据集。
2. 每条样本包含 id、query、intent、expected_answer_contains、expected_risk_level、expected_human_review_required、expected_evidence_keywords。
3. 实现回答关键词命中率、依据关键词命中率、风险等级准确率、人工复核触发准确率、平均响应时间。
4. run_eval.py 输出整体指标，并保存到 workspace/government_service/eval_results.json。
```

### 提示词 5：新增 Web Demo

```text
请新增 metagpt/ext/government_service/web_demo.py，使用 Streamlit 实现简单演示界面。

页面需要：
1. 输入政务服务问题。
2. 调用 GovServiceWorkflow。
3. 显示最终回答。
4. 展示政策依据、材料清单、办理步骤。
5. 展示风险等级、人工复核提示和 trace_id。
```

## 第二阶段最终验收标准

第二阶段结束时，应满足：

```text
1. 至少 20 个政策/指南/FAQ 文档。
2. RAG / FAISS 检索可用。
3. 多智能体 Role 层职责清晰。
4. 回答生成支持模板模式和 LLM 模式。
5. 至少 50 条测试问题。
6. eval 脚本可输出多项指标。
7. Web demo 可运行。
8. pytest tests/metagpt/ext/government_service -q 通过。
9. 可直接支撑论文第 4、5、6 章写作。
```

