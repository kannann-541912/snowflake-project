"""
Cortex Agent Evaluation Runner

Evaluates the TPCH_ANALYST Cortex Agent against ground truth Q&A pairs
using SNOWFLAKE.CORTEX.AI_JUDGE for LLM-as-judge scoring.

Usage:
    python agent/evals/run_evals.py
    python agent/evals/run_evals.py --config agent/evals/eval_config.yaml
    python agent/evals/run_evals.py --question-id GT-001      # Run single question
    python agent/evals/run_evals.py --category ranking         # Run by category
    python agent/evals/run_evals.py --dry-run                  # Validate config only
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CONFIG = PROJECT_ROOT / "agent" / "evals" / "eval_config.yaml"


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_ground_truth(config: dict) -> list[dict]:
    gt_path = PROJECT_ROOT / config["ground_truth_file"]
    with open(gt_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Snowflake connection helpers
# ---------------------------------------------------------------------------

def get_snowflake_connection(config: dict):
    """
    Return a Snowflake Python connector connection.
    Auth priority:
      1. SNOWFLAKE_PAT env var  → PROGRAMMATIC_ACCESS_TOKEN
      2. connection_name in config (uses ~/.snowflake/config.toml profile)
    """
    try:
        import snowflake.connector
    except ImportError:
        print("ERROR: snowflake-connector-python is required. Run: pip install snowflake-connector-python")
        sys.exit(1)

    conn_cfg = config["connection"]
    pat = os.environ.get("SNOWFLAKE_PAT")

    if pat:
        conn = snowflake.connector.connect(
            account=conn_cfg.get("account", os.environ.get("SNOWFLAKE_ACCOUNT", "")),
            user=conn_cfg.get("user", os.environ.get("SNOWFLAKE_USER", "")),
            authenticator="programmatic_access_token",
            token=pat,
            database=conn_cfg["database"],
            schema=conn_cfg["schema"],
            warehouse=conn_cfg["warehouse"],
        )
    else:
        # Fall back to named connection profile in config.toml
        conn = snowflake.connector.connect(
            connection_name=conn_cfg.get("profile", "default"),
            database=conn_cfg["database"],
            schema=conn_cfg["schema"],
            warehouse=conn_cfg["warehouse"],
        )
    return conn


# ---------------------------------------------------------------------------
# Agent invocation
# ---------------------------------------------------------------------------

def invoke_agent(conn, agent_fqn: str, question: str) -> dict:
    """
    Call the Cortex Agent REST API via SQL and return the response payload.
    Uses the SNOWFLAKE.CORTEX.COMPLETE_AGENT scalar function (preview).
    """
    escaped = question.replace("'", "''")
    sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE_AGENT(
            '{agent_fqn}',
            PARSE_JSON('[{{"role": "user", "content": "{escaped}"}}]')
        ) AS response
    """
    cursor = conn.cursor()
    cursor.execute(sql)
    row = cursor.fetchone()
    if not row:
        return {"error": "No response from agent"}
    raw = row[0]
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


# ---------------------------------------------------------------------------
# LLM-as-judge scoring via SNOWFLAKE.CORTEX.AI_JUDGE
# ---------------------------------------------------------------------------

def judge_response(conn, config: dict, question: str, agent_response: str, expected_behavior: str) -> dict:
    """
    Score the agent's response using SNOWFLAKE.CORTEX.AI_JUDGE.
    Returns a dict of {criterion_name: score}.
    """
    judge_model = config["judge"]["model"]
    criteria = config["judge"]["criteria"]
    scores = {}

    for criterion in criteria:
        name = criterion["name"]
        description = criterion["description"]

        # Build a structured judge prompt
        judge_prompt = f"""
You are evaluating an AI assistant's response.

Question: {question}
Expected behavior: {expected_behavior}
Agent response: {agent_response}

Criterion: {name}
Description: {description}

Score the response on this criterion from 0.0 (completely fails) to 1.0 (fully meets criterion).
Return ONLY a JSON object: {{"score": <float>, "reason": "<one sentence>"}}
        """.strip().replace("'", "''")

        sql = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                '{judge_model}',
                '{judge_prompt}'
            ) AS judge_output
        """
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        if not row:
            scores[name] = {"score": 0.0, "reason": "No judge response"}
            continue

        try:
            output = json.loads(row[0])
            scores[name] = output
        except (json.JSONDecodeError, TypeError):
            scores[name] = {"score": 0.0, "reason": "Failed to parse judge output"}

    return scores


# ---------------------------------------------------------------------------
# Scoring + pass/fail
# ---------------------------------------------------------------------------

def compute_weighted_score(judge_scores: dict, criteria_config: list[dict]) -> float:
    total_weight = sum(c["weight"] for c in criteria_config)
    weighted_sum = 0.0
    for criterion in criteria_config:
        name = criterion["name"]
        weight = criterion["weight"]
        score = judge_scores.get(name, {}).get("score", 0.0)
        weighted_sum += score * weight
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def evaluate_tool_call(agent_response: dict, expected_tool: str | None) -> bool:
    """Check if the agent called the expected tool (or correctly called no tool)."""
    tool_calls = agent_response.get("tool_calls", [])
    if expected_tool is None:
        return len(tool_calls) == 0
    called_tools = [tc.get("name") for tc in tool_calls]
    return expected_tool in called_tools


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------

def save_results_local(results: list[dict], output_dir: Path, run_id: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"eval_run_{run_id}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")


def save_results_snowflake(conn, config: dict, results: list[dict], run_id: str):
    """Persist eval results to SANDBOX.TPCH.AGENT_EVAL_RESULTS."""
    table = config["results"]["table"]

    # Ensure the table exists
    conn.cursor().execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            RUN_ID          VARCHAR NOT NULL,
            EVAL_TIMESTAMP  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            QUESTION_ID     VARCHAR,
            CATEGORY        VARCHAR,
            QUESTION        VARCHAR,
            OVERALL_SCORE   FLOAT,
            TOOL_CORRECT    BOOLEAN,
            PASSED          BOOLEAN,
            JUDGE_SCORES    VARIANT,
            AGENT_RESPONSE  VARIANT
        )
    """)

    for r in results:
        conn.cursor().execute(
            f"""
            INSERT INTO {table}
                (RUN_ID, QUESTION_ID, CATEGORY, QUESTION,
                 OVERALL_SCORE, TOOL_CORRECT, PASSED, JUDGE_SCORES, AGENT_RESPONSE)
            VALUES (%s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s), PARSE_JSON(%s))
            """,
            (
                run_id,
                r["question_id"],
                r["category"],
                r["question"],
                r["overall_score"],
                r["tool_correct"],
                r["passed"],
                json.dumps(r["judge_scores"]),
                json.dumps(r.get("agent_response", {})),
            ),
        )
    print(f"Results persisted to {table} (run_id={run_id})")


