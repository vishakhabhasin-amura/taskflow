from fpdf import FPDF
from datetime import date

TODAY = date.today().strftime("%d %B %Y")

class PDF(FPDF):
    def header(self):
        self.set_fill_color(30, 30, 50)
        self.rect(0, 0, 210, 18, 'F')
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_xy(0, 4)
        self.cell(0, 10, "TaskFlow  |  QA Report - Due Date Feature", align="C")
        self.set_text_color(0, 0, 0)
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Generated {TODAY}  *  Branch: pod_1_qa  *  Page {self.page_no()}", align="C")


def section(pdf, title):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(240, 242, 248)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 8, f"  {title}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def table_header(pdf, cols, widths):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(50, 60, 100)
    pdf.set_text_color(255, 255, 255)
    for col, w in zip(cols, widths):
        pdf.cell(w, 7, col, border=1, fill=True, align="C")
    pdf.ln()
    pdf.set_text_color(0, 0, 0)


pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_margins(14, 20, 14)

# Title block
pdf.ln(2)
pdf.set_font("Helvetica", "B", 20)
pdf.set_text_color(30, 30, 80)
pdf.cell(0, 10, "QA Test Report", ln=True, align="C")
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(90, 90, 90)
pdf.cell(0, 7, "Due Date Feature  *  Python Backend", ln=True, align="C")
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 6, f"Branch: pod_1_qa   |   Date: {TODAY}", ln=True, align="C")
pdf.set_text_color(0, 0, 0)
pdf.ln(6)

