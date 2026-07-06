import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


RNG = random.Random(42)
BASE_TIME = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)

TOOLS = {
    "order_lookup",
    "shipment_tracking",
    "refund_policy_search",
    "refund_create",
    "product_catalog",
    "account_lookup",
    "password_reset",
    "knowledge_base_search",
    "escalation_service",
}

ALLOWED_EVAL_OUTCOMES = {
    "correct_resolution": {"resolved"},
    "missing_tool_call": {"failed", "escalated"},
    "hallucinated_response": {"failed", "escalated"},
    "wrong_policy_retrieval": {"failed", "escalated"},
    "unnecessary_escalation": {"escalated"},
    "retry_loop": {"failed"},
    "timeout": {"failed"},
    "low_confidence": {"awaiting_customer", "awaiting_human"},
    "successful_with_human_review": {"resolved"},
    "incorrect_refund_decision": {"failed", "escalated"},
}

CUSTOMER_TIERS = ["standard", "silver", "gold", "platinum", "enterprise"]
REGIONS = ["US", "CA", "UK", "EU", "IN", "AU", "SG"]

PRODUCTS = [
    "TrailMax running shoes",
    "AeroBrew coffee maker",
    "LumaGlow desk lamp",
    "NestFold storage bins",
    "SoundPeak earbuds",
    "FrostLite water bottle",
    "CloudRest pillow",
    "FlexGrip phone case",
]

CASE_TYPES = [
    "refund_request",
    "shipping_status",
    "order_cancellation",
    "account_login",
    "damaged_item",
    "product_information",
    "payment_issue",
    "exchange_request",
]

ALLOWED_EDGE_CASE_TYPES = {
    "incorrect_refund_decision": {"refund_request", "damaged_item", "exchange_request"},
    "hallucinated_response": {"product_information", "damaged_item"},
    "low_confidence": {"shipping_status", "account_login", "payment_issue"},
    "successful_with_human_review": {"refund_request", "damaged_item"},
    "timeout": set(CASE_TYPES),
}

EDGE_EVALS = [
    "hallucinated_response",
    "timeout",
    "low_confidence",
    "successful_with_human_review",
    "incorrect_refund_decision",
]


def money(low: float, high: float) -> str:
    return f"${RNG.uniform(low, high):.2f}"


def order_id(run_num: int) -> str:
    return f"ORD-{900000 + run_num}"


def tracking_id(run_num: int) -> str:
    return f"TRK-{700000 + run_num}"


def timestamp_for(run_num: int) -> str:
    offset = timedelta(minutes=RNG.randint(0, 43200), seconds=RNG.randint(0, 59))
    return (BASE_TIME + offset).isoformat().replace("+00:00", "Z")


def latency_ms(low: int, high: int) -> int:
    return RNG.randint(low, high)


def step(step_num: int, action: str, tool: str, result: str, latency: int, agent: str = "support_agent") -> dict:
    if tool not in TOOLS:
        raise ValueError(f"Unknown tool: {tool}")
    return {
        "step": step_num,
        "agent": agent,
        "action": action,
        "tool": tool,
        "result": result,
        "latency_ms": latency,
    }


def totals(steps: list[dict], retry_count: int, eval_result: str) -> tuple[float, float, int, int]:
    latency_seconds = round((sum(s["latency_ms"] for s in steps) / 1000) + RNG.uniform(0.4, 3.2), 2)
    token_input = RNG.randint(520, 1800) + 90 * len(steps) + retry_count * RNG.randint(80, 180)
    token_output = RNG.randint(140, 620) + 35 * len(steps)
    penalty = 1.45 if eval_result in {"retry_loop", "timeout"} else 1.0
    cost_usd = round(((token_input * 0.00000045) + (token_output * 0.0000011)) * penalty, 4)
    return latency_seconds, cost_usd, token_input, token_output


def base_trace(run_num: int, case_type: str) -> dict:
    return {
        "run_id": f"run_{run_num:06d}",
        "timestamp": timestamp_for(run_num),
        "customer_tier": RNG.choice(CUSTOMER_TIERS),
        "region": RNG.choice(REGIONS),
        "case_type": case_type,
    }


