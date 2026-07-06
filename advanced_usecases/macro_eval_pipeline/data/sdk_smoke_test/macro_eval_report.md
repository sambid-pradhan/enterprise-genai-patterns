# Macro Evaluation Report

## Overview

- Runs analyzed: 1
- Summaries generated: 1
- Clusters found: 1
- Resolved outcome rate: 0.0%

## Evaluation Result Distribution

- missing_tool_call: 1

## Highest Impact Cluster

- Cluster: Incomplete Delivery Date Resolution
- Occurrences: 1
- Estimated cost signal: $1.25
- Recommendation: Modify agent workflow to automatically invoke a tracking tool (e.g., carrier API) when a tracking ID is available, and return the actual delivery date instead of a generic estimate.

## Clusters

### Cluster 0: Incomplete Delivery Date Resolution

- Occurrences: 1
- Dominant eval labels: missing_tool_call (1)
- Dominant case types: shipping_status (1)
- Estimated cost signal: $1.25

Root cause: Agent failed to use a tracking tool to retrieve the precise delivery date after obtaining a tracking ID, relying instead on a generic estimate from knowledge base.

Business impact: User request for specific delivery date was not fully addressed, leading to a failed outcome and potential customer dissatisfaction.

Suggested fix: Modify agent workflow to automatically invoke a tracking tool (e.g., carrier API) when a tracking ID is available, and return the actual delivery date instead of a generic estimate.

Representative runs:
- run_000001: The user asked for a specific delivery date for order ORD-900001. The agent used order_lookup to confirm the order was shipped and found a tracking ID, then used knowledge_base_search for general delivery timelines. Instead of using a tracking tool to get the precise date, it gave a generic estimate of 4 business days. This missed step led to an incomplete response, resulting in a failed outcome. The response did not fully address the user's request for the actual delivery date.
