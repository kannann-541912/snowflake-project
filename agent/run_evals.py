"""
Shared Cortex Agent Evaluation Runner.

Evaluates any agent in agent/agents/ against its ground-truth Q&A pairs
using SNOWFLAKE.CORTEX.AI_JUDGE for LLM-as-judge scoring.

Usage:
    # Run evals for a specific agent
    python agent/run_evals.py --agent tpch-analyst

    # Pass an explicit config path
    python agent/run_evals.py --config agent/agents/tpch-analyst/evals/eval_config.yaml

    # Run a single question by ID
    python agent/run_evals.py --agent tpch-analyst --question-id GT-001

    # Run questions matching a category
    python agent/run_evals.py --agent tpch-analyst --category ranking

    # Dry-run: validate config + ground truth without calling Snowflake
    python agent/run_evals.py --agent tpch-analyst --dry-run

    # Run evals for ALL agents (used in CI)
    python agent/run_evals.py --all
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR   = PROJECT_ROOT / "agent" / "agents"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_agents() -> list[Path]:
    return sorted(
        p.parent for p in AGENTS_DIR.glob("*/agent.yml")
    )


def resolve_config_path(agent_name: str | None, explicit_config: Path | None) -> Path:
    if explicit_config:
        return explicit_config
    if agent_name:
        path = AGENTS_DIR / agent_name / "evals" / "eval_config.yaml"
        if not path.exists():
            print(f"ERROR: eval_config.yaml not found for agent '{agent_name}' at {path}")
            sys.exit(1)
        return path
    print("ERROR: provide --agent <name>, --config <path>, or --all")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config + ground truth loading
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_ground_truth(config: dict) -> list[dict]:
    gt_path = PROJECT_ROOT / config["ground_truth_file"]
    with open(gt_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Snowflake connection
# ---------------------------------------------------------------------------

def get_snowflake_connection(config: dict):
    try:
        import snowflake.connector
    except ImportError:
        print("ERROR: pip install snowflake-connector-python")
        sys.exit(1)

    conn_cfg = config["connection"]
    account  = conn_cfg.get("account", os.environ.get("SNOWFLAKE_ACCOUNT", ""))
    user     = conn_cfg.get("user",    os.environ.get("SNOWFLAKE_USER", ""))

    # PAT auth (highest priority)
    pat = os.environ.get("SNOWFLAKE_PAT")
    if pat:
        return snowflake.connector.connect(
            account       = account,
            user          = user,
            authenticator = "programmatic_access_token",
            token         = pat,
            database      = conn_cfg["database"],
            schema        = conn_cfg["schema"],
            warehouse     = conn_cfg["warehouse"],
        )

    # Private key / JWT auth — connector requires DER bytes, not a file path
    private_key_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
    if private_key_path:
        from cryptography.hazmat.primitives.serialization import (
            load_pem_private_key, Encoding, PrivateFormat, NoEncryption,
        )
        from cryptography.hazmat.backends import default_backend
        with open(private_key_path, "rb") as f:
            pk_obj = load_pem_private_key(f.read(), password=None, backend=default_backend())
        pk_bytes = pk_obj.private_bytes(
            encoding=Encoding.DER,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        )
        return snowflake.connector.connect(
            account     = account,
            user        = user,
            private_key = pk_bytes,
            database    = conn_cfg["database"],
            schema      = conn_cfg["schema"],
            warehouse   = conn_cfg["warehouse"],
        )

    # Fall back to named connection profile in ~/.snowflake/config.toml
    return snowflake.connector.connect(
        connection_name = conn_cfg.get("profile", "default"),
        database        = conn_cfg["database"],
        schema          = conn_cfg["schema"],
        warehouse       = conn_cfg["warehouse"],
    )


# ---------------------------------------------------------------------------
# Agent invocation + scoring
# ---------------------------------------------------------------------------

def invoke_agent(conn, agent_fqn: str, question: str) -> dict:
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
    return json.loads(raw) if isinstance(raw, str) else raw


def judge_response(conn, config: dict, question: str, agent_response: str, expected_behavior: str) -> dict:
    judge_model = config["judge"]["model"]
    scores = {}
    for criterion in config["judge"]["criteria"]:
        name, description = criterion["name"], criterion["description"]
        prompt = f"""
You are evaluating an AI assistant's response.

Question: {question}
Expected behavior: {expected_behavior}
Agent response: {agent_response}

Criterion: {name}
Description: {description}

