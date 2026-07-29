# Temperature sweep

Qwen3-8B, thinking mode, v3 prompts, 267 papers, top_p=0.95, top_k=20. Three seeds per temperature.

| Temp | Seeds | F1 mean | F1 sd | Precision | Recall | Thought closed | Looped |
|---|---|---|---|---|---|---|---|
| 0.3 | 3 | **0.571** | 0.011 | 0.583 | 0.559 | 99% | 3.7 |
| 0.6 | 3 | **0.586** | 0.009 | 0.592 | 0.581 | 100% | 0.0 |
| 0.9 | 3 | **0.590** | 0.010 | 0.598 | 0.581 | 100% | 0.0 |
| 1.2 | 3 | **0.588** | 0.015 | 0.597 | 0.580 | 100% | 0.0 |
