from collections import Counter
from datetime import datetime, timezone
from textwrap import wrap

from app.schemas.report_generation import GenerateReportRequest, ReportFinding


def generate_scan_report_pdf(request: GenerateReportRequest) -> bytes:
    lines = _report_lines(request)
    pages = _paginate(lines, lines_per_page=42)
    return _build_pdf(pages)


def _report_lines(request: GenerateReportRequest) -> list[str]:
    findings = request.findings
    severity_counts = Counter(finding.severity.upper() for finding in findings)
    security_findings = [finding for finding in findings if finding.category.lower() in {"security", "secret"}]
    maintainability_findings = [
        finding for finding in findings if finding.category.lower() in {"quality", "maintainability", "static-analysis"}
    ]
    top_fixes = sorted(findings, key=_finding_priority)[:5]

    lines = [
        "CodePulse AI Repository Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Repository Summary",
        f"Repository: {request.repository_full_name}",
        f"URL: {request.repository_url}",
        f"Scan ID: {request.scan_id}",
        f"Status: {request.status}",
        f"Total Findings: {len(findings)}",
        "",
        "Health Score",
        f"Overall Quality: {_score(request.quality_score)}",
        f"Security: {_score(request.security_score)}",
        f"Maintainability: {_score(request.maintainability_score)}",
        "",
        "Finding Distribution",
        f"Critical: {severity_counts.get('CRITICAL', 0)}",
        f"High: {severity_counts.get('HIGH', 0)}",
        f"Medium: {severity_counts.get('MEDIUM', 0)}",
        f"Low: {severity_counts.get('LOW', 0)}",
        "",
        "Security Findings",
        *_finding_lines(security_findings[:10], "No security findings were included in this report."),
        "",
        "Maintainability Issues",
        *_finding_lines(maintainability_findings[:10], "No maintainability issues were included in this report."),
        "",
        "Technical Debt Summary",
        *_technical_debt_lines(findings),
        "",
        "Top 5 Recommended Fixes",
        *_recommended_fix_lines(top_fixes),
        "",
        "Estimated Refactor Effort",
        *_effort_lines(findings),
    ]

    return _wrap_lines(lines)


def _finding_lines(findings: list[ReportFinding], empty_message: str) -> list[str]:
    if not findings:
        return [empty_message]

    lines = []
    for finding in findings:
        location = f"{finding.file_path}:{finding.line_number or 1}"
        lines.append(f"- [{finding.severity.upper()}] {finding.title} ({location})")
        lines.append(f"  {finding.description}")
    return lines


def _technical_debt_lines(findings: list[ReportFinding]) -> list[str]:
    if not findings:
        return ["No technical debt was detected by the included scanners."]

    categories = Counter(finding.category.lower() for finding in findings)
    return [
        f"Total debt signals: {len(findings)}",
        f"Most common category: {categories.most_common(1)[0][0]}",
        f"Files affected: {len({finding.file_path for finding in findings})}",
        "Prioritize high-severity and repeated findings before broad refactors.",
    ]


def _recommended_fix_lines(findings: list[ReportFinding]) -> list[str]:
    if not findings:
        return ["No recommended fixes are required based on current findings."]

    lines = []
    for index, finding in enumerate(findings, start=1):
        recommendation = finding.recommendation or "Review the scanner guidance and update the affected code."
        lines.append(f"{index}. {finding.title} in {finding.file_path}:{finding.line_number or 1}")
        lines.append(f"   Action: {recommendation}")
    return lines


def _effort_lines(findings: list[ReportFinding]) -> list[str]:
    effort_points = sum({"CRITICAL": 8, "HIGH": 5, "MEDIUM": 2, "LOW": 1}.get(finding.severity.upper(), 1) for finding in findings)
    if effort_points == 0:
        estimate = "Low: less than 1 engineer-day."
    elif effort_points <= 15:
        estimate = "Moderate: 1-2 engineer-days."
    elif effort_points <= 40:
        estimate = "Elevated: 3-5 engineer-days."
    else:
        estimate = "High: more than 1 engineering week."

    return [
        f"Effort points: {effort_points}",
        estimate,
    ]


def _finding_priority(finding: ReportFinding) -> tuple[int, str]:
    return ({"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(finding.severity.upper(), 4), finding.file_path)


def _score(value: int | None) -> str:
    return "pending" if value is None else f"{value}/100"


def _wrap_lines(lines: list[str]) -> list[str]:
    wrapped = []
    for line in lines:
        if len(line) <= 92:
            wrapped.append(line)
            continue
        wrapped.extend(wrap(line, width=92, subsequent_indent="  "))
    return wrapped


def _paginate(lines: list[str], lines_per_page: int) -> list[list[str]]:
    return [lines[index:index + lines_per_page] for index in range(0, len(lines), lines_per_page)] or [[]]


def _build_pdf(pages: list[list[str]]) -> bytes:
    objects: list[bytes] = []
    page_object_numbers = []

    def add_object(content: bytes) -> int:
        objects.append(content)
        return len(objects)

    font_object = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page_lines in pages:
        content = _page_content(page_lines)
        content_object = add_object(
            b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream"
        )
        page_object_numbers.append((content_object, None))

    pages_object = len(objects) + len(page_object_numbers) + 1
    updated_page_numbers = []
    for content_object, _ in page_object_numbers:
        page_object = add_object(
            f"<< /Type /Page /Parent {pages_object} 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_object} 0 R >> >> /Contents {content_object} 0 R >>".encode("ascii")
        )
        updated_page_numbers.append(page_object)

    kids = " ".join(f"{page} 0 R" for page in updated_page_numbers)
    add_object(f"<< /Type /Pages /Kids [{kids}] /Count {len(updated_page_numbers)} >>".encode("ascii"))
    catalog_object = add_object(f"<< /Type /Catalog /Pages {pages_object} 0 R >>".encode("ascii"))

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_object} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF".encode("ascii")
    )
    return bytes(pdf)


def _page_content(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", "50 750 Td", "14 TL"]
    for index, line in enumerate(lines):
        if index == 0:
            commands.append(f"({_escape_pdf_text(line)}) Tj")
        else:
            commands.append(f"T* ({_escape_pdf_text(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
