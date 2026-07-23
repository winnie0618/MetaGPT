from __future__ import annotations

import asyncio

import streamlit as st

from metagpt.ext.government_service.workflow import GovServiceWorkflow


st.set_page_config(page_title="GovTrace-Agent", page_icon="🏛️", layout="wide")
st.title("GovTrace-Agent 政务服务演示")
st.write("输入政务服务问题，查看政策依据、材料清单、流程步骤、风险等级与 trace_id。")

query = st.text_input("请输入政务服务问题", placeholder="例如：高校毕业生创业补贴需要哪些材料？")

workflow = GovServiceWorkflow()

if st.button("开始问答") and query:
    resp = asyncio.run(workflow.run(query))
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("最终回答")
        st.text(resp.direct_answer)
        st.subheader("风险评估")
        st.write(resp.risk_assessment.model_dump())
        st.write(f"trace_id: {resp.trace_id}")
    with col2:
        st.subheader("政策依据")
        for item in resp.policy_evidence:
            st.markdown(f"- **{item.title}**：{item.snippet}")
        st.subheader("材料清单")
        for item in resp.materials:
            st.markdown(f"- {item.name}（{'必需' if item.required else '可选'}）{item.note}")
        st.subheader("办理步骤")
        for step in resp.process_steps:
            st.markdown(f"- {step.step_no}. {step.title}：{step.detail}")
        if resp.human_review_message:
            st.warning(resp.human_review_message)