# Checklist
section(pdf, "Testing Checklist")
checklist = [
    ("1", "At least one test per acceptance criterion", True),
    ("2", "Edge case - task with no due date", True),
    ("3", "Edge case - task due exactly today", True),
    ("4", "All tests pass against the implementation", False),
    ("5", "PR description written", True),
]
widths = [12, 142, 28]
table_header(pdf, ["#", "Checklist Item", "Result"], widths)
for i, (num, item, passed) in enumerate(checklist):
    fill = i % 2 == 0
    pdf.set_fill_color(248, 249, 252) if fill else pdf.set_fill_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(12, 6, num, border=1, fill=fill, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(142, 6, item, border=1, fill=fill)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(34, 139, 34) if passed else pdf.set_text_color(200, 30, 30)
    pdf.cell(28, 6, "PASS" if passed else "FAIL", border=1, fill=fill, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln()

pdf.ln(3)
pdf.set_font("Helvetica", "I", 8)
pdf.set_text_color(120, 120, 120)
pdf.multi_cell(0, 5,
    "Item 4 fails because the implementation (models/task.py, routes/tasks.py) has not yet been updated "
    "to support due_date. The 6 failing tests expose a date format mismatch: the implementation returns "
    "a full ISO datetime with timezone (e.g. 2026-08-02T00:00:00+05:30) while the spec requires a plain "
    "YYYY-MM-DD string (Assumption A2). This is a bug in the implementation, not in the tests.")
pdf.set_text_color(0, 0, 0)
pdf.ln(4)

# Coverage by AC
section(pdf, "Test Coverage by Acceptance Criterion")
coverage = [
    ("AC-1", "Creating a task with / without a due date", "4", "PASS"),
    ("AC-2", "Adding a due date to an existing task via PATCH", "3", "PASS"),
    ("AC-3", "Due date immutability once set (incl. after completion)", "5", "PASS"),
    ("AC-4", "Sort order - ascending, null tasks last, insertion order preserved", "6", "PASS"),
    ("AC-5", "Colour indicators (red = overdue)", "0", "N/A"),
    ("AC-6", "due_date field present on all API responses", "3", "PASS"),
]
widths = [16, 112, 22, 32]
table_header(pdf, ["AC", "Description", "Tests", "Coverage"], widths)
for i, (ac, desc, count, status) in enumerate(coverage):
    fill = i % 2 == 0
    pdf.set_fill_color(248, 249, 252) if fill else pdf.set_fill_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(16, 6, ac, border=1, fill=fill, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(112, 6, desc, border=1, fill=fill)
    pdf.cell(22, 6, count, border=1, fill=fill, align="C")
    pdf.set_font("Helvetica", "B", 9)
    if status == "PASS": pdf.set_text_color(34, 139, 34)
    elif status == "FAIL": pdf.set_text_color(200, 30, 30)
    else: pdf.set_text_color(130, 130, 130)
    pdf.cell(32, 6, status, border=1, fill=fill, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln()

pdf.ln(3)
pdf.set_font("Helvetica", "I", 8)
pdf.set_text_color(120, 120, 120)
pdf.cell(0, 5, "AC-5 not tested - colour logic lives entirely in the frontend (public/app.js) and is not exercisable via the Flask test client.")
pdf.set_text_color(0, 0, 0)
pdf.ln(6)

# Test results
section(pdf, "Test Run Results  (21 tests)")
results = [
    ("test_create_task_with_due_date_returns_201_and_stored_date", "AC-1", "FAIL"),
    ("test_create_task_without_due_date_field_defaults_to_null", "AC-1", "PASS"),
    ("test_create_task_with_explicit_null_due_date_is_valid", "AC-1", "PASS"),
    ("test_create_task_with_due_date_preserves_title_and_completed_defaults", "AC-1", "FAIL"),
    ("test_patch_adds_due_date_to_undated_task", "AC-2", "FAIL"),
    ("test_patch_due_date_response_contains_all_task_fields", "AC-2", "FAIL"),
    ("test_patch_due_date_is_reflected_in_subsequent_get", "AC-2", "FAIL"),
    ("test_patch_due_date_rejected_when_already_set", "AC-3", "PASS"),
    ("test_patch_due_date_rejected_returns_correct_error_body", "AC-3", "PASS"),
    ("test_patch_due_date_rejected_even_when_same_value", "AC-3", "PASS"),
    ("test_patch_completed_does_not_modify_due_date", "AC-3", "FAIL"),
    ("test_patch_due_date_still_rejected_after_task_is_completed", "AC-3", "PASS"),
    ("test_get_tasks_sorted_by_due_date_ascending", "AC-4", "PASS"),
    ("test_get_tasks_null_due_dates_sorted_after_all_dated_tasks", "AC-4", "PASS"),
    ("test_get_tasks_null_group_preserves_insertion_order", "AC-4", "PASS"),
    ("test_get_tasks_overdue_task_appears_before_future_task", "AC-4", "PASS"),
    ("test_get_tasks_due_today_sorts_before_future_and_after_overdue", "AC-4", "PASS"),
    ("test_get_tasks_mixed_dated_and_undated_full_sort_order", "AC-4", "PASS"),
    ("test_create_task_response_always_includes_due_date_field", "AC-6", "PASS"),
    ("test_get_all_tasks_response_includes_due_date_on_every_task", "AC-6", "PASS"),
    ("test_patch_response_includes_due_date_field", "AC-6", "PASS"),
]
widths = [122, 22, 38]
table_header(pdf, ["Test Name", "AC", "Result"], widths)
for i, (name, ac, status) in enumerate(results):
    fill = i % 2 == 0
    pdf.set_fill_color(248, 249, 252) if fill else pdf.set_fill_color(255, 255, 255)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(122, 5, name, border=1, fill=fill)
    pdf.cell(22, 5, ac, border=1, fill=fill, align="C")
    pdf.set_text_color(34, 139, 34) if status == "PASS" else pdf.set_text_color(200, 30, 30)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(38, 5, status, border=1, fill=fill, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln()

pdf.ln(4)

# Known limitations
section(pdf, "Known Limitations")
pdf.set_font("Helvetica", "", 9)
for line in [
    "1.  Implementation pending - models/task.py and routes/tasks.py do not yet support due_date. All 6 failures are implementation gaps, not test design issues.",
    "2.  Date format bug - implementation returns full ISO datetime with timezone offset instead of plain YYYY-MM-DD string (Assumption A2 violation).",
    "3.  AC-5 (colour indicators) has no backend test. Colour logic is frontend-only and cannot be exercised via the Flask test client.",
    "4.  Open questions OQ-1 (colours for non-overdue tasks) and OQ-2 (sub-sort within overdue) are unresolved and may require additional tests once decided.",
]:
    pdf.multi_cell(0, 6, line)
    pdf.ln(1)

out = "/Users/rahulsiddharthdacha/Desktop/PersonalProjects/AmuraHealth/taskflow/QA_Report_Due_Dates.pdf"
pdf.output(out)
print(f"PDF saved: {out}")
