"""VS Code friendly runner for local MetaGPT smoke runs."""

from __future__ import annotations

import argparse

from metagpt.software_company import generate_repo


DEFAULT_IDEA = "Create a simple Python command line calculator"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small MetaGPT demo project.")
    parser.add_argument("idea", nargs="*", help="Project idea to pass to MetaGPT.")
    parser.add_argument("--investment", type=float, default=3.0, help="Budget for the AI company.")
    parser.add_argument("--n-round", type=int, default=1, help="Number of MetaGPT rounds to run.")
    parser.add_argument("--project-name", default="metagpt_dev_demo", help="Workspace project name.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    idea = " ".join(args.idea) or DEFAULT_IDEA
    project_path = generate_repo(
        idea=idea,
        investment=args.investment,
        n_round=args.n_round,
        project_name=args.project_name,
    )
    if project_path:
        print(f"Project generated at: {project_path}")


if __name__ == "__main__":
    main()
