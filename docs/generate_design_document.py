"""Generate the SPARC-PM software design document PDF."""

from pathlib import Path
import re
from textwrap import dedent

import cairosvg
import fitz


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs"
WIRE_DIR = OUTPUT_DIR / "wireframes"
PDF_PATH = OUTPUT_DIR / "SPARC_software_design_document.pdf"
ARCH_PATH = OUTPUT_DIR / "architecture_diagram_updated.svg"

PAGE_W, PAGE_H = 595, 842
NAVY = (0.03, 0.06, 0.12)
PANEL = (0.07, 0.11, 0.19)
CYAN = (0.18, 0.78, 0.98)
MUTED = (0.58, 0.67, 0.78)
WHITE = (0.94, 0.97, 1.0)
GREEN = (0.2, 0.9, 0.56)
AMBER = (1.0, 0.75, 0.15)


def architecture_svg() -> str:
    return dedent(
        """
        <svg xmlns="http://www.w3.org/2000/svg" width="1400" height="820" viewBox="0 0 1400 820">
          <rect width="1400" height="820" fill="#07101e"/>
          <text x="50" y="58" fill="#f1f7ff" font-family="Arial" font-size="28" font-weight="bold">SPARC-PM | Layered mission decision-support architecture</text>
          <text x="50" y="90" fill="#93a9c4" font-family="Arial" font-size="16">Runtime path: telemetry -&gt; feature/model engines -&gt; operational decisions -&gt; Streamlit mission-control views</text>
          <g font-family="Arial" font-size="17" fill="#f1f7ff" stroke="#2e455f" stroke-width="2">
            <rect x="50" y="140" width="250" height="530" rx="12" fill="#0e1c31"/>
            <rect x="350" y="140" width="310" height="530" rx="12" fill="#0e1c31"/>
            <rect x="710" y="140" width="300" height="530" rx="12" fill="#0e1c31"/>
            <rect x="1060" y="140" width="290" height="530" rx="12" fill="#0e1c31"/>
          </g>
          <g font-family="Arial" fill="#38d2ff" font-size="20" font-weight="bold">
            <text x="78" y="182">1. Ingest</text><text x="378" y="182">2. Domain engines</text>
            <text x="738" y="182">3. Decision layer</text><text x="1088" y="182">4. Mission UI</text>
          </g>
          <g font-family="Arial" font-size="16" fill="#f1f7ff">
            <text x="78" y="235">Aditya-L1 telemetry</text><text x="78" y="275">CSV / CDF fallback</text><text x="78" y="315">TLE JSON</text><text x="78" y="355">Fleet telemetry</text><text x="78" y="395">Scenario controls</text>
            <text x="378" y="235">Severity classifier</text><text x="378" y="275">Crew dosimetry</text><text x="378" y="315">Spatial hazard / SGP4</text><text x="378" y="355">Predictive maintenance</text><text x="378" y="395">Cached resources</text>
            <text x="738" y="235">FSM triage</text><text x="738" y="275">Risk profile</text><text x="738" y="315">A* command scheduler</text><text x="738" y="355">Power / cooldown limits</text><text x="738" y="395">HMAC-SHA256 frames</text>
            <text x="1088" y="235">Overview &amp; triage</text><text x="1088" y="275">Gaganyaan dosimetry</text><text x="1088" y="315">3D fleet hazard</text><text x="1088" y="355">Predictive maintenance</text><text x="1088" y="395">Command synthesizer</text><text x="1088" y="435">Incident analytics</text>
          </g>
          <g stroke="#38d2ff" stroke-width="4" fill="none" marker-end="url(#arrow)">
            <path d="M300 405 H350"/><path d="M660 405 H710"/><path d="M1010 405 H1060"/>
          </g>
          <g stroke="#20e68e" stroke-width="2" stroke-dasharray="8 8" fill="none"><path d="M1205 500 V735 H180 V670"/></g>
          <text x="530" y="760" fill="#20e68e" font-family="Arial" font-size="16">Operational feedback: status, latency, alerts, and signed command audit data return to the operator</text>
          <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#38d2ff"/></marker></defs>
        </svg>
        """
    ).strip()


def add_header(page: fitz.Page, title: str, page_no: int) -> None:
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, PAGE_H), color=NAVY, fill=NAVY)
    page.insert_text((38, 36), "SPARC-PM | SOFTWARE DESIGN DOCUMENT", fontsize=8, fontname="hebo", color=CYAN)
    page.insert_text((PAGE_W - 52, 36), f"{page_no:02d}", fontsize=8, fontname="hebo", color=MUTED)
    page.draw_line((38, 48), (PAGE_W - 38, 48), color=(0.14, 0.25, 0.36), width=0.8)
    page.insert_text((38, 78), title, fontsize=20, fontname="hebo", color=WHITE)


def text(page: fitz.Page, value: str, rect, size=10, color=WHITE, font="helv", align=0):
    page.insert_textbox(fitz.Rect(*rect), value, fontsize=size, fontname=font, color=color, align=align, lineheight=1.2)


