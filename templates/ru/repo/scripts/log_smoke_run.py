{{#if mlflow-tracking}}
"""Log a smoke run to MLflow: what a training run logs, without training.

    uv run python scripts/log_smoke_run.py

The first stage of the end-to-end check of ml-scaffold (framework.md, step 5),
locally or in a remote task through the transport's entry point: opens a run
with {{project.pkg}}.tracking in the store and experiment of mlflow.toml, logs
params and a metric over a few steps, writes a checkpoint into the run's
directory under ${{runs_env}} (a temporary directory if unset) and uploads it
with its sha256 tag. Exit 1 if the run was not created: the store was
unreachable or refused the login (doctor.py says which).
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

import mlflow

from {{project.pkg}} import tracking


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--steps", type=int, default=5)
    ap.add_argument("--checkpoint-kb", type=int, default=64)
    args = ap.parse_args()

    root = os.environ.get("{{runs_env}}") or tempfile.mkdtemp(prefix="{{project.name}}-runs-")
    params = {"steps": args.steps, "checkpoint_kb": args.checkpoint_kb, "kind": "smoke"}
    with tracking.start_run(run_name="smoke", params=params) as run:
        if not run.active:
            print("MLflow run not created", file=sys.stderr)
            return 1
        ckpt_dir = tracking.checkpoint_dir(root, run)
        for step in range(args.steps):
            mlflow.log_metric("loss", 1.0 / (step + 1), step=step)
        ckpt = ckpt_dir / "last.ckpt"
        ckpt.write_bytes(os.urandom(args.checkpoint_kb * 1024))
        tracking.log_checkpoint(ckpt)
        print(f"run {run.run_id}, checkpoint {ckpt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
{{/if}}
