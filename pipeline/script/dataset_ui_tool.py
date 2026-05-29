import ast
import json
import pprint
import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, cast

from pipeline.nodes.entity_extraction import entity_extraction_node
from nodes.entity_linking import entity_linking_node
from pipeline.nodes.cypher_generation import cypher_generation_node
from script.dataset_table_view import DatasetTableView
from services.graph.utils import get_graph, validate_cypher
from pipeline_state import GraphState

DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "dataset.py"


def _load_dataset_samples() -> List[Dict[str, Any]]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Khong tim thay file dataset: {DATASET_PATH}")

    content = DATASET_PATH.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(DATASET_PATH))

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != "manual_samples":
            continue

        value = ast.literal_eval(node.value)
        if not isinstance(value, list):
            raise ValueError("manual_samples khong phai list.")
        return cast(List[Dict[str, Any]], value)

    raise ValueError("Khong tim thay bien manual_samples trong dataset.py")


def _write_dataset_samples(samples: List[Dict[str, Any]]) -> None:
    payload = pprint.pformat(samples, width=120, sort_dicts=False)
    DATASET_PATH.write_text(f"manual_samples = {payload}\n", encoding="utf-8")

def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)

def _normalize_record(row: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}

    for key, value in row.items():
        out_key = str(key).lower().replace(" ", "_")

        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                nested_out_key = str(nested_key).lower().replace(" ", "_")
                normalized[nested_out_key] = _normalize_scalar(nested_value)
            continue

        if hasattr(value, "items"):
            try:
                for nested_key, nested_value in dict(value).items():
                    nested_out_key = str(nested_key).lower().replace(" ", "_")
                    normalized[nested_out_key] = _normalize_scalar(nested_value)
                continue
            except Exception:
                pass

        normalized[out_key] = _normalize_scalar(value)

    return normalized


def generate_expected_cypher(question: str) -> str:
    state: Dict[str, Any] = {
        "question": question,
        "metrics": {},
    }

    state.update(entity_extraction_node(state))
    state.update(entity_linking_node(state))
    state.update(cypher_generation_node(cast(GraphState, state)))

    return state.get("cypher", "").strip()


def query_nodes_from_cypher(cypher: str) -> List[Dict[str, Any]]:
    if not validate_cypher(cypher):
        raise ValueError("Cypher khong hop le. Vui long kiem tra lai.")

    graph = get_graph()
    rows = graph.query(cypher)
    return [_normalize_record(row) for row in rows]


def _next_id(samples: List[Dict[str, Any]]) -> int:
    ids = [int(item["id"]) for item in samples if isinstance(item, dict) and "id" in item and str(item["id"]).isdigit()]
    if not ids:
        return 1
    return max(ids) + 1


def get_total_samples() -> int:
    try:
        return len(_load_dataset_samples())
    except FileNotFoundError:
        return 0
    except Exception:
        content = DATASET_PATH.read_text(encoding="utf-8")
        return len(re.findall(r'"id"\s*:\s*\d+', content))


def get_sample_by_id(sample_id: int) -> Optional[Dict[str, Any]]:
    samples = _load_dataset_samples()
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        if sample.get("id") == sample_id:
            return sample
    return None


def list_samples_overview() -> List[Dict[str, Any]]:
    samples = _load_dataset_samples()
    clean_rows: List[Dict[str, Any]] = []

    for sample in samples:
        if not isinstance(sample, dict):
            continue
        clean_rows.append(
            {
                "id": sample.get("id", ""),
                "active": bool(sample.get("active", True)),
                "question": sample.get("question", ""),
                "expected_cypher": sample.get("expected_cypher", ""),
            }
        )

    clean_rows.sort(key=lambda row: int(row["id"]) if str(row.get("id", "")).isdigit() else 0)
    return clean_rows


def delete_sample_by_id(sample_id: int) -> None:
    samples = _load_dataset_samples()
    before_count = len(samples)

    filtered = []
    for sample in samples:
        if not isinstance(sample, dict):
            filtered.append(sample)
            continue
        if sample.get("id") == sample_id:
            continue
        filtered.append(sample)

    if len(filtered) == before_count:
        raise ValueError(f"Khong tim thay sample id={sample_id} de xoa.")

    _write_dataset_samples(filtered)


def set_sample_active(sample_id: int, active: bool) -> None:
    samples = _load_dataset_samples()
    target: Optional[Dict[str, Any]] = None

    for sample in samples:
        if not isinstance(sample, dict):
            continue
        if sample.get("id") == sample_id:
            target = sample
            break

    if target is None:
        raise ValueError(f"Khong tim thay sample id={sample_id} de cap nhat active.")

    target["active"] = bool(active)
    _write_dataset_samples(samples)


