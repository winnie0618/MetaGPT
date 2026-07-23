# 第6章 实验设计与结果分析

## 6.1 数据集设计

实验数据集位于 `data/government_service/test_questions.jsonl`，围绕高校毕业生就业创业补贴办理构造 50 条问题。样本覆盖政策咨询、申请条件、材料清单、办理流程、高风险决策和复杂组合问题。每条样本包含期望回答关键词、期望材料、期望流程步骤、期望风险等级、是否需要人工复核和期望证据关键词。

## 6.2 对比方法

论文实验可设置四类方法：普通模板回答、关键词检索 + 模板回答、本地 FAISS 检索 + 模板回答、本文的可追溯多智能体协同方法。后续接入开源大模型后，可增加 LLM 直接回答、LLM + RAG 和 RAG + 多智能体协同方法作为对比。

当前代码已经支持通过 `--knowledge-backend` 切换检索后端：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_eval --dataset data\government_service\test_questions.jsonl --knowledge-backend keyword --output workspace\government_service\eval_keyword.json
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_eval --dataset data\government_service\test_questions.jsonl --knowledge-backend rag --output workspace\government_service\eval_rag.json
```

也可以直接运行检索对比脚本：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_retrieval_compare --dataset data\government_service\test_questions.jsonl --output workspace\government_service\retrieval_compare.json
```

该脚本会同时输出 JSON 结果和可直接粘贴到论文中的 Markdown 表格。

## 6.3 评价指标

系统当前实现了回答关键词命中率、政策依据命中率、风险等级准确率、人工复核触发准确率、材料命中率和流程步骤命中率。其中材料命中率只在 `expected_materials` 非空样本上计算，流程步骤命中率只在 `expected_process_steps` 非空样本上计算，避免无关样本稀释指标。

## 6.4 当前实验结果记录

评测结果保存到 `workspace/government_service/eval_results.json`。当前环境已启用本地 FAISS 检索，知识库后端状态为 `rag`，索引文件保存在 `workspace/government_service/rag`。未安装 `streamlit`，因此 Web 演示以安装提示方式运行。

当前本地 FAISS 版本评测结果如下：

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

检索后端对比结果如下：

| backend | actual_backend_counts | answer_keyword_hit_rate | evidence_keyword_hit_rate | risk_accuracy | human_review_accuracy | material_hit_rate | process_step_hit_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| keyword | {"keyword": 50} | 0.9233 | 0.8333 | 1.0000 | 1.0000 | 0.6019 | 0.4020 |
| rag | {"rag": 50} | 0.8933 | 0.7600 | 1.0000 | 1.0000 | 0.6389 | 0.5098 |

与关键词检索 baseline 相比，本地 FAISS 哈希检索在材料命中率和流程步骤命中率上有所提升，但政策依据关键词命中率下降。论文中可将这一现象作为误差分析：哈希向量提高了近似匹配能力，但仍缺少真正的中文语义表示，后续需要接入中文 embedding 模型进行对照实验。

## 6.5 后续实验扩展

后续应接入中文 embedding 模型并重建 FAISS 索引，比较关键词检索、本地哈希 FAISS 和语义 FAISS 的政策依据命中率差异；接入 Qwen 等开源模型后，比较模板回答与 LLM 生成回答在完整性、可读性和幻觉率上的差异。
