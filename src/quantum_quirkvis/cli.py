#!/usr/bin/env python3
import argparse
import sys
from quantum_quirkvis import draw


def main():
    p = argparse.ArgumentParser(description="Render QASM to SVG using quantum_quirkvis")
    p.add_argument("input", nargs="?", help="Input QASM file (default: stdin)")
    p.add_argument("-t", "--theme", help="Theme name or JSON file", default=None)
    p.add_argument("-o", "--output", help="Output SVG file (default: stdout)")
    args = p.parse_args()

    # Read QASM from file or stdin
    if args.input and args.input != "-":
        with open(args.input, "r", encoding="utf-8") as f:
            qasm_str = f.read()
    else:
        qasm_str = sys.stdin.read()

    # If output file specified, let library write it
    if args.output:
        draw(qasm_str, theme=args.theme, filename=args.output)
    else:
        svg = draw(qasm_str, theme=args.theme)
        sys.stdout.write(svg)


if __name__ == "__main__":
    main()
