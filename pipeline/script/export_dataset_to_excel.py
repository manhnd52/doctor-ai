import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pandas as pd


def load_python_module(module_path: Path):
    spec = importlib.util.spec_from_file_location("dataset_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def to_cell(value: Any) -> Any:
    """Convert nested values into JSON strings so they fit in a single Excel cell."""
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=False)
    return value


def build_main_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        row = {key: to_cell(value) for key, value in record.items()}
        rows.append(row)
    return rows


def build_nodes_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for record_idx, record in enumerate(records, start=1):
        sample_id = record.get("id", record_idx)
        question = record.get("question", "")
        nodes = record.get("nodes", [])

        if not isinstance(nodes, list):
            continue

        for node_idx, node in enumerate(nodes, start=1):
            if isinstance(node, dict):
                row = {
                    "sample_id": sample_id,
                    "question": question,
                    "node_order": node_idx,
                }
                for key, value in node.items():
                    row[key] = to_cell(value)
                rows.append(row)
            else:
                rows.append(
                    {
                        "sample_id": sample_id,
                        "question": question,
                        "node_order": node_idx,
                        "node_value": to_cell(node),
                    }
                )

    return rows


def export_dataset_to_excel(module_path: Path, variable_name: str, output_path: Path) -> None:
    module = load_python_module(module_path)

    if not hasattr(module, variable_name):
        raise AttributeError(f"Variable '{variable_name}' not found in {module_path}")

    dataset = getattr(module, variable_name)
    if not isinstance(dataset, list):
        raise TypeError(f"'{variable_name}' must be a list, got: {type(dataset).__name__}")

    if not dataset:
        raise ValueError(f"'{variable_name}' is empty, nothing to export")

    if not all(isinstance(item, dict) for item in dataset):
        raise TypeError(f"'{variable_name}' must be a list of dict objects")

    main_rows = build_main_rows(dataset)
    nodes_rows = build_nodes_rows(dataset)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(main_rows).to_excel(writer, sheet_name="samples", index=False)

        if nodes_rows:
            pd.DataFrame(nodes_rows).to_excel(writer, sheet_name="nodes", index=False)

    print(f"Exported {len(dataset)} records to: {output_path}")
    if nodes_rows:
        print(f"Exported {len(nodes_rows)} node rows to sheet: nodes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Python dataset variable to Excel file")
    parser.add_argument(
        "--input",
        default="data/dataset.py",
        help="Path to Python file containing dataset variable",
    )
    parser.add_argument(
        "--var",
        default="manual_samples",
        help="Variable name to export (default: manual_samples)",
    )
    parser.add_argument(
        "--output",
        default="outputs/manual_samples.xlsx",
        help="Output .xlsx path",
    )

    args = parser.parse_args()

    export_dataset_to_excel(
        module_path=Path(args.input).resolve(),
        variable_name=args.var,
        output_path=Path(args.output).resolve(),
    )


if __name__ == "__main__":
    main()
