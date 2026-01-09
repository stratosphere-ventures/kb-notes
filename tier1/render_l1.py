#!/usr/bin/env python3
"""
Jinja2 Rendering Script for Layer 1 Data
Renders JSON day files using market_wrap_l1.md.j2 template
"""

import json
import os
import sys
import argparse


def render_json_file(json_file: str, template_file: str, output_dir: str) -> bool:
    """Render a single JSON file to markdown"""
    # Import jinja2 at module level
    try:
        import jinja2
    except ImportError:
        print("WARNING: jinja2 library not installed")
        print("  Install with: pip install jinja2")
        return False
    
    try:
        # Load JSON data
        with open(json_file, "r") as f:
            day = json.load(f)
        
        # Load template
        with open(template_file, "r") as f:
            template_content = f.read()
        
        # Create jinja2 environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(template_file)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        template = env.from_string(template_content)
        
        # Render template
        rendered = template.render(day=day)
        
        # Determine output filename
        base_name = os.path.basename(json_file).replace(".json", ".md")
        output_file = os.path.join(output_dir, base_name)
        
        # Write output
        with open(output_file, "w") as f:
            f.write(rendered)
        
        print(f"✓ Rendered {base_name}")
        return True
    
    except Exception as e:
        print(f"WARNING: Error rendering {json_file}")
        print(f"  {type(e).__name__}: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Render Layer 1 JSON files to markdown")
    parser.add_argument("--template", default="market_wrap_l1.md.j2", help="Path to Jinja2 template file")
    parser.add_argument("--input-dir", default="sample_data", help="Directory containing JSON files")
    parser.add_argument("--output-dir", default="sample_output", help="Directory for rendered markdown files")
    
    args = parser.parse_args()
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, args.template)
    input_dir = os.path.join(script_dir, args.input_dir)
    output_dir = os.path.join(script_dir, args.output_dir)
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"WARNING: Template file not found: {template_path}")
        return 0
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"WARNING: Input directory not found: {input_dir}")
        return 0
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all JSON files
    json_files = sorted([
        f for f in os.listdir(input_dir)
        if f.endswith(".json")
    ])
    
    if not json_files:
        print(f"WARNING: No JSON files found in {input_dir}")
        return 0
    
    print(f"Rendering {len(json_files)} file(s) using {args.template}...")
    print("="*50)
    
    # Render each file
    passed = 0
    failed = 0
    
    for json_file in json_files:
        full_path = os.path.join(input_dir, json_file)
        if render_json_file(full_path, template_path, output_dir):
            passed += 1
        else:
            failed += 1
    
    print("="*50)
    print(f"Rendering complete: {passed} passed, {failed} failed")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