def finish(trace: dict, user_message: str, steps: list[dict], retry_count: int, human_review: bool,
           final_response: str, outcome: str, eval_result: str) -> dict:
    latency_seconds, cost_usd, token_input, token_output = totals(steps, retry_count, eval_result)
    trace.update(
        {
            "user_message": user_message,
            "agent_steps": steps,
            "tools_used": list(dict.fromkeys(s["tool"] for s in steps)),
            "retry_count": retry_count,
            "human_review": human_review,
            "final_response": final_response,
            "outcome": outcome,
            "eval_result": eval_result,
            "latency_seconds": latency_seconds,
            "cost_usd": cost_usd,
            "token_input": token_input,
            "token_output": token_output,
        }
    )
    return trace


def refund_unnecessary_escalation(run_num: int) -> dict:
    trace = base_trace(run_num, "refund_request")
    oid = order_id(run_num)
    product = RNG.choice(PRODUCTS)
    days = RNG.randint(3, 18)
    user_message = RNG.choice(
        [
            f"I need a refund for {product} on order {oid}. It arrived {days} days ago and is unused.",
            f"Can you refund my order {oid}? The {product} is still sealed and inside the return window.",
            f"Please help me return {product} from {oid}; I checked and it should qualify.",
        ]
    )
    steps = [
        step(1, "Look up order details", "order_lookup", f"Order {oid} delivered {days} days ago; item is refundable.", latency_ms(220, 700)),
        step(2, "Search refund eligibility policy", "refund_policy_search", "Policy: sealed items are refundable within 30 days.", latency_ms(180, 620)),
        step(3, "Escalate refund decision", "escalation_service", "Human queue ticket created despite policy match.", latency_ms(360, 1100)),
    ]
    final_response = RNG.choice(
        [
            "Your order appears to need a specialist review, so I have escalated the refund request.",
            "I have sent this refund case to our human support team for review.",
            "A support specialist will review this refund request and follow up shortly.",
        ]
    )
    return finish(trace, user_message, steps, 0, True, final_response, "escalated", "unnecessary_escalation")


def shipping_missing_tracking(run_num: int) -> dict:
    trace = base_trace(run_num, "shipping_status")
    oid = order_id(run_num)
    guessed_days = RNG.randint(2, 5)
    user_message = RNG.choice(
        [
            f"Where is my order {oid}? I have not seen a tracking update.",
            f"Can you check when {oid} will arrive?",
            f"My package for order {oid} seems late. What is the delivery date?",
        ]
    )
    steps = [
        step(1, "Look up order summary", "order_lookup", f"Order {oid} is marked shipped; tracking id available.", latency_ms(180, 550)),
        step(2, "Search delivery FAQ", "knowledge_base_search", "Standard delivery usually takes 3-5 business days.", latency_ms(150, 480)),
    ]
    final_response = RNG.choice(
        [
            f"Your package should arrive in about {guessed_days} business days based on standard delivery timing.",
            f"It looks like delivery is likely within {guessed_days} days.",
            f"The order is on its way and should arrive around {guessed_days} business days from now.",
        ]
    )
    return finish(trace, user_message, steps, 0, False, final_response, "failed", "missing_tool_call")


def account_retry_loop(run_num: int) -> dict:
    trace = base_trace(run_num, "account_login")
    retries = RNG.randint(4, 6)
    email = f"customer{run_num}@example.com"
    user_message = RNG.choice(
        [
            f"I cannot log in to my account for {email}; the reset link keeps failing.",
            f"My login is locked and password reset is not working for {email}.",
            f"I have tried resetting my password for {email}, but I still cannot get in.",
        ]
    )
    steps = [
        step(1, "Look up account status", "account_lookup", "Account exists; login lock present after repeated attempts.", latency_ms(200, 650)),
    ]
    for idx in range(retries):
        steps.append(
            step(
                idx + 2,
                "Send password reset",
                "password_reset",
                f"Reset email attempt {idx + 1} sent; customer reports link still fails.",
                latency_ms(250, 900),
            )
        )
    final_response = RNG.choice(
        [
            "I sent another password reset email, but the account could not be recovered in this session.",
            "I tried resetting the password again, but the login issue is still unresolved.",
            "The reset process was retried several times and did not restore access.",
        ]
    )
    return finish(trace, user_message, steps, retries, False, final_response, "failed", "retry_loop")


