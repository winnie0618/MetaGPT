from metagpt.ext.government_service.eval.run_ablation import to_markdown_table


def test_ablation_markdown_table_includes_trace_metric():
    table = to_markdown_table(
        [
            {
                "variant": "full",
                "answer_keyword_hit_rate": 1,
                "evidence_keyword_hit_rate": 1,
                "risk_accuracy": 1,
                "human_review_accuracy": 1,
                "material_hit_rate": 0.5,
                "process_step_hit_rate": 0.25,
                "trace_recorded_rate": 1,
            }
        ]
    )

    assert "| variant |" in table
    assert "trace_recorded_rate" in table
    assert "| full |" in table
