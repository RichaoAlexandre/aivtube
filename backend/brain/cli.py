"""Talk to AGI-chan in the terminal.

    python -m backend.brain.cli

Requires ANTHROPIC_API_KEY (in env or a .env file). Type 'quit' to exit,
'reset' to clear her memory.
"""

from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .brain import Brain


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")
        return 1

    brain = Brain()
    print(f"AGI-chan is live (model={brain.model}). Talk to her. ('quit' / 'reset')\n")

    while True:
        try:
            user = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not user:
            continue
        if user.lower() in {"quit", "exit"}:
            return 0
        if user.lower() == "reset":
            brain.reset()
            print("(memory cleared)\n")
            continue

        # Print each spoken sentence as it streams, with its emotion.
        for chunk in brain.respond(user):
            print(f"AGI-chan [{chunk.emotion}]> {chunk.text}")
        print()


if __name__ == "__main__":
    sys.exit(main())
