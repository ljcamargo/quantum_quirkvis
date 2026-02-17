# Quantum QuirkVis

A Python package that draws quantum circuits written in OpenQASM and outputs as SVG with a strong focus on personalization.

## Features
- SVG output
- Theming engine (JSON)
- Personalization (night mode, custom colors)
- Gate substitutions (emojis, icons, animations)

## Installation
```bash
pip install .
```

## Usage
```python
from quantum_quirkvis import draw
draw("qreg q[2]; h q[0]; cx q[0], q[1];", theme="night")
```