def wrong_refund_policy(run_num: int) -> dict:
    trace = base_trace(run_num, RNG.choice(["refund_request", "damaged_item", "exchange_request"]))
    oid = order_id(run_num)
    product = RNG.choice(PRODUCTS)
    user_message = RNG.choice(
        [
            f"The {product} from {oid} arrived damaged. Can I get a refund?",
            f"I want to exchange or refund {product} on order {oid}; the box was crushed.",
            f"My item from {oid} is defective. What are my refund options?",
        ]
    )
    steps = [
        step(1, "Look up order and item status", "order_lookup", f"Order {oid} delivered recently; damage reported by customer.", latency_ms(200, 620)),
        step(2, "Search refund policy", "refund_policy_search", "Retrieved final-sale policy instead of damaged-item policy.", latency_ms(190, 600)),
    ]
    final_response = RNG.choice(
        [
            "This item is final sale, so I cannot offer a refund.",
            "Based on the policy I found, the purchase is not eligible for refund or exchange.",
            "I am sorry, this order does not qualify for a refund under the policy.",
        ]
    )
    return finish(trace, user_message, steps, 0, False, final_response, "failed", "wrong_policy_retrieval")


def successful_execution(run_num: int) -> dict:
    case_type = RNG.choice(CASE_TYPES)
    trace = base_trace(run_num, case_type)
    oid = order_id(run_num)
    tid = tracking_id(run_num)
    product = RNG.choice(PRODUCTS)

    if case_type == "shipping_status":
        user_message = f"Can you tell me where my order {oid} is right now?"
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} shipped with tracking {tid}.", latency_ms(160, 520)),
            step(2, "Check tracking status", "shipment_tracking", f"{tid}: in transit; estimated delivery tomorrow.", latency_ms(260, 820)),
        ]
        final_response = "Your order is in transit and is estimated to arrive tomorrow."
    elif case_type == "refund_request":
        user_message = f"I want to refund {product} from order {oid}."
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} delivered 9 days ago.", latency_ms(170, 540)),
            step(2, "Check refund policy", "refund_policy_search", "Item is eligible for refund within 30 days.", latency_ms(180, 560)),
            step(3, "Create refund", "refund_create", f"Refund created for {money(18, 140)}.", latency_ms(340, 980)),
        ]
        final_response = "Your refund has been created. The amount should return to your original payment method soon."
    elif case_type == "order_cancellation":
        user_message = f"Please cancel order {oid} if it has not shipped yet."
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} is processing and not shipped.", latency_ms(160, 520)),
            step(2, "Search cancellation policy", "knowledge_base_search", "Orders can be cancelled before shipment.", latency_ms(160, 510)),
        ]
        final_response = "The order is still processing, so it can be cancelled. I have confirmed the cancellation path for you."
    elif case_type == "account_login":
        user_message = f"I cannot sign in to my account. Can you help?"
        steps = [
            step(1, "Look up account", "account_lookup", "Account is active; no security hold present.", latency_ms(180, 520)),
            step(2, "Send password reset", "password_reset", "Password reset email sent successfully.", latency_ms(230, 720)),
        ]
        final_response = "I sent a password reset link to the email on your account."
    elif case_type == "product_information":
        user_message = f"Does the {product} come with a warranty?"
        steps = [
            step(1, "Search product catalog", "product_catalog", f"{product}: one-year limited warranty included.", latency_ms(150, 460)),
            step(2, "Search help center", "knowledge_base_search", "Warranty covers manufacturing defects.", latency_ms(160, 480)),
        ]
        final_response = "Yes. This product includes a one-year limited warranty for manufacturing defects."
    elif case_type == "payment_issue":
        user_message = f"My payment for order {oid} was charged twice. Can you check?"
        steps = [
            step(1, "Look up order payment", "order_lookup", f"Order {oid}: one successful charge and one pending authorization.", latency_ms(180, 560)),
            step(2, "Search payment policy", "knowledge_base_search", "Pending authorizations usually drop within 3-5 business days.", latency_ms(150, 480)),
        ]
        final_response = "I found one completed charge and one pending authorization, which should drop off automatically."
    elif case_type == "exchange_request":
        user_message = f"I need to exchange {product} for a different size."
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} delivered 6 days ago.", latency_ms(170, 540)),
            step(2, "Check exchange policy", "refund_policy_search", "Exchange allowed within 30 days for unused items.", latency_ms(180, 560)),
        ]
        final_response = "Your item is within the exchange window. You can exchange it for another size."
    else:
        user_message = f"The {product} in order {oid} arrived damaged."
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} delivered 2 days ago.", latency_ms(170, 520)),
            step(2, "Search damaged-item policy", "refund_policy_search", "Damaged items are eligible for replacement or refund.", latency_ms(180, 580)),
            step(3, "Create refund", "refund_create", f"Refund created for {money(12, 180)}.", latency_ms(350, 1000)),
        ]
        final_response = "I confirmed the damage policy and created a refund for the item."

    return finish(trace, user_message, steps, 0, False, final_response, "resolved", "correct_resolution")


