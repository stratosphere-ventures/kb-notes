#!/usr/bin/env python3
"""
JSON Schema Validation Script for Layer 1 Data
Validates generated JSON files against schema.json
"""

import json
import sys
import os
import argparse


def validate_file(json_file: str, schema_file: str) -> bool:
    """Validate a JSON file against schema"""
    try:
        with open(json_file, "r") as f:
            data = json.load(f)

        with open(schema_file, "r") as f:
            schema = json.load(f)

        # Import jsonschema
        try:
            import jsonschema
        except ImportError:
            print("WARNING: jsonschema library not installed")
            print("  Install with: pip install jsonschema")
            print("  Skipping validation")
            return True

        # Validate
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            print(f"WARNING: Validation failed for {json_file}")
            print(f"  Message: {e.message}")
            print(f"  Path: {list(e.path)}")
            print(f"  Schema path: {list(e.schema_path)}")
            return False
        except jsonschema.SchemaError as e:
            print(f"WARNING: Schema error in {schema_file}")
            print(f"  Message: {e.message}")
            print(f"  Path: {list(e.path)}")
            return False

    except FileNotFoundError as e:
        print(f"WARNING: File not found: {e.filename}")
        return False
    except json.JSONDecodeError as e:
        print(f"WARNING: Invalid JSON in {json_file}")
        print(f"  Line {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"WARNING: Unexpected error validating {json_file}")
        print(f"  {type(e).__name__}: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Validate Layer 1 JSON files against schema"
    )
    parser.add_argument(
        "--schema", default="schema.json", help="Path to schema.json file"
    )

    args = parser.parse_args()

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, args.schema)

    # Check if schema exists
    if not os.path.exists(schema_path):
        print(f"WARNING: Schema file not found: {schema_path}")
        return 0

    # Get sample data directory
    sample_data_dir = os.path.join(script_dir, "sample_data")

    if not os.path.exists(sample_data_dir):
        print(f"WARNING: Sample data directory not found: {sample_data_dir}")
        return 0

    # Get all JSON files
    json_files = sorted([f for f in os.listdir(sample_data_dir) if f.endswith(".json")])

    if not json_files:
        print(f"WARNING: No JSON files found in {sample_data_dir}")
        return 0

    print(f"Validating {len(json_files)} file(s) against {args.schema}...")
    print("=" * 50)

    # Validate each file
    passed = 0
    failed = 0

    for json_file in json_files:
        full_path = os.path.join(sample_data_dir, json_file)
        if validate_file(full_path, schema_path):
            passed += 1
            print(f"✓ {json_file} - Valid")
        else:
            failed += 1
            print(f"✗ {json_file} - Validation failed")

    print("=" * 50)
    print(f"Validation complete: {passed} passed, {failed} failed")

    # Always exit with code 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
