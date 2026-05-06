# Benchmark Report

This report compares the performance of the single-agent baseline against the multi-agent orchestration pipeline.

## Metrics Summary

| Run | Latency (s) | Cost (USD) | Quality (Est) | Notes |
|---|---:|---:|---:|---|
| Baseline | 4.37s | $0.0001 | N/A | History: . Sources: 0. |
| Multi-Agent | 20.17s | $0.0012 | N/A | History: researcher -> analyst -> writer -> critic -> done. Sources: 5. |
| Baseline | 1.94s | $0.0001 | N/A | History: . Sources: 0. |
| Multi-Agent | 26.46s | $0.0012 | N/A | History: researcher -> analyst -> writer -> critic -> done. Sources: 5. |
| Baseline | 5.79s | $0.0002 | N/A | History: . Sources: 0. |
| Multi-Agent | 90.68s | $0.0014 | N/A | History: researcher -> analyst -> writer -> critic -> done. Sources: 5. |

## Analysis

### Key Findings
- **Latency**: Multi-agent systems typically exhibit higher latency due to sequential agent reasoning and intermediate orchestration overhead.
- **Cost**: Multi-agent runs involve more token exchanges (supervisor instructions, agent handoffs), increasing API costs compared to a single-shot prompt.
- **Traceability**: Multi-agent runs provide rich state logs and role separation, making it easier to debug failures in the research phase vs. the writing phase.

### Recommendation
Use **Multi-Agent** for complex, high-stakes research tasks where citation accuracy and depth are critical. Use **Baseline** for simple queries where speed and cost-efficiency are prioritized.
