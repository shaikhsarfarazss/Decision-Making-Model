"""
StudyShield — Academic Benchmark & Latency Profiling (3-Layer YouTube Engine)
Evaluates accuracy, confusion matrix, Study-vs-Coding separation, and latency percentiles
on 50 test cases in tests/test_titles.json.
"""

import json
import os
import sys
import time
import numpy as np

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from decision_engine import LayaDecisionEngine


def run_benchmark():
    print("==========================================================================")
    print("   StudyShield: 3-Layer YouTube Categorization & Latency Benchmark        ")
    print("==========================================================================")

    data_path = os.path.join(os.path.dirname(__file__), "test_titles.json")
    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    engine = LayaDecisionEngine()

    # Warmup pass
    engine.decide("Warmup video", "Warmup channel", focus_domain="aiml")
    engine.cache.clear()

    latencies = []
    tp = 0  # True Positives: correctly predicted educational (study or coding)
    fp = 0  # False Positives: predicted educational but was distraction
    tn = 0  # True Negatives: correctly predicted distraction
    fn = 0  # False Negatives: predicted distraction but was educational

    study_count = 0
    coding_count = 0
    detailed_results = []

    print(f"\nEvaluating {len(dataset)} YouTube items across 20 YouTube Categories...")

    for item in dataset:
        title = item["title"]
        channel = item["channel"]
        expected_is_study = item["expected_is_study"]

        t0 = time.perf_counter()
        result = engine.decide(title=title, channel=channel, focus_domain="aiml")
        latency = (time.perf_counter() - t0) * 1000
        latencies.append(latency)

        if result.category_tag == "study":
            study_count += 1
        elif result.category_tag == "coding":
            coding_count += 1

        is_correct = result.is_study == expected_is_study

        if expected_is_study and result.is_study:
            tp += 1
        elif not expected_is_study and result.is_study:
            fp += 1
        elif not expected_is_study and not result.is_study:
            tn += 1
        elif expected_is_study and not result.is_study:
            fn += 1

        detailed_results.append({
            "title": title,
            "channel": channel,
            "expected_study": expected_is_study,
            "predicted_study": result.is_study,
            "category": result.category,
            "category_tag": result.category_tag,
            "youtube_category_id": result.youtube_category_id,
            "youtube_macro_category": result.youtube_macro_category,
            "knowledge_graph_topics": result.knowledge_graph_topics,
            "confidence": result.confidence,
            "latency_ms": round(latency, 4),
            "is_correct": is_correct,
        })

    total = len(dataset)
    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    mean_lat = float(np.mean(latencies))
    p50_lat = float(np.percentile(latencies, 50))
    p95_lat = float(np.percentile(latencies, 95))
    min_lat = float(np.min(latencies))
    max_lat = float(np.max(latencies))

    print("\n--- 3-LAYER YOUTUBE CLASSIFICATION & ACCURACY METRICS ---")
    print(f"Total Test Cases         : {total}")
    print(f"Academic Study Detected  : {study_count} items (YouTube ID 27: Education)")
    print(f"Coding & Dev Detected    : {coding_count} items (YouTube ID 28: Science & Tech)")
    print(f"Overall Accuracy         : {accuracy * 100:.2f}%")
    print(f"Precision                : {precision * 100:.2f}%")
    print(f"Recall (Sensitivity)     : {recall * 100:.2f}%")
    print(f"F1-Score                 : {f1 * 100:.2f}%")
    print(f"Confusion Matrix         : TP={tp}, FP={fp}, TN={tn}, FN={fn}")

    print("\n--- LATENCY & REAL-TIME PROFILING ---")
    print(f"Mean Latency (Avg)       : {mean_lat:.3f} ms")
    print(f"Median Latency (p50)     : {p50_lat:.3f} ms")
    print(f"95th Percentile (p95)    : {p95_lat:.3f} ms")
    print(f"Fastest Execution        : {min_lat:.3f} ms")
    print(f"Worst-Case Execution     : {max_lat:.3f} ms")

    output_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "accuracy": accuracy,
                "f1_score": f1,
                "mean_latency_ms": mean_lat,
                "p50_latency_ms": p50_lat,
                "p95_latency_ms": p95_lat,
                "study_count": study_count,
                "coding_count": coding_count,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
                "detailed": detailed_results,
            },
            f,
            indent=2,
        )
    print(f"\nSaved 3-Layer benchmark data to {output_path}")


if __name__ == "__main__":
    run_benchmark()
