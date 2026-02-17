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
        statements = list(module._statements)
        moments, depths = self._compute_moments(statements, line_nums)
        
        n_lines = max(line_nums.values()) + 1 if line_nums else 0
        n_moments = len(moments)
        
        # No fallbacks allowed, these will raise KeyError if missing in theme
        gate_width = self.theme_manager.get_dimension('gate_width')
        gate_spacing = self.theme_manager.get_dimension('gate_spacing')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        padding = self.theme_manager.get_dimension('padding')
        label_offset = self.theme_manager.get_dimension('label_offset')
        
        width = padding * 2 + n_moments * (gate_width + gate_spacing) + label_offset * 1.5
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
                'font-family': label_font['family'],
                'font-size': str(label_font['size']),
                'text-anchor': 'end',
                'dominant-baseline': 'middle'
            })
            text.text = label

        # Draw wires (Stave)
        wire_config = self.theme_manager.get_style('qubit_wire')
        for q, line_idx in line_nums.items():
            y = padding + line_idx * line_spacing
            self._draw_line(svg, padding + label_offset, y, width - padding, y, wire_config)

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
            if sub:
                self._draw_shape(svg, x, y, sub, label=config.get('label', name.upper()))
            else:
                self._draw_shape(svg, x, y, config, label=config.get('label', name.upper()))

    def _draw_cx(self, svg, ctrl_line, target_line, x):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        
        y1 = padding + ctrl_line * line_spacing
        y2 = padding + target_line * line_spacing
        
        # Vertical connection line
        conn_config = self.theme_manager.get_style('connection_line')
        self._draw_line(svg, x, y1, x, y2, conn_config)
        
        # Control dot
        dot_config = self.theme_manager.get_shape_config('control_dot')
        self._draw_shape(svg, x, y1, dot_config)
        
        # Target plus
        plus_config = self.theme_manager.get_shape_config('target_plus')
        self._draw_shape(svg, x, y2, plus_config)

    def _draw_swap(self, svg, line1, line2, x):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        
        y1 = padding + line1 * line_spacing
        y2 = padding + line2 * line_spacing
        
        conn_config = self.theme_manager.get_style('connection_line')
        self._draw_line(svg, x, y1, x, y2, conn_config)
        
        cross_config = self.theme_manager.get_shape_config('swap_x')
        for y in [y1, y2]:
            self._draw_shape(svg, x, y, cross_config)

    def _draw_measurement(self, svg, stmt, x, line_nums):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        
        qubit = self._identifier_to_key(stmt.measure.qubit)
        line_idx = line_nums[qubit]
        y = padding + line_idx * line_spacing
        
        config = self.theme_manager.get_gate_config('measurement')
        self._draw_shape(svg, x, y, config, label=config.get('label', 'M'))

    def _draw_barrier(self, svg, stmt, x, line_nums):
        padding = self.theme_manager.get_dimension('padding')
        line_spacing = self.theme_manager.get_dimension('line_spacing')
        barrier_config = self.theme_manager.get_style('barrier')
        barrier_padding = self.theme_manager.get_dimension('barrier_padding')
        
        qubits = [self._identifier_to_key(q) for q in stmt.qubits]
        lines = [line_nums[q] for q in qubits]
        if not lines: return
        
        y_min = padding + min(lines) * line_spacing - barrier_padding
        y_max = padding + max(lines) * line_spacing + barrier_padding
        
        self._draw_line(svg, x, y_min, x, y_max, barrier_config)

    def _draw_line(self, svg, x1, y1, x2, y2, config):
        style = config['style']
        stroke = config['stroke']
        width = config['stroke_width']
        dash = config.get('dasharray', '')
        
        if style == 'wave':
            amp = config['amplitude']
            wl = config['wavelength']
            path_data = self._wave_path(x1, y1, x2, y2, amp, wl)
            ET.SubElement(svg, 'path', {
                'd': path_data,
                'stroke': stroke,
                'stroke-width': str(width),
                'fill': 'none',
                'stroke-dasharray': dash
            })
        else:
            ET.SubElement(svg, 'line', {
                'x1': str(x1), 'y1': str(y1), 'x2': str(x2), 'y2': str(y2),
                'stroke': stroke, 'stroke-width': str(width),
                'stroke-dasharray': dash
            })

    def _wave_path(self, x1, y1, x2, y2, amplitude, wavelength):
        import math
        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        angle = math.atan2(y2 - y1, x2 - x1)
        
        num_cycles = int(dist / wavelength)
        # We'll use a series of cubic beziers (via 'q' and 't' commands)
        # to simulate the wave, oriented along the line.
        points = [f"{x1},{y1}"]
        
        # For simplicity and precision, we generate points and join with L
        # This makes it easier to handle arbitrary rotations and non-integer cycles.
        res = 10 # points per wavelength
        num_points = int(dist / wavelength * res)
        d_points = []
        for i in range(num_points + 1):
            t = i / num_points
            curr_dist = t * dist
            
            # Local wave offset
            wave_y = amplitude * math.sin(2 * math.pi * curr_dist / wavelength)
            
            # Rotate and translate
            gx = x1 + curr_dist * math.cos(angle) - wave_y * math.sin(angle)
            gy = y1 + curr_dist * math.sin(angle) + wave_y * math.cos(angle)
            d_points.append(f"{gx} {gy}")
            
        return "M " + " L ".join(d_points)

    def _draw_shape(self, svg, x, y, config, label=None):
        shape_type = config['type']
        
        if shape_type == 'circle':
            radius = config['radius']
            ET.SubElement(svg, 'circle', {
                'cx': str(x), 'cy': str(y), 'r': str(radius),
                'fill': config.get('fill', 'none'),
                'stroke': config.get('stroke', 'none'),
                'stroke-width': str(config.get('stroke_width', 1))
            })
        elif shape_type == 'rect':
            w = config['width']
            h = config['height']
            r = config.get('radius', 0)
            ET.SubElement(svg, 'rect', {
                'x': str(x - w/2), 'y': str(y - h/2),
                'width': str(w), 'height': str(h), 'rx': str(r),
                'fill': config.get('fill', 'none'),
                'stroke': config.get('stroke', 'none'),
                'stroke-width': str(config.get('stroke_width', 1))
            })
        elif shape_type == 'emoji':
            text = ET.SubElement(svg, 'text', {
                'x': str(x), 'y': str(y),
                'font-size': '24',
                'text-anchor': 'middle', 'dominant-baseline': 'middle'
            })
            text.text = config['value']
        elif shape_type == 'image':
            w = self.theme_manager.get_dimension('gate_width')
            h = self.theme_manager.get_dimension('gate_height')
            ET.SubElement(svg, 'image', {
                'href': config['value'],
                'x': str(x - w/2), 'y': str(y - h/2),
                'width': str(w), 'height': str(h)
            })
        elif shape_type == 'cross':
            size = config['size']
            stroke = config['stroke']
            sw = config['stroke_width']
            ET.SubElement(svg, 'line', {
                'x1': str(x - size), 'y1': str(y - size), 'x2': str(x + size), 'y2': str(y + size),
                'stroke': stroke, 'stroke-width': str(sw)
            })
            ET.SubElement(svg, 'line', {
                'x1': str(x - size), 'y1': str(y + size), 'x2': str(x + size), 'y2': str(y - size),
                'stroke': stroke, 'stroke-width': str(sw)
            })
        elif shape_type == 'plus_circle':
            radius = config['radius']
            stroke = config['stroke']
            sw = config['stroke_width']
            ET.SubElement(svg, 'circle', {
                'cx': str(x), 'cy': str(y), 'r': str(radius),
                'fill': 'none', 'stroke': stroke, 'stroke-width': str(sw)
            })
            ET.SubElement(svg, 'line', {
                'x1': str(x - radius), 'y1': str(y), 'x2': str(x + radius), 'y2': str(y),
                'stroke': stroke, 'stroke-width': str(sw)
            })
            ET.SubElement(svg, 'line', {
                'x1': str(x), 'y1': str(y - radius), 'x2': str(x), 'y2': str(y + radius),
                'stroke': stroke, 'stroke-width': str(sw)
            })
        elif shape_type == 'svg':
             # Inline or external SVG would go here
             pass

        if label:
            text_color = self.theme_manager.get_style('text')
            txt = ET.SubElement(svg, 'text', {
                'x': str(x), 'y': str(y),
                'fill': text_color, 'font-family': 'sans-serif', 'font-size': '12',
                'text-anchor': 'middle', 'dominant-baseline': 'middle'
            })
            txt.text = label

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
