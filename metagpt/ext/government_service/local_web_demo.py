from __future__ import annotations

import argparse
import asyncio
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from metagpt.ext.government_service.actions.trace_record import TraceRecordStore
from metagpt.ext.government_service.workflow import GovServiceWorkflow


BACKENDS = {"keyword", "rag", "tfidf"}
DEFAULT_QUERY = "高校毕业生创业补贴需要哪些材料，办理流程是什么？"


def build_payload(query: str, backend: str = "rag") -> dict[str, Any]:
    if backend not in BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}")
    workflow = GovServiceWorkflow(knowledge_backend=backend)
    response = asyncio.run(workflow.run(query))
    kb_status = workflow.coordinator.policy_expert.last_status
    return {
        "query": query,
        "backend": backend,
        "knowledge_base_status": kb_status,
        "response": response.model_dump(mode="json"),
    }


def build_trace_payload(trace_id: str) -> dict[str, Any]:
    record = TraceRecordStore().find_by_trace_id(trace_id)
    if record is None:
        raise ValueError(f"Trace not found: {trace_id}")
    return {"trace_id": trace_id, "record": record}


def build_recent_traces_payload(limit: int = 20) -> dict[str, Any]:
    records = TraceRecordStore().list_recent(limit=limit)
    return {"count": len(records), "records": records}


class GovTraceDemoHandler(BaseHTTPRequestHandler):
    server_version = "GovTraceDemo/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in {"/", "/index.html"}:
            self._send_html(INDEX_HTML)
            return
        if path == "/api/health":
            self._send_json({"ok": True, "backends": sorted(BACKENDS)})
            return
        if path == "/api/traces":
            params = parse_qs(parsed.query)
            limit = int((params.get("limit") or ["20"])[0])
            self._send_json(build_recent_traces_payload(limit=limit))
            return
        if path.startswith("/api/trace/"):
            trace_id = unquote(path.removeprefix("/api/trace/"))
            try:
                self._send_json(build_trace_payload(trace_id))
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/query":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        try:
            payload = self._read_json()
            query = str(payload.get("query") or DEFAULT_QUERY).strip()
            backend = str(payload.get("backend") or "rag").strip()
            if not query:
                raise ValueError("query is required")
            result = build_payload(query=query, backend=backend)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


