# Monthly Benchmark Update Checklist

## 📅 Schedule: 1st of Each Month

## Step 1: Research Latest Benchmarks (30 mins)

### Sources to Check:
- [ ] **Mailchimp Benchmarks**
  - URL: https://mailchimp.com/resources/email-marketing-benchmarks/
  - Look for: Open rates, click rates by industry
  
- [ ] **Campaign Monitor**
  - URL: https://www.campaignmonitor.com/resources/guides/
  - Look for: Industry averages, best practices
  
- [ ] **Litmus Email Analytics**
  - URL: https://www.litmus.com/blog/
  - Look for: Deliverability, engagement metrics
  
- [ ] **HubSpot Marketing Stats**
  - URL: https://blog.hubspot.com/marketing/email-marketing-stats
  - Look for: Conversion rates, trends

### Record Your Findings:
```
Metric          | Source            | Value | Date
----------------|-------------------|-------|------
Open Rate       | Mailchimp 2024    | 21.5% | Dec 2024
Click Rate      | Campaign Monitor  | 2.6%  | Dec 2024
Bounce Rate     | Litmus           | 0.7%  | Dec 2024
```

## Step 2: Update Script (5 mins)

- [ ] Open `scripts/update_benchmarks.py`
- [ ] Update `LATEST_BENCHMARKS` dictionary with new values
- [ ] Update source names and dates
- [ ] Save file

## Step 3: Run Update (2 mins)
```bash
python scripts/update_benchmarks.py
```

- [ ] Review changes
- [ ] Type 'yes' to confirm
- [ ] Verify success messages

## Step 4: Test (2 mins)
```bash
python tests/test_benchmark_agent.py
```

- [ ] Verify benchmarks load correctly
- [ ] Check dates are current

## Step 5: Document (1 min)

Add entry to `docs/BENCHMARK_HISTORY.md`:
```markdown
## 2024-11-01
- Open Rate: 21.5% (Mailchimp 2024)
- Click Rate: 2.6% (Campaign Monitor 2024)
- Changes: +0.5% open rate vs Oct
```

## Total Time: ~40 minutes

## Next Update: [Auto-calculated in script]