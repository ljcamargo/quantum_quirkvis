import json
import os

def deep_merge(base, update):
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base

class ThemeManager:
    def __init__(self, theme_data=None):
        self.theme = self._get_default_theme()
        if theme_data:
            if isinstance(theme_data, str):
                self.load_from_file(theme_data)
            elif isinstance(theme_data, dict):
                self.update_theme(theme_data)

    def _get_default_theme(self):
        default_path = os.path.join(os.path.dirname(__file__), "themes", "default.json")
        with open(default_path, 'r') as f:
            return json.load(f)

    def load_from_file(self, filepath):
        if not os.path.exists(filepath):
            # Try loading from built-in themes directory
            builtin_path = os.path.join(os.path.dirname(__file__), "themes", f"{filepath}.json")
            if os.path.exists(builtin_path):
                filepath = builtin_path
            else:
                raise FileNotFoundError(f"Theme file {filepath} not found.")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.update_theme(data)

    def update_theme(self, data):
        deep_merge(self.theme, data)

    def get_style(self, category, subkey=None):
        style = self.theme.get("styles", {}).get(category)
        if style is None:
            raise KeyError(f"Style category '{category}' not found in theme.")
        if subkey:
            if not isinstance(style, dict):
                raise TypeError(f"Style category '{category}' is not a dictionary.")
            val = style.get(subkey)
            if val is None:
                raise KeyError(f"Subkey '{subkey}' not found in style category '{category}'.")
            return val
        return style

    def get_dimension(self, key):
        val = self.theme.get("dimensions", {}).get(key)
        if val is None:
            raise KeyError(f"Dimension '{key}' not found in theme.")
        return val

    def get_shape_config(self, shape_name):
        config = self.theme.get("shapes", {}).get(shape_name)
        if config is None:
            raise KeyError(f"Shape '{shape_name}' not found in theme.")
        return config

    def get_gate_config(self, gate_name):
        # Gates use the base 'gate' shape config as their foundation
        base_config = self.get_shape_config("gate")
        gate_specific = self.theme.get("gates", {}).get(gate_name, {})
        return {**base_config, **gate_specific}

    def get_substitution(self, gate_name):
        return self.theme.get("substitutions", {}).get(gate_name)