def edge_case(run_num: int) -> dict:
    eval_result = RNG.choice(EDGE_EVALS)
    if eval_result == "incorrect_refund_decision":
        case_type = RNG.choice(["refund_request", "damaged_item", "exchange_request"])
    elif eval_result == "hallucinated_response":
        case_type = RNG.choice(["product_information", "damaged_item"])
    elif eval_result == "low_confidence":
        case_type = RNG.choice(["shipping_status", "account_login", "payment_issue"])
    elif eval_result == "successful_with_human_review":
        case_type = RNG.choice(["refund_request", "damaged_item"])
    else:
        case_type = RNG.choice(CASE_TYPES)

    trace = base_trace(run_num, case_type)
    oid = order_id(run_num)
    product = RNG.choice(PRODUCTS)

    if eval_result == "timeout":
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} lookup returned slowly.", latency_ms(1800, 4200)),
            step(2, "Search knowledge base", "knowledge_base_search", "Search timed out before final answer.", latency_ms(3500, 9000)),
        ]
        return finish(
            trace,
            f"I need help with order {oid}; the chat keeps hanging.",
            steps,
            RNG.randint(1, 2),
            False,
            "I am sorry, I could not complete the request before the session timed out.",
            "failed",
            "timeout",
        )

    if eval_result == "successful_with_human_review":
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} has a high-value item.", latency_ms(220, 680)),
            step(2, "Search policy", "refund_policy_search", "High-value refund requires review.", latency_ms(180, 590)),
            step(3, "Escalate for approval", "escalation_service", "Human reviewer approved the action.", latency_ms(500, 1600)),
        ]
        return finish(
            trace,
            f"I need a refund for a high-value {product} on {oid}.",
            steps,
            0,
            True,
            "A human reviewer approved the request, and the refund has been completed.",
            "resolved",
            "successful_with_human_review",
        )

    if eval_result == "incorrect_refund_decision":
        steps = [
            step(1, "Look up order", "order_lookup", f"Order {oid} delivered 74 days ago.", latency_ms(180, 540)),
            step(2, "Create refund", "refund_create", f"Refund incorrectly created for {money(20, 160)}.", latency_ms(330, 900)),
        ]
        return finish(
            trace,
            f"Can I get a refund for {product} from {oid}? I bought it a while ago.",
            steps,
            0,
            False,
            "I created the refund for your item.",
            "failed",
            "incorrect_refund_decision",
        )

    if eval_result == "hallucinated_response":
        steps = [
            step(1, "Search product catalog", "product_catalog", f"{product}: no expedited replacement details found.", latency_ms(160, 520)),
        ]
        return finish(
            trace,
            f"Does {product} include same-day replacement coverage?",
            steps,
            0,
            False,
            "Yes, this product includes free same-day replacement coverage in all regions.",
            "failed",
            "hallucinated_response",
        )

    steps = [
        step(1, "Look up account", "account_lookup", "Account has several historical addresses.", latency_ms(180, 580)),
        step(2, "Search help article", "knowledge_base_search", "Found two possible explanations with conflicting guidance.", latency_ms(170, 560)),
    ]
    return finish(
        trace,
        f"I am not sure which address is attached to order {oid}. Can you check?",
        steps,
        RNG.randint(0, 1),
        False,
        "I found conflicting account details and cannot confidently confirm the address.",
        "awaiting_customer",
        "low_confidence",
    )


