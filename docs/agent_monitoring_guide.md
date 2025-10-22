# Agent Monitoring Configuration

## AI Agents (TruLens)

| Agent | LLM Used | Metrics Tracked |
|-------|----------|-----------------|
| DataAgent | CORTEX.COMPLETE (mistral-large) | Relevance, Groundedness, SQL Quality, Latency, Token Usage |
| InsightAgent | CORTEX.COMPLETE (mistral-large) | Relevance, Groundedness, Insight Quality, Latency |
| BenchmarkAgent (LLM mode) | CORTEX.COMPLETE (mistral-large) | Context Quality, Accuracy, Latency |

## Internal Agents (Traditional Metrics)

| Agent | Technology | Metrics Tracked |
|-------|------------|-----------------|
| VisualizationAgent | Plotly + Pandas | Execution Time, Success Rate, Chart Type Accuracy, Error Rate |
| BenchmarkAgent (DB mode) | SQL Query | Query Time, Cache Hit Rate, Data Freshness |

## Human Agents (Manual Tracking)

| Agent | Activity | Metrics Tracked |
|-------|----------|-----------------|
| Benchmark Researcher | Monthly Updates | Time Spent, Sources Checked, Metrics Updated, Quality Score |