INDEX_HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GovTrace-Agent</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #182026;
      --muted: #5f6b76;
      --line: #d8dee6;
      --brand: #146c5f;
      --brand-dark: #0d4c43;
      --warn: #a64020;
      --ok: #1c6b44;
      --shadow: 0 10px 30px rgba(24, 32, 38, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.55 "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }
    header {
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }
    .topbar {
      max-width: 1280px;
      margin: 0 auto;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 240px;
    }
    .mark {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: var(--brand);
      color: white;
      font-weight: 700;
      letter-spacing: 0;
    }
    h1 {
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    .subtitle {
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
    }
    .status-pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #f8fafb;
      color: var(--muted);
      padding: 6px 10px;
      white-space: nowrap;
      font-size: 12px;
    }
    main {
      max-width: 1280px;
      width: 100%;
      margin: 0 auto;
      padding: 20px 24px 28px;
      display: grid;
      grid-template-columns: minmax(320px, 420px) 1fr;
      gap: 16px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      min-width: 0;
    }
    .input-panel {
      padding: 16px;
      align-self: start;
      position: sticky;
      top: 16px;
    }
    label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 8px;
    }
    textarea {
      width: 100%;
      min-height: 128px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      color: var(--ink);
      outline: none;
      font: inherit;
      background: #fbfcfd;
    }
    textarea:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(20, 108, 95, 0.12);
    }
    .segmented {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      margin: 14px 0;
    }
    .segmented button {
      border: 0;
      border-right: 1px solid var(--line);
      padding: 10px 8px;
      background: #ffffff;
      color: var(--muted);
      cursor: pointer;
      font: inherit;
    }
    .segmented button:last-child { border-right: 0; }
    .segmented button.active {
      background: var(--brand);
      color: #ffffff;
      font-weight: 700;
    }
    .primary {
      width: 100%;
      height: 42px;
      border: 0;
      border-radius: 8px;
      background: var(--brand);
      color: #ffffff;
      font-weight: 700;
      cursor: pointer;
      font: inherit;
    }
    .primary:hover { background: var(--brand-dark); }
    .examples {
      display: grid;
      gap: 8px;
      margin-top: 14px;
    }
    .examples button {
      text-align: left;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      color: var(--ink);
      padding: 10px;
      cursor: pointer;
      font: inherit;
    }
    .trace-lookup {
      border-top: 1px solid var(--line);
      margin-top: 16px;
      padding-top: 14px;
      display: grid;
      gap: 8px;
    }
    input {
      width: 100%;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 10px;
      color: var(--ink);
      outline: none;
      font: inherit;
      background: #fbfcfd;
    }
    input:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(20, 108, 95, 0.12);
    }
    .button-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .secondary {
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
    }
    .workspace {
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 16px;
      min-width: 0;
    }
    .answer {
      padding: 16px;
      white-space: pre-wrap;
    }
    .answer h2, .section h2 {
      margin: 0 0 10px;
      font-size: 15px;
      letter-spacing: 0;
    }
    .meta-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 10px;
    }
    .metric {
      padding: 12px;
    }
    .metric .value {
      font-size: 18px;
      font-weight: 700;
      color: var(--brand-dark);
      overflow-wrap: anywhere;
    }
    .metric .label {
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
    }
    .detail-grid {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 16px;
      align-items: start;
    }
    .section {
      padding: 16px;
    }
    .list {
      display: grid;
      gap: 10px;
    }
    .item {
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }
    .item:first-child {
      border-top: 0;
      padding-top: 0;
    }
    .item-title {
      font-weight: 700;
      margin-bottom: 4px;
      overflow-wrap: anywhere;
    }
    .item-body {
      color: var(--muted);
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }
    .risk-high { color: var(--warn); }
    .risk-low, .risk-medium { color: var(--ok); }
    .empty {
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 16px;
      background: #fbfcfd;
    }
    .loading {
      opacity: 0.65;
      pointer-events: none;
    }
    @media (max-width: 920px) {
      main {
        grid-template-columns: 1fr;
        padding: 12px;
      }
      .input-panel {
        position: static;
      }
      .meta-grid, .detail-grid {
        grid-template-columns: 1fr;
      }
      .topbar {
        align-items: flex-start;
        flex-direction: column;
        padding: 14px 12px;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <div class="topbar">
        <div class="brand">
          <div class="mark">GT</div>
          <div>
            <h1>GovTrace-Agent</h1>
            <div class="subtitle">面向政务服务流程的可追溯多智能体协同演示</div>
          </div>
        </div>
        <div class="status-pill" id="serverStatus">本地服务就绪</div>
      </div>
    </header>
    <main>
      <section class="panel input-panel">
        <label for="query">政务服务问题</label>
        <textarea id="query">高校毕业生创业补贴需要哪些材料，办理流程是什么？</textarea>
        <label>检索后端</label>
        <div class="segmented" id="backendGroup">
          <button type="button" data-backend="rag" class="active">FAISS</button>
          <button type="button" data-backend="keyword">Keyword</button>
          <button type="button" data-backend="tfidf">TF-IDF</button>
        </div>
        <button class="primary" id="submitBtn" type="button">运行协同流程</button>
        <div class="examples">
          <button type="button" data-query="高校毕业生创业补贴需要哪些材料，办理流程是什么？">材料和流程咨询</button>
          <button type="button" data-query="我能不能确定拿到创业补贴，金额是多少？">高风险结果判断</button>
          <button type="button" data-query="申请创业补贴被要求补正材料时该怎么办？">材料补正咨询</button>
        </div>
        <div class="trace-lookup">
          <label for="traceQuery">Trace ID 查询</label>
          <input id="traceQuery" placeholder="运行后自动填入，也可粘贴历史 trace_id" />
          <div class="button-row">
            <button class="secondary" id="traceSearchBtn" type="button">查询链路</button>
            <button class="secondary" id="recentTraceBtn" type="button">最近记录</button>
          </div>
        </div>
      </section>
      <section class="workspace">
        <section class="panel answer">
          <h2>最终回答</h2>
          <div id="answerText" class="empty">等待运行</div>
        </section>
        <section class="meta-grid">
          <div class="panel metric">
            <div class="value" id="riskLevel">-</div>
            <div class="label">风险等级</div>
          </div>
          <div class="panel metric">
            <div class="value" id="reviewFlag">-</div>
            <div class="label">人工复核</div>
          </div>
          <div class="panel metric">
            <div class="value" id="backendValue">-</div>
            <div class="label">知识库后端</div>
          </div>
          <div class="panel metric">
            <div class="value" id="traceId">-</div>
            <div class="label">Trace ID</div>
          </div>
        </section>
        <section class="detail-grid">
          <div class="panel section">
            <h2>政策依据</h2>
            <div id="evidenceList" class="list empty">等待运行</div>
          </div>
          <div class="panel section">
            <h2>材料清单</h2>
            <div id="materialList" class="list empty">等待运行</div>
          </div>
          <div class="panel section">
            <h2>办理步骤</h2>
            <div id="stepList" class="list empty">等待运行</div>
          </div>
          <div class="panel section">
            <h2>追溯状态</h2>
            <div id="traceStatus" class="list empty">等待运行</div>
          </div>
          <div class="panel section">
            <h2>追溯链路</h2>
            <div id="traceRecord" class="list empty">等待查询</div>
          </div>
        </section>
      </section>
    </main>
  </div>
  <script>
    const state = { backend: "rag" };
    const $ = (id) => document.getElementById(id);
    const queryInput = $("query");
    const submitBtn = $("submitBtn");
    const traceQuery = $("traceQuery");

    document.querySelectorAll("#backendGroup button").forEach((button) => {
      button.addEventListener("click", () => {
        state.backend = button.dataset.backend;
        document.querySelectorAll("#backendGroup button").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
      });
    });

    document.querySelectorAll(".examples button").forEach((button) => {
      button.addEventListener("click", () => {
        queryInput.value = button.dataset.query;
      });
    });

    submitBtn.addEventListener("click", runQuery);
    $("traceSearchBtn").addEventListener("click", queryTrace);
    $("recentTraceBtn").addEventListener("click", loadRecentTraces);

    async function runQuery() {
      const query = queryInput.value.trim();
      if (!query) return;
      setLoading(true);
      try {
        const response = await fetch("/api/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, backend: state.backend })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "请求失败");
        render(payload);
      } catch (error) {
        $("serverStatus").textContent = error.message;
      } finally {
        setLoading(false);
      }
    }

    function render(payload) {
      const response = payload.response;
      const risk = response.risk_assessment || {};
      const status = payload.knowledge_base_status || {};
      $("answerText").className = "";
      $("answerText").textContent = response.direct_answer || "";
      $("riskLevel").textContent = risk.risk_level || "-";
      $("riskLevel").className = "value risk-" + (risk.risk_level || "low");
      $("reviewFlag").textContent = risk.human_review_required ? "需要" : "不需要";
      $("backendValue").textContent = status.backend || payload.backend || "-";
      $("traceId").textContent = response.trace_id || "-";
      traceQuery.value = response.trace_id || "";
      $("evidenceList").className = "list";
      $("materialList").className = "list";
      $("stepList").className = "list";
      $("traceStatus").className = "list";
      $("evidenceList").innerHTML = renderEvidence(response.policy_evidence || []);
      $("materialList").innerHTML = renderMaterials(response.materials || []);
      $("stepList").innerHTML = renderSteps(response.process_steps || []);
      $("traceStatus").innerHTML = renderStatus(status, risk);
      $("traceRecord").className = "list";
      $("traceRecord").innerHTML = emptyText("已生成 trace_id，可点击查询链路");
      $("serverStatus").textContent = "最近运行：" + new Date().toLocaleTimeString();
    }

    async function queryTrace() {
      const traceId = traceQuery.value.trim();
      if (!traceId) return;
      setLoading(true);
      try {
        const response = await fetch("/api/trace/" + encodeURIComponent(traceId));
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "查询失败");
        $("traceRecord").className = "list";
        $("traceRecord").innerHTML = renderTraceRecord(payload.record);
        $("serverStatus").textContent = "追溯查询：" + traceId;
      } catch (error) {
        $("traceRecord").className = "list";
        $("traceRecord").innerHTML = emptyText(error.message);
      } finally {
        setLoading(false);
      }
    }

    async function loadRecentTraces() {
      setLoading(true);
      try {
        const response = await fetch("/api/traces?limit=10");
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || "查询失败");
        $("traceRecord").className = "list";
        $("traceRecord").innerHTML = renderRecentTraces(payload.records || []);
        $("serverStatus").textContent = "最近记录：" + (payload.count || 0);
      } catch (error) {
        $("traceRecord").className = "list";
        $("traceRecord").innerHTML = emptyText(error.message);
      } finally {
        setLoading(false);
      }
    }

    function renderEvidence(items) {
      if (!items.length) return emptyText("无政策依据");
      return items.map((item) => `
        <div class="item">
          <div class="item-title">${escapeHtml(item.title)} · ${Number(item.score || 0).toFixed(4)}</div>
          <div class="item-body">${escapeHtml(item.snippet)}</div>
        </div>
      `).join("");
    }

    function renderMaterials(items) {
      if (!items.length) return emptyText("无材料清单");
      return items.map((item) => `
        <div class="item">
          <div class="item-title">${escapeHtml(item.name)} · ${item.required ? "必需" : "可选"}</div>
          <div class="item-body">${escapeHtml(item.note || "")}</div>
        </div>
      `).join("");
    }

    function renderSteps(items) {
      if (!items.length) return emptyText("无办理步骤");
      return items.map((item) => `
        <div class="item">
          <div class="item-title">${item.step_no}. ${escapeHtml(item.title)}</div>
          <div class="item-body">${escapeHtml(item.detail || "")}</div>
        </div>
      `).join("");
    }

    function renderStatus(status, risk) {
      return `
        <div class="item">
          <div class="item-title">Knowledge Base</div>
          <div class="item-body">backend=${escapeHtml(status.backend || "")}; ready=${Boolean(status.ready)}</div>
        </div>
        <div class="item">
          <div class="item-title">Risk Reason</div>
          <div class="item-body">${escapeHtml(risk.reason || "")}</div>
        </div>
        <div class="item">
          <div class="item-title">Last Error</div>
          <div class="item-body">${escapeHtml(status.last_error || "无")}</div>
        </div>
      `;
    }

    function renderTraceRecord(record) {
      if (!record) return emptyText("未找到追溯记录");
      const metadata = record.metadata || {};
      return `
        <div class="item">
          <div class="item-title">${escapeHtml(record.trace_id || "")}</div>
          <div class="item-body">${escapeHtml(record.timestamp || "")}</div>
        </div>
        <div class="item">
          <div class="item-title">Query / Intent</div>
          <div class="item-body">${escapeHtml(record.query || "")}\nintent=${escapeHtml(record.intent || "")}</div>
        </div>
        <div class="item">
          <div class="item-title">Actions</div>
          <div class="item-body">${escapeHtml((record.actions || []).join(" -> "))}</div>
        </div>
        <div class="item">
          <div class="item-title">Retrieved Docs</div>
          <div class="item-body">${escapeHtml((record.retrieved_docs || []).join("\\n"))}</div>
        </div>
        <div class="item">
          <div class="item-title">Risk / Backend</div>
          <div class="item-body">risk=${escapeHtml(record.risk_level || "")}; review=${Boolean(record.human_review_required)}; backend=${escapeHtml(metadata.backend || "")}</div>
        </div>
      `;
    }

    function renderRecentTraces(records) {
      if (!records.length) return emptyText("暂无追溯记录");
      return records.map((record) => `
        <div class="item">
          <div class="item-title">${escapeHtml(record.trace_id || "")}</div>
          <div class="item-body">${escapeHtml(record.timestamp || "")}\n${escapeHtml(record.query || "")}</div>
        </div>
      `).join("");
    }

    function emptyText(text) {
      return `<div class="empty">${escapeHtml(text)}</div>`;
    }

    function setLoading(isLoading) {
      submitBtn.textContent = isLoading ? "运行中..." : "运行协同流程";
      document.body.classList.toggle("loading", isLoading);
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), GovTraceDemoHandler)
    print(f"GovTrace-Agent local demo: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("GovTrace-Agent local demo stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
