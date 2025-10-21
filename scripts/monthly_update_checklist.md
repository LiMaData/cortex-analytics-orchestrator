# Monthly Benchmark Update Checklist

## Step 1: Research (30 mins)
- [ ] Check Mailchimp benchmarks: https://mailchimp.com/resources/email-marketing-benchmarks/
- [ ] Check Campaign Monitor: https://www.campaignmonitor.com/resources/guides/
- [ ] Check Litmus: https://www.litmus.com/blog/
- [ ] Check HubSpot: https://blog.hubspot.com/marketing/email-marketing-stats

## Step 2: Update Script (5 mins)
- [ ] Open `scripts/update_benchmarks.py`
- [ ] Update BENCHMARK_UPDATES dictionary with new values
- [ ] Update source URLs

## Step 3: Run Update (2 mins)
```bash
python scripts/update_benchmarks.py
```

## Step 4: Verify (2 mins)
```bash
python tests/test_benchmark_agent.py
```

## Total Time: ~40 minutes monthly