def build_dataset() -> list[dict]:
    plan = (
        ["refund_unnecessary_escalation"] * 120
        + ["shipping_missing_tracking"] * 80
        + ["account_retry_loop"] * 60
        + ["wrong_refund_policy"] * 50
        + ["successful_execution"] * 150
        + ["edge_case"] * 40
    )
    RNG.shuffle(plan)

    factories = {
        "refund_unnecessary_escalation": refund_unnecessary_escalation,
        "shipping_missing_tracking": shipping_missing_tracking,
        "account_retry_loop": account_retry_loop,
        "wrong_refund_policy": wrong_refund_policy,
        "successful_execution": successful_execution,
        "edge_case": edge_case,
    }
    return [factories[name](run_num) for run_num, name in enumerate(plan, start=1)]


def validate(traces: list[dict]) -> dict:
    if len(traces) != 500:
        raise ValueError(f"Expected 500 traces, got {len(traces)}")

    required = {
        "run_id",
        "timestamp",
        "customer_tier",
        "region",
        "case_type",
        "user_message",
        "agent_steps",
        "tools_used",
        "retry_count",
        "human_review",
        "final_response",
        "outcome",
        "eval_result",
        "latency_seconds",
        "cost_usd",
        "token_input",
        "token_output",
    }

    for trace in traces:
        missing = required - set(trace)
        if missing:
            raise ValueError(f"{trace.get('run_id')} missing fields: {sorted(missing)}")
        used = set(trace["tools_used"])
        if not used <= TOOLS:
            raise ValueError(f"{trace['run_id']} has invalid tools: {sorted(used - TOOLS)}")
        if trace["case_type"] == "shipping_status" and trace["eval_result"] == "missing_tool_call":
            if "shipment_tracking" in used:
                raise ValueError(f"{trace['run_id']} should not use shipment_tracking")
        if trace["eval_result"] == "retry_loop" and trace["retry_count"] <= 3:
            raise ValueError(f"{trace['run_id']} retry_loop needs retry_count > 3")
        allowed_outcomes = ALLOWED_EVAL_OUTCOMES.get(trace["eval_result"])
        if allowed_outcomes is None:
            raise ValueError(f"{trace['run_id']} has unknown eval_result: {trace['eval_result']}")
        if trace["outcome"] not in allowed_outcomes:
            raise ValueError(
                f"{trace['run_id']} has inconsistent outcome "
                f"{trace['outcome']} for eval_result {trace['eval_result']}"
            )
        allowed_case_types = ALLOWED_EDGE_CASE_TYPES.get(trace["eval_result"])
        if allowed_case_types and trace["case_type"] not in allowed_case_types:
            raise ValueError(
                f"{trace['run_id']} has inconsistent case_type "
                f"{trace['case_type']} for eval_result {trace['eval_result']}"
            )

    return {
        "total": len(traces),
        "case_type_counts": dict(Counter(t["case_type"] for t in traces)),
        "eval_result_counts": dict(Counter(t["eval_result"] for t in traces)),
        "outcome_counts": dict(Counter(t["outcome"] for t in traces)),
    }


def main() -> None:
    traces = build_dataset()
    summary = validate(traces)

    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "execution_traces.json"
    output_path.write_text(json.dumps(traces, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
