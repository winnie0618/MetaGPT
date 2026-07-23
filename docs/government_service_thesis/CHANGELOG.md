# GovTrace-Agent 本次更改说明

本次提交围绕硕士毕业论文题目《面向政务服务流程的可追溯多智能体协同方法研究与实现》完善了 MetaGPT 政务服务扩展模块，使其从基础规则原型推进到可进行初步实验评测的版本。

## 提交信息

- Commit: `ad1af678`
- Branch: `main`
- Remote: `https://github.com/winnie0618/MetaGPT.git`
- Commit message: `Enhance government service agent evaluation assets`

## 主要改动

### 1. 政务服务知识库扩充

在 `data/government_service/raw_docs/` 中新增多份高校毕业生就业创业补贴相关政策说明文档，使政策文档总数达到 21 个。新增内容覆盖申请对象、毕业年度、就业证明、创业证明、银行卡、线上线下办理、材料补正、审核公示、补贴发放、人工复核、申诉和隐私保护等主题。

### 2. 评测数据集扩展

将 `data/government_service/test_questions.jsonl` 扩展到 50 条样本，覆盖政策咨询、材料清单、办理流程、资格判断、高风险决策和复杂组合问题。每条样本补充了期望回答关键词、期望材料、期望流程步骤、风险等级、人工复核标记和证据关键词。

### 3. 风险识别规则增强

增强了 `IntentRecognizeAction` 和 `RiskAssessAction` 的关键词规则，补充识别审批结果、补贴金额、到账、最终资格认定、最终批准、申诉、虚假材料、重复申领、跨地区申请、公示名单和保证发放等风险表达。高风险问题会触发人工复核提示，避免系统承诺审批结果、补贴金额或最终行政结论。

### 4. RAG 降级状态可见

`RAGPolicyKnowledgeBase` 增加显式状态记录，包括 `backend`、`ready`、`last_error`、`raw_docs_dir` 和 `persist_dir`。当前环境缺少 `llama_index` 时，系统会回退到关键词检索，并在回答和追溯日志中记录 fallback 原因，而不是静默失败。

### 5. 材料与流程抽取增强

`MaterialChecklistAction` 支持从政策依据片段中抽取身份证明、毕业证书、就业协议、创业证明、银行卡信息、申请表和承诺书等材料。`TaskPlanAction` 支持从政策依据片段中抽取提交申请、受理、审核、公示、补正材料、人工复核和发放等流程步骤。

### 6. 评测脚本完善

`eval/dataset.py` 支持 `utf-8-sig`，避免 Windows 编辑 JSONL 后出现 BOM 导致解析失败。`eval/run_eval.py` 输出回答关键词命中率、政策依据命中率、风险等级准确率、人工复核触发准确率、材料命中率、流程步骤命中率和各类样本数量。

### 7. 论文材料补充

扩写 `docs/government_service_thesis/` 下的论文辅助材料，并新增 `setup_dependencies.md`。`figures.md` 包含系统架构、多智能体协同、RAG 降级、风险分级和追溯日志的 Mermaid 图草稿。

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

当前环境尚未安装 `llama_index` 和 `streamlit`。因此 RAG / FAISS 模块当前处于 fallback 模式，Web Demo 文件已支持降级提示但尚未在 Streamlit 环境中完成真实页面验收。后续工作应优先安装 RAG 和 Web 依赖，完成真实 FAISS 检索、Web 演示和 LLM 生成模式实验。
