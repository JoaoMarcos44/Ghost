"""Prepare native-image prompts for the three remaining Ghost fixes."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--title', required=True)
    parser.add_argument('--summary', required=True)
    parser.add_argument('--docs', required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    title = args.title.lower()
    if 'pagination' in title:
        theme = 'Transit map: off-white, cobalt, orange; consecutive numbered stops grouped into pages.'
    elif 'product' in title:
        theme = 'Bauhaus product poster: cream, red, yellow and black; separate description link and purchase button.'
    else:
        theme = 'Observatory timeline: midnight blue, violet and silver; a clear historical window and later events.'
    prompt = (
        'Create a polished landscape infographic explaining a Ghost pull request. '
        'Use simple English and three clearly connected panels: Flow, Problem, Fix. '
        f'Title: {args.title}. Summary: {args.summary}. Theme: {theme} '
        'Keep labels brief and legible. Explain the architecture conceptually. '
        'No invented test counts, performance numbers, screenshots, logos or validation badges. '
        f'Documentation context: {args.docs}.'
    )
    payload = dict(title=args.title, summary=args.summary, validation_docs=args.docs,
                   theme=theme, prompt=prompt)
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else prompt)


if __name__ == '__main__':
    main()
