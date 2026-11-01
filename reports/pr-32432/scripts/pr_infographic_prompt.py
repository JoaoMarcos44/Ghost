"""Prepare reproducible native-image prompts for the three Ghost pull requests."""

import argparse
import json


THEMES = {
    "settings": {
        "name": "Engineering blueprint",
        "direction": "Dark navy drafting paper, cyan and white linework, amber for pending edits. Precise timeline and layered form-state cards; clean technical typography.",
    },
    "labels": {
        "name": "Paper-cut workshop",
        "direction": "Warm ivory, terracotta, moss green and muted mustard. Tactile paper-cut member cards and detachable label tabs, with a single clearly bounded batch tray.",
    },
    "toggle": {
        "name": "Editorial print",
        "direction": "Ivory newsprint, charcoal typography and vermilion accents. Book pages and rich-text blocks move through an HTML-to-Lexical conversion, with readable paragraph and link symbols.",
    },
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--docs", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    title = args.title.lower()
    theme_key = "toggle" if "toggle" in title else "labels" if "label" in title else "settings"
    theme = THEMES[theme_key]
    payload = {
        "title": args.title,
        "summary": args.summary,
        "validation_docs": args.docs,
        "theme": theme,
        "prompt": (
            "Create a polished landscape infographic for a GitHub pull request. "
            "Explain the architecture, problem, and corrected behavior in simple conceptual language. "
            "Use three clearly connected areas: Flow, Problem, Fix. Keep text brief and legible. "
            f"Title: {args.title}. Summary: {args.summary}. "
            f"Theme: {theme['name']}. {theme['direction']} "
            "Use English captions for upstream reviewers. Do not invent benchmark numbers, test counts, "
            "or claims of complete validation. No credentials, brand logos, signatures, or watermarks. "
            f"Documentation context: {args.docs}."
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["prompt"])


if __name__ == "__main__":
    main()