Score 0.0–1.0. Return ONLY JSON: {{"score": <float>, "reason": "<one sentence>"}}
        """.strip().replace("'", "''")

        cursor = conn.cursor()
        cursor.execute(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{judge_model}', '{prompt}') AS out")
        row = cursor.fetchone()
        try:
            scores[name] = json.loads(row[0]) if row else {"score": 0.0, "reason": "no response"}
        except (json.JSONDecodeError, TypeError):
            scores[name] = {"score": 0.0, "reason": "parse error"}
    return scores


def compute_weighted_score(judge_scores: dict, criteria_config: list[dict]) -> float:
    total_weight = sum(c["weight"] for c in criteria_config)
    weighted_sum = sum(
        judge_scores.get(c["name"], {}).get("score", 0.0) * c["weight"]
        for c in criteria_config
    )
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def evaluate_tool_call(agent_response: dict, expected_tool: str | None) -> bool:
    tool_calls = agent_response.get("tool_calls", [])
    if expected_tool is None:
        return len(tool_calls) == 0
    return expected_tool in [tc.get("name") for tc in tool_calls]


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------

def save_results_local(results: list[dict], output_dir: Path, run_id: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"eval_run_{run_id}.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {path}")


def save_results_snowflake(conn, config: dict, results: list[dict], run_id: str):
    table = config["results"]["table"]
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
            (run_id, r["question_id"], r["category"], r["question"],
             r["overall_score"], r["tool_correct"], r["passed"],
             json.dumps(r["judge_scores"]), json.dumps(r.get("agent_response", {}))),
        )
    print(f"Results persisted to {table} (run_id={run_id})")


# ---------------------------------------------------------------------------
# Eval loop
# ---------------------------------------------------------------------------

def run_evaluation(config: dict, ground_truth: list[dict], dry_run: bool = False) -> int:
    agent_fqn  = config["agent"]["fqn"]
    thresholds = config["thresholds"]
    run_id     = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    print(f"\n{'='*60}")
    print(f"  Agent Evaluation Suite")
    print(f"  Agent:  {agent_fqn}")
    print(f"  Run ID: {run_id}  |  Items: {len(ground_truth)}")
    if dry_run:
        print("  Mode:   DRY RUN — config + ground truth validated. No Snowflake calls.")
    print(f"{'='*60}\n")

    if dry_run:
        return 0

    conn = get_snowflake_connection(config)
    all_results = []

    for item in ground_truth:
        qid              = item["id"]
        question         = item["question"]
        expected_tool    = item.get("expected_tool")
        expected_behavior = item["expected_behavior"]

        print(f"[{qid}] {question[:70]}...")
        start          = time.time()
        agent_response = invoke_agent(conn, agent_fqn, question)
        elapsed        = time.time() - start

        response_text = "".join(
            block.get("text", "") if isinstance(block, dict) else block
            for msg in agent_response.get("messages", [])
            if msg.get("role") == "assistant"
            for block in msg.get("content", [])
        )

        tool_correct  = evaluate_tool_call(agent_response, expected_tool)
        judge_scores  = judge_response(conn, config, question, response_text, expected_behavior)
        overall_score = compute_weighted_score(judge_scores, config["judge"]["criteria"])
        passed        = overall_score >= thresholds["per_question_min_score"] and tool_correct

        print(f"  [{'PASS' if passed else 'FAIL'}] score={overall_score:.2f} "
              f"tool_correct={tool_correct} elapsed={elapsed:.1f}s")

        all_results.append({
            "question_id": qid, "category": item.get("category", "general"),
            "question": question, "overall_score": overall_score,
            "tool_correct": tool_correct, "passed": passed,
            "judge_scores": judge_scores, "agent_response": agent_response,
        })

    passed_count   = sum(1 for r in all_results if r["passed"])
    avg_score      = sum(r["overall_score"] for r in all_results) / len(all_results)
    all_tool_ok    = all(r["tool_correct"] for r in all_results)
    suite_passed   = (avg_score >= thresholds["overall_pass_score"]
                      and all_tool_ok and passed_count == len(all_results))

    print(f"\n{'='*60}")
    print(f"  SUITE {'PASSED' if suite_passed else 'FAILED'}")
    print(f"  Overall score:    {avg_score:.2f} (threshold: {thresholds['overall_pass_score']})")
    print(f"  Questions passed: {passed_count}/{len(all_results)}")
    print(f"  Tool accuracy:    {'100%' if all_tool_ok else 'FAILED'}")
    print(f"{'='*60}\n")

    output_dir = PROJECT_ROOT / config["results"]["output_dir"]
    save_results_local(all_results, output_dir, run_id)
    if config["results"].get("write_to_snowflake"):
        save_results_snowflake(conn, config, all_results, run_id)

    conn.close()
    return 0 if suite_passed else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Cortex Agent evaluation suite")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--agent",  help="Agent folder name to evaluate (e.g. tpch-analyst)")
    group.add_argument("--all",    action="store_true", help="Run evals for all discovered agents")
    group.add_argument("--config", type=Path, help="Explicit path to eval_config.yaml")
    parser.add_argument("--question-id", help="Run a single question by ID (e.g. GT-001)")
    parser.add_argument("--category",    help="Run only questions in this category")
    parser.add_argument("--dry-run",     action="store_true")
    parser.add_argument("--list",        action="store_true", help="List discovered agents and exit")
    args = parser.parse_args()

    if args.list:
        agents = discover_agents()
        print("Discovered agents:")
        for a in agents:
            print(f"  {a.name}  ({a})")
        return

    agents_to_run: list[Path] = []

    if args.all:
        agents_to_run = discover_agents()
        if not agents_to_run:
            print(f"No agents found in {AGENTS_DIR}.")
            sys.exit(1)
    else:
        config_path = resolve_config_path(args.agent, args.config)
        config      = load_config(config_path)
        ground_truth = load_ground_truth(config)

        if args.question_id:
            ground_truth = [q for q in ground_truth if q["id"] == args.question_id]
            if not ground_truth:
                print(f"ERROR: No question with id '{args.question_id}'")
                sys.exit(1)
        if args.category:
            ground_truth = [q for q in ground_truth if q.get("category") == args.category]
            if not ground_truth:
                print(f"ERROR: No questions in category '{args.category}'")
                sys.exit(1)

        sys.exit(run_evaluation(config, ground_truth, dry_run=args.dry_run))

    # --all path
    failures: list[str] = []
    for agent_dir in agents_to_run:
        config_path  = agent_dir / "evals" / "eval_config.yaml"
        config       = load_config(config_path)
        ground_truth = load_ground_truth(config)
        rc = run_evaluation(config, ground_truth, dry_run=args.dry_run)
        if rc != 0:
            failures.append(agent_dir.name)

    if failures:
        print(f"\nFAILED agents: {', '.join(failures)}")
        sys.exit(1)
    print(f"\nAll {len(agents_to_run)} agent eval suite(s) passed.")


if __name__ == "__main__":
    main()
