import json
from datetime import datetime


def parse(payload: dict) -> list[str]:
    """Convert an Alertmanager webhook payload into text chunks."""
    chunks = []
    common_labels = payload.get("commonLabels", {})
    common_annotations = payload.get("commonAnnotations", {})

    for alert in payload.get("alerts", []):
        labels = {**common_labels, **alert.get("labels", {})}
        annotations = {**common_annotations, **alert.get("annotations", {})}
        status = alert.get("status", payload.get("status", "unknown"))
        starts_at = alert.get("startsAt", "")

        parts = [f"Alert status: {status}"]
        if starts_at:
            parts.append(f"Started: {starts_at}")
        for k, v in labels.items():
            parts.append(f"{k}: {v}")
        for k, v in annotations.items():
            parts.append(f"{k}: {v}")

        chunks.append("\n".join(parts))

    return chunks
