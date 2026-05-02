# Runbook: [Alert Name]

**Service:** `service-name`
**Severity:** P1 / P2 / P3
**Owner:** @team-oncall
**Last updated:** YYYY-MM-DD

---

## Summary

Brief description of what this alert means and its impact on users or systems.

## Symptoms

- What the alert fires on (metric, threshold)
- Observable effects (latency spike, errors, service unavailable)

## Diagnosis

### Step 1 — Verify the alert

```bash
kubectl get pods -n <namespace>
kubectl describe pod <pod-name> -n <namespace>
```

### Step 2 — Check recent changes

```bash
# Check recent deployments
kubectl rollout history deployment/<name> -n <namespace>
```

### Step 3 — Inspect logs

```bash
kubectl logs <pod-name> -n <namespace> --since=30m | grep -i error
```

## Resolution

### Option A — Rollback

```bash
kubectl rollout undo deployment/<name> -n <namespace>
```

### Option B — Scale up

```bash
kubectl scale deployment/<name> --replicas=<N> -n <namespace>
```

### Option C — Restart pods

```bash
kubectl rollout restart deployment/<name> -n <namespace>
```

## Escalation

If unresolved after 15 minutes:
1. Page the on-call engineer via PagerDuty
2. Open a war-room channel: `#incident-YYYY-MM-DD`
3. Notify the service owner: @team

## Post-incident

After resolution, open a post-mortem within 48h using the [post-mortem template](postmortem-template.md).
