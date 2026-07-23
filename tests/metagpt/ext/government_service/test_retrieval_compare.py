from metagpt.ext.government_service.eval.run_retrieval_compare import to_markdown_table


def test_to_markdown_table_formats_metric_values():
    table = to_markdown_table(
        [
            {
                "requested_backend": "keyword",
                "actual_backend_counts": {"keyword": 2},
                "answer_keyword_hit_rate": 1,
                "evidence_keyword_hit_rate": 0.5,
                "risk_accuracy": 1,
                "human_review_accuracy": 1,
                "material_hit_rate": 0.75,
                "process_step_hit_rate": None,
            }
        ]
    )

    assert "| backend |" in table
    assert "| keyword |" in table
    assert "0.5000" in table
