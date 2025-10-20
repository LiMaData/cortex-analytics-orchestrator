# Usage Guide

## Quick Start
```bash
# Run interactive mode
python main.py
```

## Example Queries

### Aggregations
```
What was the total number of emails sent?
How many emails were delivered?
```

### By Dimension
```
Show me open rates by market
What are sends by country?
```

### With Visualization
```
show me open rates by market
chart click rates by country
```

### Time-Based
```
What were sends last month?
Show me open rates this week
```

## Advanced Usage

### Python API
```python
from orchestrators.conversational import ConversationalOrchestrator

orchestrator = ConversationalOrchestrator()
result = orchestrator.process_query("What are total sends?")

if result['success']:
    print(result['data'])
```