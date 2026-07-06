# Macro Evaluation Report

## Overview

- Runs analyzed: 3
- Summaries generated: 3
- Clusters found: 2
- Resolved outcome rate: 33.3%

## Evaluation Result Distribution

- missing_tool_call: 1
- correct_resolution: 1
- unnecessary_escalation: 1

## Highest Impact Cluster

- Cluster: Unnecessary Escalation or Incomplete Action
- Occurrences: 2
- Estimated cost signal: $2.50
- Recommendation: Implement a mandatory tool-use check before escalation or response generation, and enforce a policy that if all eligibility criteria are met, the agent must execute the final action (e.g., tracking lookup or refund processing) without deferring to a human.

## Clusters

### Cluster 1: Unnecessary Escalation or Incomplete Action

- Occurrences: 2
- Dominant eval labels: missing_tool_call (1), unnecessary_escalation (1)
- Dominant case types: shipping_status (1), refund_request (1)
- Estimated cost signal: $2.50

Root cause: The agent fails to complete the final actionable step after gathering sufficient information, either by not using a required tool or by unnecessarily escalating to a human.

Business impact: Customer dissatisfaction due to delayed resolution, increased operational costs from human intervention, and reduced trust in automated support.

Suggested fix: Implement a mandatory tool-use check before escalation or response generation, and enforce a policy that if all eligibility criteria are met, the agent must execute the final action (e.g., tracking lookup or refund processing) without deferring to a human.

Representative runs:
- run_000001: A user from an enterprise EU account inquired about a late package for order ORD-900001, seeking the actual delivery date. The agent correctly looked up the order (retrieving a tracking ID) and consulted the delivery FAQ, but failed to use the tracking ID to fetch the specific delivery date. Instead of calling a tracking tool, it provided a generic estimate of "4 business days from now." This decision led to an incomplete answer, missing the user's primary intent, and the trace was flagged for a missing tool call, resulting in a failed outcome.
- run_000003: A Gold-tier customer requested a refund for sealed earbuds within the 30-day return window. The agent used order lookup and policy search tools, confirming the order was eligible for a straightforward refund. Despite matching the policy, the agent escalated the decision to a human queue instead of processing the refund automatically. This unnecessary escalation resulted in a delayed response, telling the customer a specialist would follow up. The final outcome was an escalated ticket rather than an immediate refund.

### Cluster 0: Password Reset for Login Issues

- Occurrences: 1
- Dominant eval labels: correct_resolution (1)
- Dominant case types: account_login (1)
- Estimated cost signal: $0.25

Root cause: Platinum-tier US customer unable to sign in, likely due to forgotten password or credential issue, with no account lock or security hold detected.

Business impact: High-value customer experienced login disruption, potentially leading to frustration and churn risk for a key account segment.

Suggested fix: Implement proactive password expiration reminders or self-service password reset options to reduce support tickets and improve user experience.

Representative runs:
- run_000002: A platinum-tier US customer reported being unable to sign in. The agent first verified the account was active with no security hold, then immediately sent a password reset email. No errors or retries occurred, and the issue was resolved via the password reset.
