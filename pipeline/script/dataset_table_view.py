import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List


class DatasetTableView:
    def __init__(
        self,
        parent: tk.Tk,
        load_rows: Callable[[], List[Dict[str, Any]]],
        delete_by_id: Callable[[int], None],
        set_active: Callable[[int, bool], None],
    ) -> None:
        self.load_rows = load_rows
        self.delete_by_id = delete_by_id
        self.set_active = set_active

        self.window = tk.Toplevel(parent)
        self.window.title("Dataset Table View")
        self.window.geometry("1180x620")

        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.window, padding=12)
        container.pack(fill="both", expand=True)

        action_row = ttk.Frame(container)
        action_row.pack(fill="x", pady=(0, 8))

        ttk.Button(action_row, text="Refresh", command=self.refresh).pack(side="left")
        ttk.Button(action_row, text="Bat/Tat active", command=self.on_toggle_active_selected).pack(side="left", padx=(8, 0))
        ttk.Button(action_row, text="Xoa sample da chon", command=self.on_delete_selected).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="San sang.")
        ttk.Label(action_row, textvariable=self.status_var).pack(side="right")

        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "active", "question", "query")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("active", text="Active")
        self.tree.heading("question", text="Question")
        self.tree.heading("query", text="Query")

        self.tree.column("id", width=80, anchor="center", stretch=False)
        self.tree.column("active", width=90, anchor="center", stretch=False)
        self.tree.column("question", width=340, anchor="w", stretch=True)
        self.tree.column("query", width=620, anchor="w", stretch=True)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_show_details)

    def _truncate(self, text: Any, limit: int = 180) -> str:
        text_str = str(text or "")
        text_str = " ".join(text_str.split())
        if len(text_str) <= limit:
            return text_str
        return text_str[: limit - 3] + "..."

    def refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.load_rows()
        for row in rows:
            sample_id = row.get("id", "")
            is_active = bool(row.get("active", True))
            question = self._truncate(row.get("question", ""), limit=220)
            query = self._truncate(row.get("expected_cypher", ""), limit=300)

            self.tree.insert(
                "",
                "end",
                iid=str(sample_id),
                values=(sample_id, "True" if is_active else "False", question, query),
            )

        self.status_var.set(f"Tong so sample: {len(rows)}")

    def _get_selected_id(self) -> int:
        selected = self.tree.selection()
        if not selected:
            raise ValueError("Vui long chon mot dong trong bang.")

        iid = selected[0]
        if not iid.isdigit():
            raise ValueError("ID da chon khong hop le.")

        return int(iid)

    def _get_selected_active(self) -> bool:
        selected = self.tree.selection()
        if not selected:
            raise ValueError("Vui long chon mot dong trong bang.")

        values = self.tree.item(selected[0], "values")
        if len(values) < 2:
            return True

        raw = str(values[1]).strip().lower()
        return raw in {"true", "1", "yes", "y", "on"}

    def on_toggle_active_selected(self) -> None:
        try:
            sample_id = self._get_selected_id()
            current_active = self._get_selected_active()
        except Exception as exc:
            messagebox.showwarning("Chua chon dong", str(exc), parent=self.window)
            return

        next_active = not current_active
        try:
            self.set_active(sample_id, next_active)
            self.refresh()
            self.status_var.set(f"Da cap nhat active sample id={sample_id} -> {next_active}.")
            messagebox.showinfo(
                "Thanh cong",
                f"Sample id={sample_id} da duoc dat active={next_active}.",
                parent=self.window,
            )
        except Exception as exc:
            messagebox.showerror("Loi", str(exc), parent=self.window)

    def on_delete_selected(self) -> None:
        try:
            sample_id = self._get_selected_id()
        except Exception as exc:
            messagebox.showwarning("Chua chon dong", str(exc), parent=self.window)
            return

        confirmed = messagebox.askyesno(
            "Xac nhan xoa",
            f"Ban co chac chan muon xoa sample id={sample_id}?",
            parent=self.window,
        )
        if not confirmed:
            return

        try:
            self.delete_by_id(sample_id)
            self.refresh()
            self.status_var.set(f"Da xoa sample id={sample_id}.")
            messagebox.showinfo("Thanh cong", f"Da xoa sample id={sample_id}.", parent=self.window)
        except Exception as exc:
            messagebox.showerror("Loi", str(exc), parent=self.window)

    def on_show_details(self, _event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        if len(values) < 4:
            return

        sample_id, active, question, query = values
        messagebox.showinfo(
            f"Sample id={sample_id}",
            f"Active: {active}\n\nQuestion:\n{question}\n\nQuery:\n{query}",
            parent=self.window,
        )