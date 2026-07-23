# 政务服务智能体系统依赖说明

本系统第一阶段规则版不依赖外部大模型即可运行，默认使用 `SimplePolicyKnowledgeBase` 进行关键词检索。第二阶段增强版支持 MetaGPT RAG / FAISS、LLM 生成和 Web 演示，需要额外安装可选依赖。

## 基础运行

基础命令行和评测功能依赖项目现有虚拟环境：

```powershell
venv\Scripts\python.exe -m pytest tests\metagpt\ext\government_service -q
venv\Scripts\python.exe -m metagpt.ext.government_service.eval.run_eval --dataset data\government_service\test_questions.jsonl --output workspace\government_service\eval_results.json
```

## RAG / FAISS 增强依赖

若要启用 MetaGPT RAG / FAISS 检索，需要安装：

```powershell
venv\Scripts\python.exe -m pip install llama-index-core llama-index-vector-stores-faiss llama-index-embeddings-huggingface sentence-transformers
```

当前环境已经安装 `faiss_cpu`，但未安装 `llama_index`，因此 `RAGPolicyKnowledgeBase` 会自动回退到关键词检索，并在 `status()` 中记录失败原因。例如：

```json
{
  "backend": "fallback",
  "ready": false,
  "last_error": "RAG 初始化失败: No module named 'llama_index'"
}
```

这种降级设计保证依赖缺失时系统仍可完成政策检索、风险判断、追溯日志和评测。

## Web 演示依赖

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
