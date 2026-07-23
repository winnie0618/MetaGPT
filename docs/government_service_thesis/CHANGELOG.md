# GovTrace-Agent 本次更改说明

本次提交围绕硕士毕业论文题目《面向政务服务流程的可追溯多智能体协同方法研究与实现》完善了 MetaGPT 政务服务扩展模块，使其从基础规则原型推进到可进行初步实验评测的版本。

## 提交信息

- Commit: `ad1af678`
- Follow-up commit: `071df599`
- Branch: `main`
- Remote: `https://github.com/winnie0618/MetaGPT.git`
- Commit messages: `Enhance government service agent evaluation assets`, `Document GovTrace agent updates`

## 追加更新：本地 FAISS 检索可运行

在后续实现中，`RAGPolicyKnowledgeBase` 已从“仅暴露降级状态”推进为可运行的本地 FAISS 检索模块。系统会读取 `data/government_service/raw_docs/` 下的政策文本，使用确定性哈希向量构建可复现的 384 维向量，并将 `policy.faiss` 与 `policy_metadata.json` 持久化到 `workspace/government_service/rag`。元数据记录政策文本指纹，源文档变化后会自动重建索引。在当前环境下，知识库状态为：

```json
{
  "backend": "rag",
  "ready": true,
  "last_error": ""
}
```

如果 FAISS 初始化或检索失败，系统仍会自动回退到关键词检索，并在回答和追溯日志中记录具体原因。

本地 FAISS 版本的 50 条样本评测结果如下：

```json
{
  "sample_count": 50,
  "answer_keyword_hit_rate": 0.8933,
  "evidence_keyword_hit_rate": 0.76,
  "risk_accuracy": 1.0,
  "human_review_accuracy": 1.0,
  "material_hit_rate": 0.6389,
  "process_step_hit_rate": 0.5098,
  "material_sample_count": 18,
  "process_sample_count": 17,
  "high_risk_sample_count": 11
}
```

该结果说明，本地哈希 FAISS 检索已经能够支撑端到端流程，但政策证据命中率仍有提升空间。论文后续实验应继续加入中文 embedding 模型作为语义检索增强对照。

## 追加更新：检索后端对比实验

系统新增 `knowledge_backend` 配置，可在 `GovServiceWorkflow` 中显式选择 `keyword` 或 `rag`。评测脚本 `run_eval.py` 增加 `--knowledge-backend` 参数，并记录实际后端分布；新增 `run_retrieval_compare.py` 用于一次性比较关键词检索和本地 FAISS 检索，并输出 JSON 与 Markdown 表格。

运行命令：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_retrieval_compare --dataset data\government_service\test_questions.jsonl --output workspace\government_service\retrieval_compare.json
```

该能力用于支撑论文第 6 章的消融实验和对比实验，不需要额外依赖。

## 追加更新：TF-IDF 统计向量检索 baseline

系统新增 `TfidfPolicyKnowledgeBase`，使用 `scikit-learn` 的 TF-IDF 向量化和 `jieba` 中文分词构建离线统计向量检索 baseline。`knowledge_backend` 现在支持 `keyword`、`rag` 和 `tfidf` 三种后端，`run_retrieval_compare.py` 默认输出三组检索对比结果。

最新 50 条样本对比结果如下：

| backend | actual_backend_counts | answer_keyword_hit_rate | evidence_keyword_hit_rate | risk_accuracy | human_review_accuracy | material_hit_rate | process_step_hit_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| keyword | {"keyword": 50} | 0.9233 | 0.8333 | 1.0000 | 1.0000 | 0.6019 | 0.4020 |
| rag | {"rag": 50} | 0.8933 | 0.7600 | 1.0000 | 1.0000 | 0.6389 | 0.5098 |
| tfidf | {"tfidf": 50} | 0.9300 | 0.8300 | 1.0000 | 1.0000 | 0.6389 | 0.3431 |

该结果为论文提供了更完整的检索消融实验基础：关键词检索在证据覆盖上更稳定，本地 FAISS 哈希检索对流程步骤更友好，TF-IDF 在回答关键词和材料抽取上表现较好，但流程步骤召回偏弱。

## 主要改动

### 1. 政务服务知识库扩充

在 `data/government_service/raw_docs/` 中新增多份高校毕业生就业创业补贴相关政策说明文档，使政策文档总数达到 21 个。新增内容覆盖申请对象、毕业年度、就业证明、创业证明、银行卡、线上线下办理、材料补正、审核公示、补贴发放、人工复核、申诉和隐私保护等主题。

### 2. 评测数据集扩展

将 `data/government_service/test_questions.jsonl` 扩展到 50 条样本，覆盖政策咨询、材料清单、办理流程、资格判断、高风险决策和复杂组合问题。每条样本补充了期望回答关键词、期望材料、期望流程步骤、风险等级、人工复核标记和证据关键词。

### 3. 风险识别规则增强

增强了 `IntentRecognizeAction` 和 `RiskAssessAction` 的关键词规则，补充识别审批结果、补贴金额、到账、最终资格认定、最终批准、申诉、虚假材料、重复申领、跨地区申请、公示名单和保证发放等风险表达。高风险问题会触发人工复核提示，避免系统承诺审批结果、补贴金额或最终行政结论。

### 4. RAG 状态可见

`RAGPolicyKnowledgeBase` 增加显式状态记录，包括 `backend`、`ready`、`last_error`、`raw_docs_dir` 和 `persist_dir`。系统优先使用本地 FAISS 检索；当 FAISS 不可用或索引失败时，会回退到关键词检索，并在回答和追溯日志中记录 fallback 原因，而不是静默失败。

### 5. 材料与流程抽取增强

`MaterialChecklistAction` 支持从政策依据片段中抽取身份证明、毕业证书、就业协议、创业证明、银行卡信息、申请表和承诺书等材料。`TaskPlanAction` 支持从政策依据片段中抽取提交申请、受理、审核、公示、补正材料、人工复核和发放等流程步骤。

### 6. 评测脚本完善

`eval/dataset.py` 支持 `utf-8-sig`，避免 Windows 编辑 JSONL 后出现 BOM 导致解析失败。`eval/run_eval.py` 输出回答关键词命中率、政策依据命中率、风险等级准确率、人工复核触发准确率、材料命中率、流程步骤命中率和各类样本数量。

### 7. 论文材料补充

扩写 `docs/government_service_thesis/` 下的论文辅助材料，并新增 `setup_dependencies.md`。`figures.md` 包含系统架构、多智能体协同、本地 FAISS 检索与降级、风险分级和追溯日志的 Mermaid 图草稿。

## 验证结果

单元测试：

```text
venv\Scripts\python.exe -m pytest tests\metagpt\ext\government_service -q
8 passed, 10 warnings
```

数据规模：

```text
raw_docs_count: 21
test_questions_count: 50
```

评测结果：

```json
{
  "sample_count": 50,
  "answer_keyword_hit_rate": 0.9233,
  "evidence_keyword_hit_rate": 0.8333,
  "risk_accuracy": 1.0,
  "human_review_accuracy": 1.0,
  "material_hit_rate": 0.6019,
  "process_step_hit_rate": 0.4020,
  "material_sample_count": 18,
  "process_sample_count": 17,
  "high_risk_sample_count": 11
}
```

## 当前限制

当前环境尚未安装 `streamlit`，Web Demo 文件已支持安装提示但尚未在 Streamlit 环境中完成真实页面验收。当前 FAISS 版本使用确定性哈希向量而非中文语义 embedding，适合作为可复现实验基线；后续工作应优先接入中文 embedding、Web 演示和 LLM 生成模式实验。