def panel(page: fitz.Page, rect, fill=PANEL):
    page.draw_rect(fitz.Rect(*rect), color=(0.12, 0.22, 0.33), fill=fill, width=0.7)


def code_box(page: fitz.Page, rect, value: str):
    panel(page, rect, fill=(0.02, 0.04, 0.08))
    text(page, value, (rect[0] + 12, rect[1] + 12, rect[2] - 12, rect[3] - 10), size=7.2, color=(0.75, 0.9, 0.98), font="cour")


def render_wireframe(filename: str) -> bytes:
    source = (WIRE_DIR / filename).read_text(encoding="utf-8")
    source = source.replace("&bull;", "&#8226;")
    source = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", source)
    return cairosvg.svg2png(bytestring=source.encode("utf-8"), output_width=960)


def screen_page(doc: fitz.Document, page_no: int, title: str, filenames: list[str], captions: list[str]):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    add_header(page, title, page_no)
    page.insert_text((38, 104), "Updated wireframe screens generated from the repository's design artifacts.", fontsize=9, fontname="helv", color=MUTED)
    y = 128
    for filename, caption in zip(filenames, captions):
        png = render_wireframe(filename)
        page.insert_image(fitz.Rect(38, y, 557, y + 290), stream=png, keep_proportion=True)
        page.insert_text((38, y + 305), caption, fontsize=9, fontname="hebo", color=CYAN)
        y += 338


