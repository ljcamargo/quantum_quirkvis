import os
import glob
from quantum_quirkvis import draw

# Directories
QASM_DIR = "tests/qasms"
THEME_DIR = "tests/themes"
OUTPUT_DIR = "test_output"

# Built-in themes to test
BUILTIN_THEMES = ["default", "night"]

def run_tests():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get all qasm files
    qasm_files = glob.glob(os.path.join(QASM_DIR, "*.qasm"))
    
    # Get all theme files
    theme_files = glob.glob(os.path.join(THEME_DIR, "*.json"))
    
    # Combined list of themes (built-in names and file paths)
    themes = BUILTIN_THEMES + theme_files

    print(f"Starting automated tests...")
    print(f"Found {len(qasm_files)} QASM files and {len(themes)} themes.")

    count = 0
    for qasm_path in qasm_files:
        with open(qasm_path, 'r') as f:
            qasm_content = f.read()
        
        qasm_name = os.path.splitext(os.path.basename(qasm_path))[0]
        
        for theme in themes:
            if os.path.isfile(theme):
                theme_name = os.path.splitext(os.path.basename(theme))[0]
            else:
                theme_name = theme
            
            output_filename = f"{qasm_name}_{theme_name}.svg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            print(f" - Rendering {qasm_name} with theme {theme_name} -> {output_filename}")
            try:
                draw(qasm_content, theme=theme, filename=output_path)
                count += 1
            except Exception as e:
                print(f"   [ERROR] Failed to render {qasm_name} with theme {theme_name}: {e}")

    print(f"\nFinished! Generated {count} SVG files in '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    run_tests()
