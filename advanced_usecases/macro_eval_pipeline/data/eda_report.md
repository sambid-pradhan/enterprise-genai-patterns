# Execution Traces EDA

## Dataset Overview

| Metric | Value |
| --- | --- |
| Total traces | 500 |
| Unique run IDs | 500 |
| Timestamp range | 2026-06-01T09:15:42Z to 2026-07-01T07:12:37Z |
| Total simulated cost | $0.6587 |
| Total tokens | 1002371 |

## Case Type Distribution

| Case type | Count | Percent |
| --- | --- | --- |
| refund_request | 158 | 31.6% |
| shipping_status | 98 | 19.6% |
| account_login | 79 | 15.8% |
| damaged_item | 54 | 10.8% |
| exchange_request | 44 | 8.8% |
| payment_issue | 27 | 5.4% |
| product_information | 23 | 4.6% |
| order_cancellation | 17 | 3.4% |

## Evaluation Result Distribution

| Eval result | Count | Percent |
| --- | --- | --- |
| correct_resolution | 150 | 30.0% |
| unnecessary_escalation | 120 | 24.0% |
| missing_tool_call | 80 | 16.0% |
| retry_loop | 60 | 12.0% |
| wrong_policy_retrieval | 50 | 10.0% |
| hallucinated_response | 10 | 2.0% |
| timeout | 8 | 1.6% |
| low_confidence | 8 | 1.6% |
| successful_with_human_review | 7 | 1.4% |
| incorrect_refund_decision | 7 | 1.4% |

## Outcome Distribution

| Outcome | Count | Percent |
| --- | --- | --- |
| failed | 215 | 43.0% |
| resolved | 157 | 31.4% |
| escalated | 120 | 24.0% |
| awaiting_customer | 8 | 1.6% |

## Customer And Region Distribution

### Customer Tier

| Tier | Count | Percent |
| --- | --- | --- |
| standard | 107 | 21.4% |
| enterprise | 104 | 20.8% |
| platinum | 97 | 19.4% |
| gold | 96 | 19.2% |
| silver | 96 | 19.2% |

### Region

| Region | Count | Percent |
| --- | --- | --- |
| SG | 85 | 17.0% |
| EU | 79 | 15.8% |
| US | 73 | 14.6% |
| UK | 71 | 14.2% |
| IN | 67 | 13.4% |
| CA | 66 | 13.2% |
| AU | 59 | 11.8% |

## Eval Result By Outcome

| Eval result | Outcome | Count |
| --- | --- | --- |
| correct_resolution | resolved | 150 |
| unnecessary_escalation | escalated | 120 |
| missing_tool_call | failed | 80 |
| retry_loop | failed | 60 |
| wrong_policy_retrieval | failed | 50 |
| hallucinated_response | failed | 10 |
| timeout | failed | 8 |
| low_confidence | awaiting_customer | 8 |
| successful_with_human_review | resolved | 7 |
| incorrect_refund_decision | failed | 7 |

## Tool Usage

| Tool | Traces using tool | Percent of traces |
| --- | --- | --- |
| order_lookup | 387 | 77.4% |
| refund_policy_search | 239 | 47.8% |
| knowledge_base_search | 153 | 30.6% |
| escalation_service | 127 | 25.4% |
| account_lookup | 85 | 17.0% |
| password_reset | 77 | 15.4% |
| refund_create | 44 | 8.8% |
| product_catalog | 28 | 5.6% |
| shipment_tracking | 14 | 2.8% |

### Dominant Tools By Case Type

| Case type | Top tools |
| --- | --- |
| account_login | account_lookup (79), password_reset (77), knowledge_base_search (2) |
| damaged_item | order_lookup (49), refund_policy_search (44), refund_create (22) |
| exchange_request | order_lookup (44), refund_policy_search (39), knowledge_base_search (3) |
| order_cancellation | order_lookup (17), knowledge_base_search (17) |
| payment_issue | knowledge_base_search (27), order_lookup (24), account_lookup (3) |
| product_information | product_catalog (23), knowledge_base_search (18) |
| refund_request | order_lookup (158), refund_policy_search (156), escalation_service (123) |
| shipping_status | order_lookup (95), knowledge_base_search (84), shipment_tracking (14) |