def append_to_dataset(
    question: str,
    expected_cypher: str,
    nodes: List[Dict[str, Any]],
    source: str,
    source_id: str,
) -> int:
    samples = _load_dataset_samples()
    new_id = _next_id(samples)

    new_entry = {
        "id": new_id,
        "question": question,
        "source": source,
        "source_id": source_id,
        "expected_cypher": expected_cypher,
        "expected_answer": "",
        "nodes": nodes,
    }

    samples.append(new_entry)
    _write_dataset_samples(samples)
    return new_id


def update_sample_by_id(
    sample_id: int,
    question: str,
    expected_cypher: str,
    nodes: List[Dict[str, Any]],
    source: str,
    source_id: str,
) -> None:
    samples = _load_dataset_samples()
    target: Optional[Dict[str, Any]] = None

    for sample in samples:
        if not isinstance(sample, dict):
            continue
        if sample.get("id") == sample_id:
            target = sample
            break

    if target is None:
        raise ValueError(f"Khong tim thay sample id={sample_id} trong dataset.py")

    target["question"] = question
    target["source"] = source
    target["source_id"] = source_id
    target["expected_cypher"] = expected_cypher
    target["nodes"] = nodes
    if "expected_answer" not in target:
        target["expected_answer"] = ""

    _write_dataset_samples(samples)


class DatasetToolUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Dataset Builder Tool")
        self.root.geometry("1050x760")

        self.nodes_data: List[Dict[str, Any]] = []
        self.editing_sample_id: Optional[int] = None
        self.active_mode: Optional[str] = None
        self.main_container = ttk.Frame(self.root, padding=12)
        self.main_container.pack(fill="both", expand=True)

        self._build_mode_selector()

    def _clear_main_container(self) -> None:
        for child in self.main_container.winfo_children():
            child.destroy()

    def _build_mode_selector(self) -> None:
        self._clear_main_container()

        box = ttk.Frame(self.main_container)
        box.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(box, text="Chon che do lam viec", font=("Segoe UI", 16, "bold")).pack(pady=(0, 8))
        ttk.Label(
            box,
            text="Ban can chon Add mode hoac Edit mode truoc khi vao form.",
        ).pack(pady=(0, 18))

        button_row = ttk.Frame(box)
        button_row.pack()

        ttk.Button(button_row, text="Add mode", command=lambda: self._enter_mode("add")).pack(side="left", padx=(0, 10))
        ttk.Button(button_row, text="Edit mode", command=lambda: self._enter_mode("edit")).pack(side="left", padx=(0, 10))
        ttk.Button(button_row, text="Table view", command=self.open_table_view).pack(side="left")

    def _enter_mode(self, mode: str) -> None:
        self.active_mode = mode
        self.nodes_data = []
        self.editing_sample_id = None
        self._build_layout()

        if mode == "add":
            self.status_var.set("Dang o Add mode. Ban co the tao sample moi.")
        else:
            self.status_var.set("Dang o Edit mode. Vui long nhap Sample ID va bam Load sample.")

    def _build_layout(self) -> None:
        self._clear_main_container()
        main = self.main_container

        top_row = ttk.Frame(main)
        top_row.pack(fill="x", pady=(0, 8))
        ttk.Button(top_row, text="Doi mode", command=self._build_mode_selector).pack(side="right")
        ttk.Button(top_row, text="Mo Table view", command=self.open_table_view).pack(side="right", padx=(0, 8))
        mode_name = "Add" if self.active_mode == "add" else "Edit"
        ttk.Label(top_row, text=f"Che do hien tai: {mode_name}").pack(side="left")

        ttk.Label(main, text="Question").pack(anchor="w")
        self.question_text = tk.Text(main, height=4, wrap="word")
        self.question_text.pack(fill="x", pady=(4, 10))

        self.sample_id_var = tk.StringVar()
        if self.active_mode == "edit":
            edit_row = ttk.Frame(main)
            edit_row.pack(fill="x", pady=(0, 10))

            ttk.Label(edit_row, text="Sample ID (edit)").pack(side="left")
            self.sample_id_entry = ttk.Entry(edit_row, textvariable=self.sample_id_var, width=14)
            self.sample_id_entry.pack(side="left", padx=(8, 8))
            ttk.Button(edit_row, text="Load sample", command=self.on_load_sample).pack(side="left", padx=(0, 8))
            ttk.Button(edit_row, text="Bo chon sample", command=self.on_exit_edit_mode).pack(side="left")

        source_row = ttk.Frame(main)
        source_row.pack(fill="x", pady=(0, 10))

        ttk.Label(source_row, text="Source").pack(side="left")
        self.source_var = tk.StringVar()
        self.source_entry = ttk.Entry(source_row, textvariable=self.source_var)
        self.source_entry.pack(side="left", fill="x", expand=True, padx=(8, 12))

        ttk.Label(source_row, text="Source ID").pack(side="left")
        self.source_id_var = tk.StringVar()
        self.source_id_entry = ttk.Entry(source_row, textvariable=self.source_id_var, width=24)
        self.source_id_entry.pack(side="left", padx=(8, 0))

        button_row = ttk.Frame(main)
        button_row.pack(fill="x", pady=(0, 10))

        ttk.Button(button_row, text="1) Sinh expected_cypher", command=self.on_generate_cypher).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="2) Lay nodes tu Neo4j", command=self.on_fetch_nodes).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="3) Luu vao dataset.py", command=self.on_save).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="Xoa form", command=self.on_clear).pack(side="left")

        ttk.Label(main, text="Expected Cypher").pack(anchor="w")
        self.cypher_text = tk.Text(main, height=10, wrap="word")
        self.cypher_text.pack(fill="both", expand=False, pady=(4, 10))

        ttk.Label(main, text="Nodes (preview JSON)").pack(anchor="w")
        self.nodes_preview = tk.Text(main, height=18, wrap="none")
        self.nodes_preview.pack(fill="both", expand=True, pady=(4, 10))

        footer = ttk.Frame(main)
        footer.pack(fill="x")

        self.status_var = tk.StringVar(value="San sang.")
        ttk.Label(footer, textvariable=self.status_var).pack(side="left", anchor="w")

        self.total_samples_var = tk.StringVar(value="")
        ttk.Label(footer, textvariable=self.total_samples_var).pack(side="right", anchor="e")
        self.mode_var = tk.StringVar(value="Mode: Tao moi")
        ttk.Label(footer, textvariable=self.mode_var).pack(side="right", padx=(0, 12), anchor="e")
        self._refresh_total_samples()

    def _refresh_total_samples(self) -> None:
        total = get_total_samples()
        self.total_samples_var.set(f"Tong so sample: {total}")

    def _get_question(self) -> str:
        return self.question_text.get("1.0", "end").strip()

    def _get_cypher(self) -> str:
        return self.cypher_text.get("1.0", "end").strip()

    def _get_source(self) -> str:
        return self.source_var.get().strip()

    def _get_source_id(self) -> str:
        return self.source_id_var.get().strip()

    def _set_cypher(self, value: str) -> None:
        self.cypher_text.delete("1.0", "end")
        self.cypher_text.insert("1.0", value)

    def _set_nodes_preview(self, value: str) -> None:
        self.nodes_preview.delete("1.0", "end")
        self.nodes_preview.insert("1.0", value)

    def _reset_form_fields(self) -> None:
        self.question_text.delete("1.0", "end")
        self.sample_id_var.set("")
        self.source_var.set("")
        self.source_id_var.set("")
        self.cypher_text.delete("1.0", "end")
        self.nodes_preview.delete("1.0", "end")
        self.nodes_data = []
        self._set_mode(None)

    def _set_mode(self, sample_id: Optional[int]) -> None:
        self.editing_sample_id = sample_id
        if not hasattr(self, "mode_var"):
            return

        if sample_id is None:
            if self.active_mode == "add":
                self.mode_var.set("Mode: Tao moi")
            else:
                self.mode_var.set("Mode: Edit (chua load sample)")
        else:
            self.mode_var.set(f"Mode: Edit id={sample_id}")

    def on_load_sample(self) -> None:
        sample_id_text = self.sample_id_var.get().strip()
        if not sample_id_text:
            messagebox.showwarning("Thieu thong tin", "Vui long nhap Sample ID.")
            return
        if not sample_id_text.isdigit():
            messagebox.showwarning("Du lieu khong hop le", "Sample ID phai la so nguyen duong.")
            return

        sample_id = int(sample_id_text)
        try:
            sample = get_sample_by_id(sample_id)
            if sample is None:
                messagebox.showwarning("Khong tim thay", f"Khong tim thay sample id={sample_id}.")
                return

            self.question_text.delete("1.0", "end")
            self.question_text.insert("1.0", str(sample.get("question", "")))
            self.source_var.set(str(sample.get("source", "")))
            self.source_id_var.set(str(sample.get("source_id", "")))
            self._set_cypher(str(sample.get("expected_cypher", "")))

            nodes = sample.get("nodes", [])
            if isinstance(nodes, list):
                self.nodes_data = cast(List[Dict[str, Any]], nodes)
            else:
                self.nodes_data = []

            self._set_nodes_preview(json.dumps(self.nodes_data, ensure_ascii=False, indent=2))
            self._set_mode(sample_id)
            self.status_var.set(f"Da load sample id={sample_id}.")
        except Exception as exc:
            self.status_var.set("Load sample that bai.")
            messagebox.showerror("Loi", str(exc))

    def on_exit_edit_mode(self) -> None:
        if self.active_mode != "edit":
            self._build_mode_selector()
            return

        self._set_mode(None)
        self.sample_id_var.set("")
        self.status_var.set("Da bo chon sample. Nhap ID khac de load tiep.")

    def on_generate_cypher(self) -> None:
        question = self._get_question()
        if not question:
            messagebox.showwarning("Thieu thong tin", "Vui long nhap question.")
            return

        try:
            self.status_var.set("Dang sinh expected_cypher...")
            self.root.update_idletasks()
            cypher = generate_expected_cypher(question)
            self._set_cypher(cypher)
            self.status_var.set("Da sinh expected_cypher thanh cong.")
        except Exception as exc:
            self.status_var.set("Sinh expected_cypher that bai.")
            messagebox.showerror("Loi", str(exc))

    def on_fetch_nodes(self) -> None:
        cypher = self._get_cypher()
        if not cypher:
            messagebox.showwarning("Thieu thong tin", "Vui long sinh hoac nhap expected_cypher truoc.")
            return

        try:
            self.status_var.set("Dang query Neo4j de lay nodes...")
            self.root.update_idletasks()
            self.nodes_data = query_nodes_from_cypher(cypher)
            preview = json.dumps(self.nodes_data, ensure_ascii=False, indent=2)
            self._set_nodes_preview(preview)
            self.status_var.set(f"Da lay {len(self.nodes_data)} dong nodes.")
        except Exception as exc:
            self.status_var.set("Lay nodes that bai.")
            messagebox.showerror("Loi", str(exc))

    def on_save(self) -> None:
        question = self._get_question()
        cypher = self._get_cypher()
        source = self._get_source()
        source_id = self._get_source_id()

        if not question:
            messagebox.showwarning("Thieu thong tin", "Vui long nhap question.")
            return
        if not cypher:
            messagebox.showwarning("Thieu thong tin", "Vui long sinh hoac nhap expected_cypher.")
            return

        if not self.nodes_data:
            proceed = messagebox.askyesno(
                "Nodes rong",
                "Danh sach nodes dang rong. Ban co muon luu van tiep tuc?",
            )
            if not proceed:
                return

        try:
            if self.active_mode == "add":
                new_id = append_to_dataset(question, cypher, self.nodes_data, source, source_id)
                self._reset_form_fields()
                self.status_var.set(f"Da luu vao dataset.py voi id={new_id}.")
                messagebox.showinfo("Thanh cong", f"Da them mau moi voi id={new_id}.")
            else:
                if self.editing_sample_id is None:
                    messagebox.showwarning("Thieu thong tin", "Edit mode yeu cau load Sample ID truoc khi luu.")
                    return
                updated_id = self.editing_sample_id
                update_sample_by_id(updated_id, question, cypher, self.nodes_data, source, source_id)
                self._reset_form_fields()
                self.status_var.set(f"Da cap nhat sample id={updated_id}.")
                messagebox.showinfo("Thanh cong", f"Da cap nhat sample id={updated_id}.")

            self._refresh_total_samples()
        except Exception as exc:
            self.status_var.set("Luu dataset that bai.")
            messagebox.showerror("Loi", str(exc))

    def on_clear(self) -> None:
        self._reset_form_fields()
        self.status_var.set("Da xoa form.")

    def open_table_view(self) -> None:
        try:
            DatasetTableView(
                parent=self.root,
                load_rows=list_samples_overview,
                delete_by_id=delete_sample_by_id,
                set_active=set_sample_active,
            )
            if hasattr(self, "status_var"):
                self.status_var.set("Da mo Table view.")
        except Exception as exc:
            if hasattr(self, "status_var"):
                self.status_var.set("Mo Table view that bai.")
            messagebox.showerror("Loi", str(exc))


def main() -> None:
    root = tk.Tk()
    app = DatasetToolUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
