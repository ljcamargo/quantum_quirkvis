import xml.etree.ElementTree as ET
from pyqasm.entrypoint import loads
from .theme import ThemeManager

class SVGDrawer:
    def __init__(self, theme=None):
        self.theme_manager = ThemeManager(theme)

    def draw(self, program_str):
        if isinstance(program_str, str):
            module = loads(program_str)
        else:
            module = program_str

        module.unroll()
        module.remove_includes()
        
        line_nums, sizes = self._compute_line_nums(module)
        
        # Adaptation of _compute_moments from pyqasm
        statements = []
        for s in module._statements:
            # Filter declarations and only include QuantumStatement
            statements.append(s)

        moments, depths = self._compute_moments(statements, line_nums)
        
        n_lines = max(line_nums.values()) + 1 if line_nums else 0
        n_moments = len(moments)
        
        gate_width = self.theme_manager.get_dimension('gate_width')
        gate_spacing = self.theme_manager.get_dimension('gate_spacing')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        padding = self.theme_manager.get_dimension('padding')
        label_offset = self.theme_manager.get_dimension('label_offset')
        
        width = padding * 2 + n_moments * (gate_width + gate_spacing) + label_offset * 2
        height = n_lines * line_spacing + 2 * padding
        
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(width),
            'height': str(height),
            'viewBox': f'0 0 {width} {height}'
        })
        
        bg_color = self.theme_manager.get_style('background')
        ET.SubElement(svg, 'rect', {
            'width': '100%',
            'height': '100%',
            'fill': bg_color
        })
        
        # Draw labels
        text_color = self.theme_manager.get_style('text')
        label_font = self.theme_manager.get_style('label_font')
        for (reg_name, reg_idx), line_idx in line_nums.items():
            y = padding + line_idx * line_spacing
            label = f"{reg_name}[{reg_idx}]" if reg_idx != -1 else reg_name
            text = ET.SubElement(svg, 'text', {
                'x': str(padding + label_offset - 10),
                'y': str(y),
                'fill': text_color,
                'font-family': label_font.get('family', 'sans-serif'),
                'font-size': str(label_font.get('size', 12)),
                'text-anchor': 'end',
                'dominant-baseline': 'middle'
            })
            text.text = label

        # Draw wires
        wire_color = self.theme_manager.get_style('wire')
        for q, line_idx in line_nums.items():
            y = padding + line_idx * line_spacing
            ET.SubElement(svg, 'line', {
                'x1': str(padding + label_offset),
                'y1': str(y),
                'x2': str(width - padding),
                'y2': str(y),
                'stroke': wire_color,
                'stroke-width': '1'
            })

        # Draw moments
        x = padding + label_offset + gate_width/2
        for moment in moments:
            for stmt in moment:
                self._draw_statement(svg, stmt, x, line_nums)
            x += gate_width + gate_spacing

        return ET.tostring(svg, encoding='unicode')

    def _draw_statement(self, svg, stmt, x, line_nums):
        from openqasm3 import ast
        if isinstance(stmt, ast.QuantumGate):
            self._draw_gate(svg, stmt, x, line_nums)
        elif isinstance(stmt, ast.QuantumMeasurementStatement):
            self._draw_measurement(svg, stmt, x, line_nums)
        elif isinstance(stmt, ast.QuantumBarrier):
            self._draw_barrier(svg, stmt, x, line_nums)

    def _draw_gate(self, svg, gate, x, line_nums):
        name = gate.name.name.lower()
        qubits = [self._identifier_to_key(q) for q in gate.qubits]
        lines = [line_nums[q] for q in qubits]
        
        # Check for substitution
        sub = self.theme_manager.get_substitution(name)
        config = self.theme_manager.get_gate_config(name)
        
        if name == "cx" and len(lines) == 2:
            self._draw_cx(svg, lines[0], lines[1], x)
            return
        elif name == "swap" and len(lines) == 2:
            self._draw_swap(svg, lines[0], lines[1], x)
            return

        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')

        for line_idx in lines:
            y = padding + line_idx * line_spacing
            
            if sub and sub.get('type') == 'emoji':
                self._draw_emoji(svg, x, y, sub.get('value'))
            elif sub and sub.get('type') == 'image':
                self._draw_image(svg, x, y, sub.get('value'))
            elif sub and sub.get('type') == 'animation':
                self._draw_animation(svg, x, y, name, config, sub.get('value'))
            else:
                self._draw_box_gate(svg, x, y, name, config)

    def _draw_emoji(self, svg, x, y, emoji):
        text = ET.SubElement(svg, 'text', {
            'x': str(x),
            'y': str(y),
            'font-size': '24',
            'text-anchor': 'middle',
            'dominant-baseline': 'middle'
        })
        text.text = emoji

    def _draw_image(self, svg, x, y, url):
        gate_width = self.theme_manager.get_dimension('gate_width')
        gate_height = self.theme_manager.get_dimension('gate_height')
        ET.SubElement(svg, 'image', {
            'href': url,
            'x': str(x - gate_width/2),
            'y': str(y - gate_height/2),
            'width': str(gate_width),
            'height': str(gate_height)
        })

    def _draw_animation(self, svg, x, y, name, config, anim_type):
        gate_width = self.theme_manager.get_dimension('gate_width')
        gate_height = self.theme_manager.get_dimension('gate_height')
        
        fill = config.get('fill')
        stroke = config.get('stroke')
        radius = config.get('radius')
        
        rect_el = ET.SubElement(svg, 'rect', {
            'x': str(x - gate_width/2),
            'y': str(y - gate_height/2),
            'width': str(gate_width),
            'height': str(gate_height),
            'fill': fill,
            'stroke': stroke,
            'rx': str(radius)
        })
        
        if anim_type == 'pulse':
            ET.SubElement(rect_el, 'animate', {
                'attributeName': 'fill-opacity',
                'values': '1;0.4;1',
                'dur': '2s',
                'repeatCount': 'indefinite'
            })
        
        label = config.get('label', name.upper())
        text_color = self.theme_manager.get_style('text')
        txt = ET.SubElement(svg, 'text', {
            'x': str(x),
            'y': str(y),
            'fill': text_color,
            'font-family': 'sans-serif',
            'font-size': '12',
            'text-anchor': 'middle',
            'dominant-baseline': 'middle'
        })
        txt.text = label

    def _draw_box_gate(self, svg, x, y, name, config):
        gate_width = self.theme_manager.get_dimension('gate_width')
        gate_height = self.theme_manager.get_dimension('gate_height')
        
        fill = config.get('fill')
        stroke = config.get('stroke')
        radius = config.get('radius')
        
        ET.SubElement(svg, 'rect', {
            'x': str(x - gate_width/2),
            'y': str(y - gate_height/2),
            'width': str(gate_width),
            'height': str(gate_height),
            'fill': fill,
            'stroke': stroke,
            'rx': str(radius)
        })
        
        label = config.get('label', name.upper())
        text_color = self.theme_manager.get_style('text')
        txt = ET.SubElement(svg, 'text', {
            'x': str(x),
            'y': str(y),
            'fill': text_color,
            'font-family': 'sans-serif',
            'font-size': '12',
            'text-anchor': 'middle',
            'dominant-baseline': 'middle'
        })
        txt.text = label

    def _draw_cx(self, svg, ctrl_line, target_line, x):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        control_dot_radius = self.theme_manager.get_dimension('control_dot_radius')
        target_plus_radius = self.theme_manager.get_dimension('target_plus_radius')
        
        y1 = padding + ctrl_line * line_spacing
        y2 = padding + target_line * line_spacing
        wire_color = self.theme_manager.get_style('wire')
        
        # Vertical line
        ET.SubElement(svg, 'line', {
            'x1': str(x),
            'y1': str(y1),
            'x2': str(x),
            'y2': str(y2),
            'stroke': wire_color,
            'stroke-width': '1'
        })
        
        # Control dot
        ET.SubElement(svg, 'circle', {
            'cx': str(x),
            'cy': str(y1),
            'r': str(control_dot_radius),
            'fill': wire_color
        })
        
        # Target plus
        ET.SubElement(svg, 'circle', {
            'cx': str(x),
            'cy': str(y2),
            'r': str(target_plus_radius),
            'fill': 'none',
            'stroke': wire_color,
            'stroke-width': '1'
        })
        ET.SubElement(svg, 'line', {
            'x1': str(x - target_plus_radius), 'y1': str(y2), 'x2': str(x + target_plus_radius), 'y2': str(y2),
            'stroke': wire_color, 'stroke-width': '1'
        })
        ET.SubElement(svg, 'line', {
            'x1': str(x), 'y1': str(y2 - target_plus_radius), 'x2': str(x), 'y2': str(y2 + target_plus_radius),
            'stroke': wire_color, 'stroke-width': '1'
        })

    def _draw_swap(self, svg, line1, line2, x):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        swap_size = self.theme_manager.get_dimension('swap_size')
        
        y1 = padding + line1 * line_spacing
        y2 = padding + line2 * line_spacing
        wire_color = self.theme_manager.get_style('wire')
        
        ET.SubElement(svg, 'line', {
            'x1': str(x), 'y1': str(y1), 'x2': str(x), 'y2': str(y2),
            'stroke': wire_color, 'stroke-width': '1'
        })
        
        for y in [y1, y2]:
            d = swap_size
            ET.SubElement(svg, 'line', {
                'x1': str(x - d), 'y1': str(y - d), 'x2': str(x + d), 'y2': str(y + d),
                'stroke': wire_color, 'stroke-width': '1'
            })
            ET.SubElement(svg, 'line', {
                'x1': str(x - d), 'y1': str(y + d), 'x2': str(x + d), 'y2': str(y - d),
                'stroke': wire_color, 'stroke-width': '1'
            })

    def _draw_measurement(self, svg, stmt, x, line_nums):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        
        qubit = self._identifier_to_key(stmt.measure.qubit)
        line_idx = line_nums[qubit]
        y = padding + line_idx * line_spacing
        
        config = self.theme_manager.get_gate_config('measurement')
        self._draw_box_gate(svg, x, y, 'M', config)

    def _draw_barrier(self, svg, stmt, x, line_nums):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        barrier_style = self.theme_manager.get_style('barrier')
        barrier_padding = self.theme_manager.get_dimension('barrier_padding')
        
        qubits = [self._identifier_to_key(q) for q in stmt.qubits]
        lines = [line_nums[q] for q in qubits]
        if not lines: return
        
        y_min = padding + min(lines) * line_spacing - barrier_padding
        y_max = padding + max(lines) * line_spacing + barrier_padding
        
        ET.SubElement(svg, 'line', {
            'x1': str(x), 'y1': str(y_min), 'x2': str(x), 'y2': str(y_max),
            'stroke': barrier_style.get('stroke', 'gray'),
            'stroke-width': str(barrier_style.get('stroke_width', 2)),
            'stroke-dasharray': barrier_style.get('dasharray', '4,4')
        })

    def _compute_moments(self, statements, line_nums):
        # Full implementation of moment computation
        from openqasm3 import ast
        depths = {k: -1 for k in line_nums}
        moments = []
        
        for statement in statements:
            # Filter non-quantum statements
            if isinstance(statement, (ast.CalibrationGrammarDeclaration, ast.ClassicalDeclaration, 
                                     ast.ConstantDeclaration, ast.ExternDeclaration, 
                                     ast.IODeclaration, ast.QubitDeclaration)):
                continue

            if isinstance(statement, ast.QuantumGate):
                qubits = [self._identifier_to_key(q) for q in statement.qubits]
                target_keys = qubits # simplified for now, pyqasm handles multi-qubit range
                depth = 1 + max(depths[key] for key in target_keys)
                for key in target_keys:
                    depths[key] = depth
            elif isinstance(statement, ast.QuantumMeasurementStatement):
                key = self._identifier_to_key(statement.measure.qubit)
                depth = 1 + depths[key]
                depths[key] = depth
            else:
                # Skip other statements for now
                continue

            if depth >= len(moments):
                for _ in range(depth - len(moments) + 1):
                    moments.append([])
            
            moments[depth].append(statement)
            
        return moments, depths

    def _identifier_to_key(self, identifier):
        from openqasm3 import ast
        from pyqasm.expressions import Qasm3ExprEvaluator
        if isinstance(identifier, ast.Identifier):
            return identifier.name, -1

        indices = identifier.indices
        if len(indices) >= 1 and isinstance(indices[0], list) and len(indices[0]) >= 1:
            return (
                identifier.name.name,
                Qasm3ExprEvaluator.evaluate_expression(indices[0][0])[0],
            )
        raise ValueError(f"Unsupported identifier: {identifier}")

    def _compute_line_nums(self, module):
        # Adapted from pyqasm printer.py
        line_nums = {}
        sizes = {}
        line_num = -1
        
        # Classical registers
        for k in module._classical_registers:
            line_num += 1
            line_nums[(k, -1)] = line_num
            sizes[(k, -1)] = module._classical_registers[k]
            
        # Qubit registers
        for qubit_reg in module._qubit_registers:
            size = module._qubit_registers[qubit_reg]
            line_num += size
            for i in range(size):
                line_nums[(qubit_reg, i)] = line_num
                line_num -= 1
            line_num += size
            
        return line_nums, sizes

def draw(program, theme=None, filename=None):
    drawer = SVGDrawer(theme)
    svg_content = drawer.draw(program)
    if filename:
        with open(filename, 'w') as f:
            f.write(svg_content)
    return svg_content