## Numeric Ranges

| Metric | Min | P50 | P75 | P90 | P95 | Max | Mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| latency_seconds | 0.9 | 3.12 | 3.87 | 4.79 | 6.01 | 14.71 | 3.2767 |
| cost_usd | 0.0006 | 0.0012 | 0.0014 | 0.0021 | 0.0025 | 0.0035 | 0.0013 |
| token_input | 663 | 1502 | 1849 | 2046 | 2476 | 3439 | 1520.012 |
| token_output | 197 | 493 | 599 | 667 | 688 | 852 | 484.73 |
| retry_count | 0 | 0 | 0 | 4 | 5 | 6 | 0.642 |
| steps_per_trace | 1 | 2 | 3 | 5 | 6 | 7 | 2.796 |
| tools_per_trace | 1 | 2 | 3 | 3 | 3 | 3 | 2.308 |

## Behavioral Checks

| Check | Result |
| --- | --- |
| Missing tool-call traces without shipment_tracking | 80 |
| Retry-loop min retry_count | 4 |
| Retry-loop max retry_count | 6 |
| Unnecessary escalations with escalation_service | 120 |
| Wrong-policy traces with refund_policy_search | 50 |

## Quality Checks

| Check | Issue count |
| --- | --- |
| Duplicate run IDs | 0 |
| Missing required fields | 0 |
| Invalid tools | 0 |
| Step numbering or negative step latency issues | 0 |
| Eval/outcome consistency issues | 0 |
| Eval/case_type semantic consistency issues | 0 |
| Resolved traces saying human will complete next step | 0 |

## Representative Examples

### unnecessary_escalation - run_000003

| Field | Value |
| --- | --- |
| Case type | refund_request |
| Outcome | escalated |
| Retry count | 0 |
| Tools used | order_lookup, refund_policy_search, escalation_service |
| User message | Can you refund my order ORD-900003? The SoundPeak earbuds is still sealed and inside the return window. |
| Final response | A support specialist will review this refund request and follow up shortly. |

### missing_tool_call - run_000001

| Field | Value |
| --- | --- |
| Case type | shipping_status |
| Outcome | failed |
| Retry count | 0 |
| Tools used | order_lookup, knowledge_base_search |
| User message | My package for order ORD-900001 seems late. What is the delivery date? |
| Final response | The order is on its way and should arrive around 4 business days from now. |

### retry_loop - run_000008

| Field | Value |
| --- | --- |
| Case type | account_login |
| Outcome | failed |
| Retry count | 4 |
| Tools used | account_lookup, password_reset |
| User message | I have tried resetting my password for customer8@example.com, but I still cannot get in. |
| Final response | The reset process was retried several times and did not restore access. |

### wrong_policy_retrieval - run_000023

| Field | Value |
| --- | --- |
| Case type | damaged_item |
| Outcome | failed |
| Retry count | 0 |
| Tools used | order_lookup, refund_policy_search |
| User message | My item from ORD-900023 is defective. What are my refund options? |
| Final response | This item is final sale, so I cannot offer a refund. |

### correct_resolution - run_000002

| Field | Value |
| --- | --- |
| Case type | account_login |
| Outcome | resolved |
| Retry count | 0 |
| Tools used | account_lookup, password_reset |
| User message | I cannot sign in to my account. Can you help? |
| Final response | I sent a password reset link to the email on your account. |

### low_confidence - run_000072

| Field | Value |
| --- | --- |
| Case type | payment_issue |
| Outcome | awaiting_customer |
| Retry count | 0 |
| Tools used | account_lookup, knowledge_base_search |
| User message | I am not sure which address is attached to order ORD-900072. Can you check? |
| Final response | I found conflicting account details and cannot confidently confirm the address. |

## Interpretation

- The dataset has strong, discoverable macro patterns rather than pure randomness. The biggest visible behaviors are unnecessary refund escalations, missing shipment tool calls, password reset retry loops, and wrong refund-policy retrievals.
- The generated labels are now logically cleaner: every major eval_result maps to the expected outcome, and edge-case evals are constrained to relevant case types.
- This is useful for demonstrating clustering, root-cause summaries, dashboard slices, and regression tracking. It is still synthetic, so operational conclusions should be framed as demo insights rather than real customer-support findings.
