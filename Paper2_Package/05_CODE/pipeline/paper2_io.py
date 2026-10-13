"""
paper2_io.py
------------
Shared output helper for Paper 2.

WHY
The required deliverables stay as CSVs, because that is what the plan names and
what a reviewer will open. The small tables that only support a claim in a
README do not each deserve a file -- one of them was a single row. Nine such
tables across three tasks is noise at the top level of a results folder, and it
buries the six files that actually matter.

They are collected instead into one workbook per task, one sheet each. Nothing
is lost and nothing stops being machine-readable; the sheet names are the names
the files used to have.

The project already uses this shape: Paper1_HighConfidence ships
12_KG_supplementary.xlsx with seven sheets.

Usage in a task script:

    from paper2_io import SupportingTables
    sup = SupportingTables("Paper2_Results/Task2", "task2")
    sup.add("action_breakdown", action_df)
    sup.add("mapping_sensitivity", sens_df)
    sup.write()
"""

import os

import pandas as pd

# Excel sheet names: 31 characters, and none of : \ / ? * [ ]
_BAD = ':\\/?*[]'
MAX_SHEET = 31


def _clean(name):
    for ch in _BAD:
        name = name.replace(ch, '-')
    return name[:MAX_SHEET]


class SupportingTables:
    """Collects the small tables of one task into a single .xlsx."""

    def __init__(self, out_dir, prefix):
        self.out_dir = out_dir
        self.path = os.path.join(out_dir, f"{prefix}_supporting.xlsx")
        self.tables = {}

    def add(self, sheet, df):
        sheet = _clean(sheet)
        if sheet in self.tables:
            raise ValueError(f"duplicate sheet name: {sheet}")
        self.tables[sheet] = df
        return df

    def write(self):
        """Merge into any existing workbook rather than replacing it.

        A task's supporting tables can come from more than one script -- Task 1's
        stage-mean verification is produced separately from its master table --
        and a plain write would silently drop whichever ran first.
        """
        if not self.tables:
            return None
        os.makedirs(self.out_dir, exist_ok=True)

        merged = {}
        if os.path.exists(self.path):
            merged.update(pd.read_excel(self.path, sheet_name=None))
        merged.update(self.tables)          # this run's tables win

        with pd.ExcelWriter(self.path, engine="openpyxl") as xl:
            for sheet, df in merged.items():
                df.to_excel(xl, sheet_name=sheet, index=False)
        self.tables = merged
        rows = sum(len(d) for d in self.tables.values())
        print(f"wrote {self.path}  ({len(self.tables)} sheets, {rows:,} rows)")
        return self.path
