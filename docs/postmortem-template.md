# Post-Mortem: [Incident Title]

**Date:** YYYY-MM-DD
**Duration:** HH:MM — HH:MM UTC (X hours Y minutes)
**Severity:** P1 / P2
**Status:** Resolved
**Author:** @name

---

## Summary

One paragraph describing what happened, the impact, and how it was resolved.

## Impact

| Metric | Value |
|--------|-------|
| Users affected | ~N |
| Error rate | X% |
| Latency p99 | Xms |
| Revenue impact | $N (estimated) |

## Timeline

| Time (UTC) | Event |
|------------|-------|
| HH:MM | Alert fired |
| HH:MM | On-call acknowledged |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Service restored |
| HH:MM | Post-mortem opened |

## Root Cause

Detailed technical explanation of what caused the incident.

## Contributing Factors

- Factor 1
- Factor 2

## Resolution

What was done to restore service.

## Lessons Learned

### What went well

- Monitoring caught the issue within X minutes
- Runbook was clear and effective

### What went wrong

- Alert threshold was too high
- Lack of runbook for this failure mode

### Where we got lucky

- Low traffic period reduced blast radius

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Lower alert threshold | @sre-team | YYYY-MM-DD | Open |
| Write runbook for X | @service-owner | YYYY-MM-DD | Open |
| Add integration test for Y | @dev-team | YYYY-MM-DD | Open |
