# 政务服务智能体系统依赖说明

本系统第一阶段规则版不依赖外部大模型即可运行，默认使用 `SimplePolicyKnowledgeBase` 进行关键词检索。当前阶段已经支持本地 FAISS 检索和 TF-IDF 统计向量检索；LLM 生成、中文语义 embedding 和 Web 演示属于后续可选增强。

## 基础运行

基础命令行和评测功能依赖项目现有虚拟环境：

```powershell
venv\Scripts\python.exe -m pytest tests\metagpt\ext\government_service -q
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_eval --dataset data\government_service\test_questions.jsonl --output workspace\government_service\eval_results.json
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_retrieval_compare --dataset data\government_service\test_questions.jsonl --output workspace\government_service\retrieval_compare.json
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_ablation --dataset data\government_service\test_questions.jsonl --knowledge-backend rag --output workspace\government_service\ablation_rag.json
venv\Scripts\python.exe -m metagpt.ext.government_service.local_web_demo --host 127.0.0.1 --port 8765
```

当前评测数据集包含 100 条样本，其中高风险样本 23 条、材料清单样本 37 条、流程步骤样本 42 条。

## 本地 FAISS 检索依赖

当前可复现实验版本使用 `faiss-cpu` 和确定性哈希向量构建本地索引，不依赖 `llama_index` 或外部 embedding 服务。若环境中已经安装 `faiss-cpu`，首次检索时会自动在 `workspace/government_service/rag` 下生成：

```text
policy.faiss
policy_metadata.json
```

索引元数据中记录政策文本指纹；当 `data/government_service/raw_docs` 下的源文档发生变化时，系统会自动重建 FAISS 索引，避免继续复用过期检索结果。

运行状态示例：

```json
{
  "backend": "rag",
  "ready": true,
  "last_error": "",
  "raw_docs_dir": "E:\\MetaGPT\\data\\government_service\\raw_docs",
  "persist_dir": "E:\\MetaGPT\\workspace\\government_service\\rag"
}
```

如果 `faiss-cpu` 不可用或索引构建失败，系统会自动回退到关键词检索，并在 `status()` 中记录失败原因。这种降级设计保证依赖缺失时系统仍可完成政策检索、风险判断、追溯日志和评测。

## TF-IDF 统计向量检索依赖

`TfidfPolicyKnowledgeBase` 使用当前虚拟环境中的 `scikit-learn` 和 `jieba`，不需要下载外部模型。它可以通过以下命令单独评测：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_eval --dataset data\government_service\test_questions.jsonl --knowledge-backend tfidf --output workspace\government_service\eval_tfidf.json
```

该后端适合作为关键词检索和深度语义 embedding 检索之间的统计向量 baseline。

## 可选语义检索增强

后续若要将哈希向量替换为中文语义 embedding，可在网络条件允许时安装：

```powershell
venv\Scripts\python.exe -m pip install sentence-transformers
```

也可以继续扩展为 LlamaIndex 管线：

```powershell
venv\Scripts\python.exe -m pip install llama-index-core llama-index-vector-stores-faiss llama-index-embeddings-huggingface sentence-transformers
```

论文实验中建议将“关键词检索”“本地 FAISS 哈希检索”“TF-IDF 统计向量检索”“中文 embedding + FAISS 检索”作为检索对照组。

## Web 演示依赖

标准库本地 Web Demo 不需要额外依赖，可直接运行：

```powershell
venv\Scripts\python.exe -m metagpt.ext.government_service.local_web_demo --host 127.0.0.1 --port 8765
```

访问地址：

```text
http://127.0.0.1:8765
```

页面提供 `/api/query`、`/api/trace/{trace_id}` 和 `/api/traces` 三类接口，可用于演示问答生成、单条追溯链路查询和最近追溯记录查看。

若要运行 Streamlit Web Demo，需要安装：

```powershell
venv\Scripts\python.exe -m pip install streamlit
```

运行方式：

```powershell
venv\Scripts\streamlit.exe run metagpt/ext/government_service/web_demo.py
```

如果未安装 `streamlit`，直接运行 `web_demo.py` 会输出提示：

```text
请先安装 streamlit：pip install streamlit
```

## 大语言模型配置

`AnswerGenerateAction` 默认使用模板模式 `use_llm=False`，不需要联网或配置模型。后续接入 Qwen、DeepSeek 或其他开源/接口模型时，可将 `use_llm=True`，并通过 MetaGPT 的 LLM 配置统一管理模型调用。高风险问题仍必须保留人工复核提示，不得让模型承诺审批结果、补贴金额或资格最终认定。
