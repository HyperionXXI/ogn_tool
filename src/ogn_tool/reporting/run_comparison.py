def compare_runs(run_A, run_B):
    """
    Compare two RFAnalysisReport dicts (from report.json).
    Returns a dict with comparability, summary_delta, network_delta, coverage_delta.
    """
    def dict_delta(a, b):
        keys = set(a) | set(b)
        delta = {}
        for k in keys:
            if a.get(k) != b.get(k):
                delta[k] = {"A": a.get(k), "B": b.get(k)}
        return delta

    comparability = {
        "fields_A": list(run_A.keys()),
        "fields_B": list(run_B.keys()),
        "fields_in_common": list(set(run_A) & set(run_B)),
        "fields_only_in_A": list(set(run_A) - set(run_B)),
        "fields_only_in_B": list(set(run_B) - set(run_A)),
    }
    summary_delta = dict_delta(run_A.get("summary_metrics", {}), run_B.get("summary_metrics", {}))
    network_delta = dict_delta(run_A.get("network_metrics", {}), run_B.get("network_metrics", {}))
    coverage_delta = dict_delta(run_A.get("coverage_metrics", {}), run_B.get("coverage_metrics", {}))
    return {
        "comparability": comparability,
        "summary_delta": summary_delta,
        "network_delta": network_delta,
        "coverage_delta": coverage_delta,
    }