# ---------------------------------------------------------------------------
# Main eval loop
# ---------------------------------------------------------------------------

def run_evaluation(config: dict, ground_truth: list[dict], dry_run: bool = False) -> int:
    """
    Run the full evaluation suite. Returns exit code (0 = pass, 1 = fail).
    """
    agent_fqn = config["agent"]["fqn"]
    thresholds = config["thresholds"]
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    print(f"\n{'='*60}")
    print(f"  Cortex Agent Evaluation Suite")
    print(f"  Agent:   {agent_fqn}")
    print(f"  Run ID:  {run_id}")
    print(f"  Items:   {len(ground_truth)}")
    if dry_run:
        print("  Mode:    DRY RUN (no Snowflake calls)")
    print(f"{'='*60}\n")

    if dry_run:
        print("Config and ground truth validated. Exiting dry run.")
        return 0

    conn = get_snowflake_connection(config)
    all_results = []

    for item in ground_truth:
        qid = item["id"]
        question = item["question"]
        expected_tool = item.get("expected_tool")
        expected_behavior = item["expected_behavior"]
        category = item.get("category", "general")

        print(f"[{qid}] {question[:70]}...")

        # Invoke the agent
        start = time.time()
        agent_response = invoke_agent(conn, agent_fqn, question)
        elapsed = time.time() - start

        # Extract text response
        response_text = ""
        messages = agent_response.get("messages", [])
        for msg in messages:
            if msg.get("role") == "assistant":
                for block in msg.get("content", []):
                    if isinstance(block, dict) and block.get("type") == "text":
                        response_text += block.get("text", "")
                    elif isinstance(block, str):
                        response_text += block

        # Tool call accuracy
        tool_correct = evaluate_tool_call(agent_response, expected_tool)

        # LLM-as-judge scoring
        judge_scores = judge_response(conn, config, question, response_text, expected_behavior)
        overall_score = compute_weighted_score(judge_scores, config["judge"]["criteria"])

        passed = (
            overall_score >= thresholds["per_question_min_score"]
            and tool_correct
        )

        status_icon = "PASS" if passed else "FAIL"
        print(f"  [{status_icon}] score={overall_score:.2f} tool_correct={tool_correct} elapsed={elapsed:.1f}s")

        all_results.append({
            "question_id": qid,
            "category": category,
            "question": question,
            "overall_score": overall_score,
            "tool_correct": tool_correct,
            "passed": passed,
            "judge_scores": judge_scores,
            "agent_response": agent_response,
        })

    # Suite-level summary
    passed_count = sum(1 for r in all_results if r["passed"])
    avg_score = sum(r["overall_score"] for r in all_results) / len(all_results)
    all_tool_correct = all(r["tool_correct"] for r in all_results)

    suite_passed = (
        avg_score >= thresholds["overall_pass_score"]
        and all_tool_correct
        and passed_count == len(all_results)
    )

    print(f"\n{'='*60}")
    print(f"  SUITE {'PASSED' if suite_passed else 'FAILED'}")
    print(f"  Overall score:    {avg_score:.2f} (threshold: {thresholds['overall_pass_score']})")
    print(f"  Questions passed: {passed_count}/{len(all_results)}")
    print(f"  Tool accuracy:    {'100%' if all_tool_correct else 'FAILED'}")
    print(f"{'='*60}\n")

    # Persist results
    output_dir = PROJECT_ROOT / config["results"]["output_dir"]
    save_results_local(all_results, output_dir, run_id)

    if config["results"].get("write_to_snowflake"):
        save_results_snowflake(conn, config, all_results, run_id)

    conn.close()
    return 0 if suite_passed else 1


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run Cortex Agent evaluation suite")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--question-id", help="Run a single question by ID (e.g. GT-001)")
    parser.add_argument("--category", help="Run only questions matching this category")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without making Snowflake calls")
    args = parser.parse_args()

    config = load_config(args.config)
    ground_truth = load_ground_truth(config)

    # Apply filters
    if args.question_id:
        ground_truth = [q for q in ground_truth if q["id"] == args.question_id]
        if not ground_truth:
            print(f"ERROR: No question found with id '{args.question_id}'")
            sys.exit(1)

    if args.category:
        ground_truth = [q for q in ground_truth if q.get("category") == args.category]
        if not ground_truth:
            print(f"ERROR: No questions found in category '{args.category}'")
            sys.exit(1)

    exit_code = run_evaluation(config, ground_truth, dry_run=args.dry_run)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
