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
        style = self.theme.get("styles", {}).get(category, {})
        if subkey and isinstance(style, dict):
            return style.get(subkey)
        return style

    def get_dimension(self, key):
        return self.theme.get("dimensions", {}).get(key)

    def get_gate_config(self, gate_name):
        gate_config = self.theme.get("gates", {}).get(gate_name, {})
        # Overlay with default box styles if not present
        return {**self.theme["styles"].get("gate_box", {}), **gate_config}

    def get_substitution(self, gate_name):
        return self.theme.get("substitutions", {}).get(gate_name)