def build_pdf() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCH_PATH.write_text(architecture_svg(), encoding="utf-8")
    doc = fitz.open()

    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, PAGE_H), color=NAVY, fill=NAVY)
    page.draw_rect(fitz.Rect(38, 94, 557, 99), color=CYAN, fill=CYAN)
    text(page, "SPARC-PM", (38, 145, 557, 205), size=34, color=WHITE, font="hebo")
    text(page, "Software Design Document", (38, 210, 557, 260), size=24, color=CYAN, font="hebo")
    text(page, "Space Weather Risk Classification & Predictive Maintenance Engine", (38, 290, 540, 335), size=14, color=MUTED)
    text(page, "Design coverage: principles, architecture, interface design, implementation evidence, and key decisions", (38, 370, 540, 425), size=12, color=WHITE)
    panel(page, (38, 500, 557, 630), fill=PANEL)
    text(page, "Prepared for project review", (58, 530, 530, 555), size=12, color=CYAN, font="hebo")
    text(page, "Repository baseline: Streamlit mission-control dashboard\nDate: 11 September 2026\nScope: current implementation plus clearly marked production follow-ups", (58, 565, 530, 620), size=10, color=WHITE)
    text(page, "The design is intentionally operational: telemetry is transformed into explainable risk, crew guidance, fleet actions, and auditable commands.", (38, 720, 557, 770), size=11, color=GREEN)

    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    add_header(page, "1. Design principles applied", 2)
    text(page, "SPARC-PM separates scientific computation from operator presentation. This keeps the dashboard readable while allowing each algorithm to be tested and replaced independently.", (38, 105, 557, 150), size=10)
    principles = [
        ("Abstraction", "The dashboard consumes engine-level reports rather than reimplementing physics, model inference, or scheduling logic in UI code."),
        ("Modularity", "Severity, dosimetry, spatial hazard, maintenance, and scheduling are separate modules with focused responsibilities."),
        ("Cohesion", "Each engine owns its domain constants, transformations, thresholds, and output contract; related behavior stays together."),
        ("Low coupling", "The UI communicates through dictionaries/data frames and cached constructors, so an engine can change without changing all six views."),
        ("Operational safety", "Triage actions, power budgets, cooldowns, cryptographic signatures, and a manual override boundary are explicit concerns."),
    ]
    y = 178
    for heading, body in principles:
        panel(page, (38, y, 557, y + 72))
        text(page, heading, (54, y + 14, 175, y + 36), size=11, color=CYAN, font="hebo")
        text(page, body, (190, y + 12, 540, y + 58), size=9.2, color=WHITE)
        y += 84
    text(page, "Cheap validation check", (38, 620, 200, 645), size=11, color=AMBER, font="hebo")
    text(page, "A change to a model engine should be testable without launching Streamlit. The current module boundaries support that check; the remaining improvement is adding a formal automated test suite for the contracts.", (38, 650, 557, 705), size=10)

    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    add_header(page, "2. High-level architecture", 3)
    arch_png = cairosvg.svg2png(url=str(ARCH_PATH), output_width=1100)
    page.insert_image(fitz.Rect(38, 105, 557, 430), stream=arch_png, keep_proportion=True)
    text(page, "Architecture style: layered pipeline with a decision boundary", (38, 465, 557, 493), size=12, color=CYAN, font="hebo")
    text(page, "The layered style was chosen because the system has a directional flow from sensor data to decisions, while the decision layer must remain visibly distinct from presentation. It makes ownership, testing boundaries, and failure containment easy to discuss in a review.", (38, 505, 557, 555), size=10)
    text(page, "Runtime sequence", (38, 590, 200, 615), size=11, color=GREEN, font="hebo")
    text(page, "1. Ingest telemetry and TLE/fleet data.\n2. Normalize and derive physical features.\n3. Run specialist engines and cache stable resources.\n4. Apply FSM triage and A* prioritization.\n5. Present six operator views and signed/auditable command results.", (38, 625, 557, 725), size=10)

    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    add_header(page, "3. Implementation evidence", 4)
    text(page, "The following excerpts show how the architecture is expressed in code.", (38, 105, 557, 130), size=10, color=MUTED)
    code_box(page, (38, 150, 557, 286), dedent('''\n@st.cache_resource\ndef load_spatial_engine():\n    return SpatialHazardEngine()\n\n@st.cache_resource\ndef load_dosimetry_engine():\n    return CrewDosimetryEngine()\n\n@st.cache_resource\ndef load_action_scheduler():\n    return AStarActionScheduler()''').strip())
    text(page, "Resource caching reduces repeated model and fleet initialization during Streamlit reruns. It is a presentation-layer optimization that does not leak into domain logic.", (38, 305, 557, 360), size=9.5)
    code_box(page, (38, 390, 557, 552), dedent('''\ntelemetry_packet = {\n    "proton_flux_pfu": sim_flux,\n    "proton_speed_kms": sim_speed,\n    "mag_bz_field": sim_bz,\n    "proton_density_cm3": sim_density,\n    "solar_wind_dyn_pressure_npa": sim_pressure,\n}\n\nseverity_report = clf.predict_single(telemetry_packet)\nhazard_report = spatial_eng.evaluate_storm_hazards(\n    solar_wind_speed_kms=sim_speed,\n    bz_field_nt=sim_bz,\n    proton_flux_pfu=sim_flux,\n)''').strip())
    text(page, "The UI assembles one telemetry packet and delegates computation to engines. This is the main low-coupling seam in the implementation.", (38, 570, 557, 625), size=9.5)
    code_box(page, (38, 655, 557, 785), dedent('''\nscheduled_commands = scheduler.schedule_telecommands(\n    hazard_report["fleet_hazard_profile"],\n    fleet_maintenance\n)\n\ndosimetry_report = dosimetry_eng.forecast_6h_radiation_curve(\n    historical_flux_window, sim_speed, sim_bz\n)''').strip())

    screen_page(doc, 5, "4. User interface design | screens 1-2", ["01_executive_overview.svg", "02_gaganyaan_dosimetry.svg"], ["Screen 1: executive overview and triage", "Screen 2: Gaganyaan crew dosimetry"])
    screen_page(doc, 6, "4. User interface design | screens 3-4", ["03_3d_fleet_hazard.svg", "04_predictive_maintenance.svg"], ["Screen 3: 3D fleet spatial hazard", "Screen 4: predictive maintenance"])
    screen_page(doc, 7, "4. User interface design | screens 5-6", ["05_command_synthesizer.svg", "06_incident_analytics.svg"], ["Screen 5: command synthesizer and verification", "Screen 6: incident analytics and replay"])

    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    add_header(page, "5. Design decisions and usability rationale", 8)
    decisions = [
        ("Streamlit as the current shell", "It provides a fast, testable mission-control prototype with direct access to Python models and Plotly visualizations. A service/API split remains a future deployment decision."),
        ("Six task-oriented screens", "The tabs map to the operator workflow: orient, protect crew, inspect fleet, diagnose assets, authorize commands, and review incidents."),
        ("Severity color plus plain-language action", "Green/yellow/red status is paired with a concrete directive so the interface supports rapid scanning without forcing the operator to interpret a score."),
        ("Cached domain engines", "Models and fleet state are expensive or stateful resources; caching improves rerun behavior and keeps view code focused on composition."),
        ("Signed commands with constraints", "A* prioritization is bounded by power, cooldown, and command-count constraints, while HMAC-SHA256 provides an auditable integrity check."),
    ]
    y = 112
    for heading, body in decisions:
        panel(page, (38, y, 557, y + 86))
        text(page, heading, (54, y + 13, 540, y + 34), size=10.5, color=CYAN, font="hebo")
        text(page, body, (54, y + 42, 540, y + 76), size=9.3)
        y += 101
    text(page, "User-friendly interaction patterns", (38, 635, 300, 660), size=11, color=GREEN, font="hebo")
    text(page, "Persistent tab navigation, high-salience status banners, KPI cards, interactive Plotly charts, operator-controlled scenarios, explicit thresholds, and a visible audit/verification path reduce cognitive load during a simulated event.", (38, 672, 557, 730), size=10)
    text(page, "Known follow-ups", (38, 755, 180, 780), size=10.5, color=AMBER, font="hebo")
    text(page, "Production hardening should add automated contract tests, externalize the uplink secret, validate the real data-label ground truth, and decide whether the long-term frontend remains Streamlit or moves behind an API.", (180, 752, 557, 795), size=9)

    doc.save(PDF_PATH)
    print(f"Wrote {PDF_PATH} ({len(doc)} pages)")


if __name__ == "__main__":
    build_pdf()