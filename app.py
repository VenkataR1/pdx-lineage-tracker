"""
🧬 PDX Lineage Tracker
A Streamlit app for tracking Patient-Derived Xenograft mouse lineages,
drug regimens, and colony management.

Usage:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PDX Lineage Tracker v6",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp { background-color: #0a0e1a; }
    
    /* Global text brightness fix */
    .stApp, .stApp p, .stApp span, .stApp div, .stMarkdown {
        color: #e2e8f0 !important;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        color: #f1f5f9 !important;
    }
    .stApp strong, .stApp b {
        color: #ffffff !important;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #111827, #1e293b);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 12px;
        color: #cbd5e1 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Drug badges */
    .drug-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: 600;
        margin: 1px 2px;
    }
    .cycle-badge {
        display: inline-block;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 500;
        border: 1px solid;
        margin-left: 4px;
    }
    
    /* Lineage path */
    .lineage-path {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 16px;
        overflow-x: auto;
        white-space: nowrap;
    }
    .lineage-node {
        display: inline-block;
        background: #1e293b;
        border: 2px solid #334155;
        border-radius: 8px;
        padding: 8px 14px;
        margin: 0 4px;
        text-align: center;
        vertical-align: middle;
        font-size: 12px;
    }
    .lineage-node.selected {
        border-color: #38bdf8;
        box-shadow: 0 0 12px rgba(56,189,248,0.3);
    }
    .lineage-node.origin {
        border-color: #22c55e;
        background: #064e3b;
    }
    .lineage-arrow {
        display: inline-block;
        color: #475569;
        font-size: 18px;
        vertical-align: middle;
        margin: 0 2px;
    }
    
    /* Active indicator */
    .active-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
        margin-right: 6px;
    }
    
    /* Section headers */
    .section-header {
        font-size: 16px;
        font-weight: 700;
        color: #e2e8f0;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #1e293b;
    }
    
    /* Info grid */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 12px;
    }
    .info-item label {
        font-size: 10px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .info-item value {
        font-size: 13px;
        color: #f1f5f9;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar styling */
    .css-1d391kg { background-color: #111827; }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 8px 16px;
        color: #cbd5e1;
    }
    .stTabs [aria-selected="true"] {
        background-color: #38bdf8 !important;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# DRUG COLOR MAPPING
# ─────────────────────────────────────────────────────────────────
DRUG_COLORS = {
    "Double Dox + Dox Chow": {"bg": "#9f1239", "fg": "#fff", "label": "Dbl Dox + Chow"},
    "Double Dox":            {"bg": "#dc2626", "fg": "#fff", "label": "Double Dox"},
    "Dox Chow":              {"bg": "#ea580c", "fg": "#fff", "label": "Dox Chow"},
    "Dox":                   {"bg": "#ef4444", "fg": "#fff", "label": "Dox"},
    "CisEtop":               {"bg": "#2563eb", "fg": "#fff", "label": "CisEtop"},
    "CarbEtop":              {"bg": "#1d4ed8", "fg": "#fff", "label": "CarbEtop"},
    "MRTX1133":              {"bg": "#7c3aed", "fg": "#fff", "label": "MRTX1133"},
    "MRT1133":               {"bg": "#7c3aed", "fg": "#fff", "label": "MRTX1133"},
    "Tarla":                 {"bg": "#0891b2", "fg": "#fff", "label": "Tarlatamab"},
    "TPT":                   {"bg": "#059669", "fg": "#fff", "label": "Topotecan"},
    "Topo":                  {"bg": "#059669", "fg": "#fff", "label": "Topotecan"},
    "BCL201":                {"bg": "#d97706", "fg": "#fff", "label": "BCL201"},
    "S63845":                {"bg": "#b45309", "fg": "#fff", "label": "S63845"},
    "FHD286":                {"bg": "#be185d", "fg": "#fff", "label": "FHD286"},
    "FHD609":                {"bg": "#a21caf", "fg": "#fff", "label": "FHD609"},
    "RMC6236":               {"bg": "#4338ca", "fg": "#fff", "label": "RMC6236"},
    "6-Thio":                {"bg": "#065f46", "fg": "#fff", "label": "6-Thio-dG"},
    "OlaTMZ":                {"bg": "#92400e", "fg": "#fff", "label": "OlaTMZ"},
    "GSK503":                {"bg": "#1e3a5f", "fg": "#fff", "label": "GSK503"},
    "Ali":                   {"bg": "#5b21b6", "fg": "#fff", "label": "Alisertib"},
    "BRQ":                   {"bg": "#78350f", "fg": "#fff", "label": "BRQ"},
    "BrdU":                  {"bg": "#475569", "fg": "#fff", "label": "BrdU"},
    "IDP233":                {"bg": "#0e7490", "fg": "#fff", "label": "IDP233"},
    "IMPDHi":                {"bg": "#155e75", "fg": "#fff", "label": "IMPDHi"},
    "JIB-04":                {"bg": "#3f6212", "fg": "#fff", "label": "JIB-04"},
    "H151":                  {"bg": "#581c87", "fg": "#fff", "label": "H151/diABZI"},
    "diABZI":                {"bg": "#581c87", "fg": "#fff", "label": "diABZI"},
    "Chae":                  {"bg": "#7f1d1d", "fg": "#fff", "label": "Chaetomin"},
    "DCA":                   {"bg": "#365314", "fg": "#fff", "label": "DCA"},
    "Veh":                   {"bg": "#6b7280", "fg": "#fff", "label": "Vehicle"},
    "EduBrdu":               {"bg": "#475569", "fg": "#fff", "label": "EdU/BrdU"},
    "T cells":               {"bg": "#0d9488", "fg": "#fff", "label": "T cells"},
}


def get_drug_info(regimen, description=""):
    """Match a regimen/description to a drug color scheme."""
    if not regimen and not description:
        return None
    reg_str = str(regimen or "")
    text = f"{reg_str} {description or ''}"
    
    # Check for vehicle controls first (e.g. "MRTX1133_Veh", "FHD_Veh")
    if reg_str.lower().endswith("_veh") or reg_str.lower().startswith("veh_"):
        return DRUG_COLORS["Veh"]
    
    for key, val in DRUG_COLORS.items():
        if key.lower() in text.lower():
            return val
    if regimen:
        return {"bg": "#334155", "fg": "#fff", "label": reg_str.split("_")[0]}
    return None


def parse_drug_cycle(regimen):
    """Extract cycle information from regimen name."""
    if not regimen:
        return None
    lower = str(regimen).lower()
    patterns = [
        (r"_x(\d+)", lambda m: f"{m.group(1)}-cycle"),
        (r"(\d+)d\b", lambda m: f"{m.group(1)}-day"),
        (r"14d", lambda m: "14-day"),
        (r"time\.?course", lambda m: "Time course"),
        (r"biw", lambda m: "Twice weekly"),
        (r"mwf", lambda m: "Mon/Wed/Fri"),
        (r"[35]?q7", lambda m: "q7 cycle"),
        (r"daily", lambda m: "Daily"),
        (r"alt\b", lambda m: "Alternating"),
        (r"1\.dose", lambda m: "Single dose"),
    ]
    for pattern, formatter in patterns:
        match = re.search(pattern, lower)
        if match:
            return formatter(match)
    return None


def drug_badge_html(regimen, description="", show_cycle=False):
    """Generate HTML for a colored drug badge."""
    info = get_drug_info(regimen, description)
    if not info:
        return ""
    html = f'<span class="drug-badge" style="background:{info["bg"]};color:{info["fg"]}">{info["label"]}</span>'
    if show_cycle:
        cycle = parse_drug_cycle(regimen)
        if cycle:
            html += f'<span class="cycle-badge" style="border-color:{info["bg"]};color:{info["bg"]}">{cycle}</span>'
    return html


# ─────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(uploaded_file):
    """Parse the Excel file and return structured data."""
    
    # Read List sheet
    df_list = pd.read_excel(uploaded_file, sheet_name="List")
    df_list = df_list[df_list["Name"].notna()].copy()
    df_list["Name"] = df_list["Name"].astype(str).str.strip()
    
    # Clean parent column
    df_list["Parent"] = df_list["Parent"].apply(
        lambda x: str(x).strip() if pd.notna(x) else None
    )
    
    # Clean source type
    df_list["Source Type"] = df_list["Source Type"].apply(
        lambda x: str(x).strip().lower() if pd.notna(x) else None
    )
    
    # Read Measurements (active mice)
    try:
        df_meas = pd.read_excel(uploaded_file, sheet_name="Measurements", header=0)
        df_meas = df_meas[df_meas["Name"].notna()].copy()
        df_meas["Name"] = df_meas["Name"].astype(str).str.strip()
        active_mice = set(df_meas["Name"].unique())
    except Exception:
        df_meas = pd.DataFrame()
        active_mice = set()
    
    # Read New-To Do
    try:
        df_todo = pd.read_excel(uploaded_file, sheet_name="New-To Do")
    except Exception:
        df_todo = pd.DataFrame()
    
    # Read Regimens reference
    try:
        df_reg = pd.read_excel(uploaded_file, sheet_name="Regimens")
    except Exception:
        df_reg = pd.DataFrame()
    
    # Build lookup structures
    models = sorted(df_list["Model"].dropna().unique())
    regimens = sorted(df_list["Regimen"].dropna().unique())
    
    return df_list, df_meas, df_todo, df_reg, active_mice, models, regimens


def get_lineage(df, mouse_id):
    """Trace lineage back to cell line origin."""
    by_id = df.set_index("Name")
    lineage = []
    current = mouse_id
    visited = set()
    
    while current:
        if current in visited:
            break
        visited.add(current)
        
        if current not in by_id.index:
            break
        
        row = by_id.loc[current]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        
        lineage.insert(0, {
            "Name": current,
            "Model": row.get("Model"),
            "Psg": row.get("Psg"),
            "Parent": row.get("Parent"),
            "Source Type": row.get("Source Type"),
            "Regimen": row.get("Regimen"),
            "Description": row.get("Description"),
            "Days": row.get("Days"),
            "Implant": row.get("Implant"),
            "Dead/Xfer": row.get("Dead/Xfer"),
            "Location": row.get("Location"),
            "Modification": row.get("Modification"),
            "Notes and Future Plan": row.get("Notes and Future Plan"),
            "Problems": row.get("Problems"),
            "Start": row.get("Start"),
        })
        
        source = row.get("Source Type")
        if source and source in ("line", "cell line", "cell_line", "bx", "ctc", "stc"):
            break
        
        parent = row.get("Parent")
        if pd.isna(parent) or parent == "" or parent == "None":
            break
        
        current = parent
    
    return pd.DataFrame(lineage)


def get_descendants(df, mouse_id):
    """Find all descendants of a mouse."""
    children_map = {}
    for _, row in df.iterrows():
        parent = row.get("Parent")
        if parent and pd.notna(parent):
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(row["Name"])
    
    result = []
    queue = [mouse_id]
    visited = {mouse_id}
    
    while queue:
        curr = queue.pop(0)
        for child in children_map.get(curr, []):
            if child not in visited:
                visited.add(child)
                result.append(child)
                queue.append(child)
    
    return result


def extract_cycles(regimen, description=""):
    """Extract number of drug cycles from regimen name and description.
    
    Handles formats like:
      - CisEtop_7_10_x2 → 2 cycles
      - CisEtop_time.course with description containing x1, x2, x3, x4 → max = 4
      - OT_100_25_x1 → 1 cycle (will be skipped in cumulative count)
    """
    reg = str(regimen) if pd.notna(regimen) else ""
    desc = str(description) if pd.notna(description) else ""
    
    if not reg or reg == "nan":
        return 0, None
    
    # From regimen name: CisEtop_7_10_x2 → 2
    match = re.search(r"_x(\d+)", reg)
    if match:
        drug_name = reg[:match.start()]
        return int(match.group(1)), drug_name
    
    # Time course: parse description for max cycle number
    if "time" in reg.lower() or "course" in reg.lower():
        xs = re.findall(r"_x(\d+)", desc)
        if xs:
            max_cycle = max(int(x) for x in xs)
            drug_match = re.search(r"(CisEtop_\d+_\d+|CarbEtop_\d+_\d+|OlaTMZ|TPT[^;]*)", desc)
            drug = drug_match.group(1) if drug_match else reg
            return max_cycle, drug
    
    return 0, None


def get_cumulative_cycles(df, mouse_id, min_cycles=2):
    """Trace lineage and sum drug cycles, skipping single-cycle (x1) treatments.
    
    Returns:
        chain: list of dicts with lineage info and per-node cycle counts
        total_cycles: cumulative cycle count (only counting >= min_cycles)
        drugs_seen: dict of drug → total cycles for that drug
    """
    by_id = df.set_index("Name")
    chain = []
    current = mouse_id
    visited = set()
    
    while current:
        if current in visited:
            break
        visited.add(current)
        if current not in by_id.index:
            break
        
        row = by_id.loc[current]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        
        reg = row.get("Regimen") if pd.notna(row.get("Regimen")) else None
        desc = row.get("Description") if pd.notna(row.get("Description")) else None
        src = row.get("Source Type")
        psg = row.get("Psg")
        
        cycles, drug = extract_cycles(reg, desc)
        counted = cycles >= min_cycles
        
        chain.insert(0, {
            "Name": current,
            "Source Type": src,
            "Psg": psg,
            "Regimen": reg,
            "Description": desc,
            "Cycles": cycles,
            "Drug": drug,
            "Counted": counted,
            "Days": row.get("Days"),
        })
        
        if src and src in ("line", "cell line", "cell_line", "bx", "ctc", "stc"):
            break
        parent = row.get("Parent")
        if pd.isna(parent) or parent in ("", "None"):
            break
        current = parent
    
    total_cycles = sum(c["Cycles"] for c in chain if c["Counted"])
    
    drugs_seen = {}
    for c in chain:
        if c["Counted"] and c["Drug"]:
            drugs_seen[c["Drug"]] = drugs_seen.get(c["Drug"], 0) + c["Cycles"]
    
    return chain, total_cycles, drugs_seen


def build_tree_graph(df, mouse_id, active_mice):
    """Build a clean top-down hierarchical tree with arrows."""
    lineage_df = get_lineage(df, mouse_id)
    descendants = get_descendants(df, mouse_id)

    # Collect all nodes: ancestors + selected + descendants (capped)
    all_ids = list(dict.fromkeys(
        lineage_df["Name"].tolist() + [mouse_id] + descendants[:50]
    ))

    by_id = df.set_index("Name")

    # Build parent→children map for nodes in the tree
    children_map = {}   # parent_id → [child_id, ...]
    parent_map = {}     # child_id → parent_id
    id_set = set(all_ids)
    for mid in all_ids:
        if mid in by_id.index:
            row = by_id.loc[mid]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            parent = row.get("Parent")
            if parent and pd.notna(parent) and parent in id_set:
                parent_map[mid] = parent
                children_map.setdefault(parent, []).append(mid)

    # Find root(s): nodes with no parent in the set
    roots = [n for n in all_ids if n not in parent_map]
    if not roots:
        return None

    # ── Hierarchical layout: assign (x, y) per node ──
    # y = depth (top to bottom), x = spread children evenly
    ROW_HEIGHT = 1.0
    NODE_SPACING = 1.0

    pos = {}
    node_depth = {}

    def _subtree_width(node):
        """Count leaf-span of subtree for spacing."""
        kids = children_map.get(node, [])
        if not kids:
            return 1
        return sum(_subtree_width(k) for k in kids)

    def _layout(node, depth, x_start):
        """Recursively assign positions top-down."""
        node_depth[node] = depth
        kids = children_map.get(node, [])
        if not kids:
            pos[node] = (x_start, -depth * ROW_HEIGHT)
            return x_start + NODE_SPACING

        # Lay out children first to figure out span
        x_cursor = x_start
        for kid in kids:
            x_cursor = _layout(kid, depth + 1, x_cursor)

        # Center parent above its children
        child_xs = [pos[k][0] for k in kids]
        parent_x = (min(child_xs) + max(child_xs)) / 2
        pos[node] = (parent_x, -depth * ROW_HEIGHT)
        return x_cursor

    # Layout each root
    x_cursor = 0
    for root in roots:
        x_cursor = _layout(root, 0, x_cursor)
        x_cursor += NODE_SPACING  # gap between disconnected subtrees

    if not pos:
        return None

    # ── Determine which nodes are on the lineage path ──
    lineage_ids = set(lineage_df["Name"].tolist())

    # ── Build figure ──
    fig = go.Figure()

    # Draw edges as lines with arrowhead annotations
    for parent_node, kids in children_map.items():
        if parent_node not in pos:
            continue
        px_coord, py_coord = pos[parent_node]
        for kid in kids:
            if kid not in pos:
                continue
            cx, cy = pos[kid]

            # Is this edge on the lineage path?
            on_lineage = parent_node in lineage_ids and kid in lineage_ids

            # Vertical connector: parent down to mid-y, then horizontal to child x, then down
            mid_y = (py_coord + cy) / 2

            # Draw as an L-shaped path: straight down from parent, horizontal, straight down to child
            fig.add_trace(go.Scatter(
                x=[px_coord, px_coord, cx, cx],
                y=[py_coord, mid_y, mid_y, cy],
                mode="lines",
                line=dict(
                    width=2.5 if on_lineage else 1.5,
                    color="#38bdf8" if on_lineage else "#334155",
                ),
                hoverinfo="none",
                showlegend=False,
            ))

            # Arrowhead at the child end — small and clean
            fig.add_annotation(
                x=cx, y=cy,
                ax=cx, ay=cy + ROW_HEIGHT * 0.12,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=0.8,
                arrowwidth=1.5 if on_lineage else 1,
                arrowcolor="#38bdf8" if on_lineage else "#475569",
            )

    # Draw passage-level labels on the left
    depths_used = sorted(set(node_depth.values()))
    min_x = min(p[0] for p in pos.values()) - NODE_SPACING * 1.5
    for d in depths_used:
        # Find any node at this depth to get a passage number
        sample_node = next((n for n, dd in node_depth.items() if dd == d), None)
        if sample_node and sample_node in by_id.index:
            row = by_id.loc[sample_node]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            src = row.get("Source Type")
            psg = row.get("Psg")
            if src and src in ("line", "bx", "ctc", "stc"):
                depth_label = f"Origin ({src})"
            elif pd.notna(psg):
                depth_label = f"P{int(psg)}"
            else:
                depth_label = f"Level {d}"
        else:
            depth_label = f"Level {d}"

        fig.add_annotation(
            x=min_x, y=-d * ROW_HEIGHT,
            text=f"<b>{depth_label}</b>",
            showarrow=False,
            font=dict(size=11, color="#cbd5e1"),
            xanchor="right",
        )

    # Draw nodes
    for node in all_ids:
        if node not in pos:
            continue
        nx_coord, ny_coord = pos[node]

        # Get node metadata
        regimen = None
        source_type = None
        days = None
        if node in by_id.index:
            row = by_id.loc[node]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            regimen = row.get("Regimen") if pd.notna(row.get("Regimen")) else None
            source_type = row.get("Source Type")
            days = row.get("Days") if pd.notna(row.get("Days")) else None

        # Determine color and emphasis
        is_selected = node == mouse_id
        is_on_lineage = node in lineage_ids
        is_origin = source_type in ("line", "bx", "ctc", "stc")
        is_active = node in active_mice
        drug_info = get_drug_info(regimen)

        if is_selected:
            color = "#38bdf8"
            size = 22
            border_color = "#0ea5e9"
        elif is_origin:
            color = "#22c55e"
            size = 20
            border_color = "#16a34a"
        elif drug_info:
            color = drug_info["bg"]
            size = 16
            border_color = drug_info["bg"]
        elif is_active:
            color = "#22c55e"
            size = 14
            border_color = "#22c55e"
        elif is_on_lineage:
            color = "#64748b"
            size = 16
            border_color = "#38bdf8"
        else:
            color = "#475569"
            size = 12
            border_color = "#334155"

        # Short label
        short = node.split("_")[-1] if "_" in node else node

        # Hover text
        hover_lines = [f"<b>{node}</b>"]
        if source_type:
            hover_lines.append(f"Source: {source_type}")
        if regimen:
            hover_lines.append(f"Drug: {regimen}")
            cycle = parse_drug_cycle(regimen)
            if cycle:
                hover_lines.append(f"Cycle: {cycle}")
        if days:
            hover_lines.append(f"Days: {int(days)}")
        if is_active:
            hover_lines.append("🟢 Active")
        hover = "<br>".join(hover_lines)

        fig.add_trace(go.Scatter(
            x=[nx_coord], y=[ny_coord],
            mode="markers",
            marker=dict(
                size=size,
                color=color,
                line=dict(width=3 if is_selected else 2, color=border_color),
                symbol="diamond" if is_origin else "circle",
            ),
            hovertext=hover,
            hoverinfo="text",
            showlegend=False,
        ))

        # Node name label — placed to the right to avoid overlap
        fig.add_annotation(
            x=nx_coord,
            y=ny_coord + ROW_HEIGHT * 0.18,
            text=f"<b>{short}</b>",
            showarrow=False,
            font=dict(
                size=11 if is_selected else 10,
                color="#ffffff" if is_selected else ("#e2e8f0" if is_on_lineage else "#cbd5e1"),
                family="monospace",
            ),
            yanchor="bottom",
        )

        # Drug label below node (for drugged nodes)
        if drug_info and regimen:
            fig.add_annotation(
                x=nx_coord,
                y=ny_coord - ROW_HEIGHT * 0.2,
                text=f"<b>{drug_info['label']}</b>",
                showarrow=False,
                font=dict(size=9, color="#e2e8f0"),
                yanchor="top",
                bgcolor=drug_info["bg"],
                borderpad=2,
                opacity=0.9,
            )

    # ── Legend ──
    max_x = max(p[0] for p in pos.values()) + NODE_SPACING * 2
    max_y = max(p[1] for p in pos.values())
    legend_items = [
        ("🔵 Selected", "#38bdf8"),
        ("◆ Origin", "#22c55e"),
        ("— Lineage path", "#38bdf8"),
        ("🟢 Active", "#22c55e"),
        ("● Untreated", "#475569"),
    ]
    for i, (label, color) in enumerate(legend_items):
        fig.add_annotation(
            x=max_x,
            y=max_y - i * ROW_HEIGHT * 0.35,
            text=f'<span style="color:{color}">●</span> {label}',
            showarrow=False,
            font=dict(size=9, color="#e2e8f0"),
            xanchor="left",
        )

    # Layout
    all_x = [p[0] for p in pos.values()]
    all_y = [p[1] for p in pos.values()]
    x_pad = NODE_SPACING * 2
    y_pad = ROW_HEIGHT * 0.8

    fig.update_layout(
        showlegend=False,
        plot_bgcolor="#0a0e1a",
        paper_bgcolor="#0a0e1a",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[min(all_x) - x_pad, max(all_x) + x_pad + NODE_SPACING * 4],
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[min(all_y) - y_pad, max(all_y) + y_pad],
            scaleanchor="x", scaleratio=1,
        ),
        height=max(350, len(depths_used) * 120 + 100),
    )

    return fig


# ─────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────

# Header
st.markdown("# 🧬 PDX Lineage Tracker")

# File upload
uploaded_file = st.sidebar.file_uploader(
    "📁 Upload Mouse Directory Excel",
    type=["xlsx", "xls"],
    help="Upload your weekly-updated Mouse Directory Excel file. "
         "The app reads from List, Measurements, and New-To Do tabs."
)

if not uploaded_file:
    st.info(
        "👋 **Welcome!** Upload your Mouse Directory Excel file in the sidebar to get started.\n\n"
        "This app supports dynamic weekly updates — just upload the latest file each time.\n\n"
        "**Features:**\n"
        "- 🔍 Search & filter across all mice\n"
        "- 🌳 Full lineage tracing back to cell line origin\n"
        "- 💊 Drug regimen color coding with cycle detection\n"
        "- 📊 Colony statistics & model overview\n"
        "- 📋 Active mice from Measurements tab\n"
        "- 📥 CSV export for lineage data"
    )
    st.stop()

# Load data
with st.spinner("Parsing Excel file..."):
    df_list, df_meas, df_todo, df_reg, active_mice, models, regimens = load_data(uploaded_file)

# Sidebar stats
st.sidebar.markdown("---")
st.sidebar.markdown(f"**📊 Data Loaded**")
st.sidebar.markdown(f"- 🐁 **{len(df_list)}** total mice")
st.sidebar.markdown(f"- 🟢 **{len(active_mice)}** active")
st.sidebar.markdown(f"- 🧬 **{len(models)}** models")
st.sidebar.markdown(f"- 💊 **{len(regimens)}** regimens")

# Navigation tabs
tab_search, tab_lineage, tab_active, tab_cycles, tab_stats = st.tabs([
    "🔍 Search & Filter",
    "🌳 Lineage Tracker",
    "📋 Active Mice",
    "🔄 Cycle Counter",
    "📊 Colony Stats",
])


# ─────────────────────────────────────────────────────────────────
# TAB 1: SEARCH & FILTER
# ─────────────────────────────────────────────────────────────────
with tab_search:
    
    col_search, col_model, col_reg, col_active = st.columns([3, 2, 2, 1])
    
    with col_search:
        search = st.text_input(
            "🔍 Search",
            placeholder="Mouse ID, model, regimen, or description...",
            label_visibility="collapsed",
        )
    with col_model:
        model_filter = st.selectbox("Model", ["All Models"] + models, label_visibility="collapsed")
    with col_reg:
        reg_filter = st.selectbox("Regimen", ["All Regimens"] + regimens, label_visibility="collapsed")
    with col_active:
        active_only = st.checkbox("Active only", value=False)
    
    # Filter
    filtered = df_list.copy()
    if search:
        s = search.lower()
        mask = (
            filtered["Name"].str.lower().str.contains(s, na=False) |
            filtered["Model"].astype(str).str.lower().str.contains(s, na=False) |
            filtered["Regimen"].astype(str).str.lower().str.contains(s, na=False) |
            filtered["Description"].astype(str).str.lower().str.contains(s, na=False)
        )
        filtered = filtered[mask]
    if model_filter != "All Models":
        filtered = filtered[filtered["Model"] == model_filter]
    if reg_filter != "All Regimens":
        filtered = filtered[filtered["Regimen"] == reg_filter]
    if active_only:
        filtered = filtered[filtered["Name"].isin(active_mice)]
    
    st.markdown(f"**{len(filtered)}** mice found")
    
    # Display table
    display_df = filtered[["Name", "Model", "Psg", "Source Type", "Regimen", "Days", "Dead/Xfer", "Location"]].head(300).copy()
    display_df["Active"] = display_df["Name"].apply(lambda x: "🟢" if x in active_mice else "")
    display_df = display_df[["Active", "Name", "Model", "Psg", "Source Type", "Regimen", "Days", "Dead/Xfer", "Location"]]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Active": st.column_config.TextColumn("", width=30),
            "Name": st.column_config.TextColumn("Mouse ID", width=220),
            "Psg": st.column_config.NumberColumn("P", width=40),
            "Days": st.column_config.NumberColumn("Days", width=60),
        }
    )
    
    if len(filtered) > 300:
        st.caption("Showing first 300 results. Refine your search for more specific results.")


# ─────────────────────────────────────────────────────────────────
# TAB 2: LINEAGE TRACKER
# ─────────────────────────────────────────────────────────────────
with tab_lineage:
    
    col_sel, col_btn = st.columns([4, 1])
    with col_sel:
        mouse_options = sorted(df_list["Name"].unique())
        selected_mouse = st.selectbox(
            "Select Mouse",
            options=mouse_options,
            index=None,
            placeholder="Type or select a mouse ID...",
        )
    
    if selected_mouse:
        # Get mouse data
        mouse_data = df_list[df_list["Name"] == selected_mouse]
        if not mouse_data.empty:
            mouse_row = mouse_data.iloc[0]
            
            # ── Mouse Detail Card ──
            st.markdown("---")
            
            header_cols = st.columns([3, 1])
            with header_cols[0]:
                status_icon = "🟢" if selected_mouse in active_mice else "⚪"
                st.markdown(f"### {status_icon} {selected_mouse}")
                
                # Tags
                tags = []
                if pd.notna(mouse_row.get("Model")):
                    tags.append(f"`{mouse_row['Model']}`")
                if pd.notna(mouse_row.get("Psg")):
                    tags.append(f"`P{int(mouse_row['Psg'])}`")
                if pd.notna(mouse_row.get("Source Type")):
                    tags.append(f"`{mouse_row['Source Type']}`")
                if selected_mouse in active_mice:
                    tags.append("`🟢 Active`")
                st.markdown(" ".join(tags))
            
            with header_cols[1]:
                regimen = mouse_row.get("Regimen")
                if pd.notna(regimen):
                    badge = drug_badge_html(regimen, mouse_row.get("Description", ""), show_cycle=True)
                    st.markdown(badge, unsafe_allow_html=True)
            
            # Details grid
            detail_cols = st.columns(4)
            details = [
                ("Parent", mouse_row.get("Parent")),
                ("Location", mouse_row.get("Location")),
                ("Implant Date", mouse_row.get("Implant")),
                ("Dead/Xfer", mouse_row.get("Dead/Xfer")),
                ("Days", mouse_row.get("Days")),
                ("Regimen Start", mouse_row.get("Start")),
                ("Modification", mouse_row.get("Modification")),
                ("Source", mouse_row.get("Source Type")),
            ]
            for i, (label, val) in enumerate(details):
                if pd.notna(val) and str(val) != "None":
                    with detail_cols[i % 4]:
                        st.caption(label)
                        st.markdown(f"**{val}**")
            
            # Description & Notes
            if pd.notna(mouse_row.get("Description")):
                st.caption("Description")
                st.markdown(f"> {mouse_row['Description']}")
            if pd.notna(mouse_row.get("Notes and Future Plan")):
                st.caption("Notes & Future Plan")
                st.markdown(f"> {mouse_row['Notes and Future Plan']}")
            if pd.notna(mouse_row.get("Problems")):
                st.caption("⚠️ Problems")
                st.error(str(mouse_row["Problems"]))
            
            # ── Lineage Path ──
            st.markdown("---")
            lineage_df = get_lineage(df_list, selected_mouse)
            
            st.markdown(f"### 🌳 Lineage Path ({len(lineage_df)} generations)")
            
            # Visual lineage path
            path_parts = []
            for _, row in lineage_df.iterrows():
                name = row["Name"]
                short = name.split("_")[-1] if "_" in name else name
                source = row.get("Source Type", "")
                
                css_class = "lineage-node"
                if name == selected_mouse:
                    css_class += " selected"
                elif source in ("line", "bx", "ctc"):
                    css_class += " origin"
                
                drug_html = drug_badge_html(row.get("Regimen"), row.get("Description", ""))
                extra = f"<br>{drug_html}" if drug_html else ""
                
                path_parts.append(
                    f'<span class="{css_class}">'
                    f'<div style="font-size:10px;color:#cbd5e1">P{int(row["Psg"]) if pd.notna(row.get("Psg")) else "?"}</div>'
                    f'<div style="font-weight:700;color:#f1f5f9">{short}</div>'
                    f'{extra}'
                    f'</span>'
                )
            
            path_html = '<span class="lineage-arrow"> → </span>'.join(path_parts)
            st.markdown(f'<div class="lineage-path">{path_html}</div>', unsafe_allow_html=True)
            
            # Lineage tree visualization
            st.markdown("#### 🌲 Lineage Tree")
            fig = build_tree_graph(df_list, selected_mouse, active_mice)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Lineage detail table
            st.markdown("#### 📋 Lineage Details")
            lineage_display = lineage_df[["Name", "Source Type", "Regimen", "Days", "Implant", "Dead/Xfer"]].copy()
            lineage_display.insert(0, "Gen", range(len(lineage_display)))
            lineage_display["Drug"] = lineage_display["Regimen"].apply(
                lambda r: get_drug_info(r)["label"] if get_drug_info(r) else "—"
            )
            lineage_display["Cycle"] = lineage_display["Regimen"].apply(
                lambda r: parse_drug_cycle(r) or "—"
            )
            st.dataframe(lineage_display, use_container_width=True, hide_index=True)
            
            # Descendants
            desc_list = get_descendants(df_list, selected_mouse)
            if desc_list:
                st.markdown(f"#### 🔽 Descendants ({len(desc_list)})")
                desc_df = df_list[df_list["Name"].isin(desc_list)][
                    ["Name", "Model", "Psg", "Regimen", "Days", "Dead/Xfer"]
                ].copy()
                desc_df["Active"] = desc_df["Name"].apply(lambda x: "🟢" if x in active_mice else "")
                desc_df["Drug"] = desc_df["Regimen"].apply(
                    lambda r: get_drug_info(r)["label"] if get_drug_info(r) else ""
                )
                st.dataframe(desc_df, use_container_width=True, hide_index=True)
            
            # Download
            st.download_button(
                "📥 Download Lineage CSV",
                lineage_df.to_csv(index=False),
                file_name=f"{selected_mouse}_lineage.csv",
                mime="text/csv",
            )
    else:
        st.markdown(
            '<div style="text-align:center;padding:60px;color:#cbd5e1">'
            '<div style="font-size:48px;margin-bottom:12px">🌳</div>'
            '<div>Select a mouse above to view its lineage</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────
# TAB 3: ACTIVE MICE
# ─────────────────────────────────────────────────────────────────
with tab_active:
    
    if not df_meas.empty:
        st.markdown(f"### 📋 Active Mice from Measurements ({len(df_meas)} mice)")
        
        # Summary by regimen
        if "Regimen" in df_meas.columns:
            reg_counts = df_meas["Regimen"].dropna().value_counts()
            if len(reg_counts) > 0:
                st.markdown("#### 💊 Active Regimens")
                
                reg_cols = st.columns(min(len(reg_counts), 4))
                for i, (reg, count) in enumerate(reg_counts.items()):
                    info = get_drug_info(reg)
                    color = info["bg"] if info else "#334155"
                    with reg_cols[i % len(reg_cols)]:
                        st.markdown(
                            f'<div class="metric-card">'
                            f'<div class="metric-value" style="color:{color}">{count}</div>'
                            f'<div class="metric-label">{reg}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
        
        st.markdown("---")
        
        # Active mice table with measurements
        display_cols = [c for c in ["Name", "Days", "Length", "Width", "Regimen", "Description", "Notes and Future Plan"] if c in df_meas.columns]
        
        active_display = df_meas[display_cols].copy()
        
        # Calculate tumor volume if L and W available
        if "Length" in active_display.columns and "Width" in active_display.columns:
            active_display["TV (mm³)"] = (
                active_display["Length"] * active_display["Width"] ** 2 / 2
            ).round(1)
        
        st.dataframe(active_display, use_container_width=True, hide_index=True, height=500)
        
        # Tumor volume chart for drugged mice
        if "TV (mm³)" in active_display.columns and "Regimen" in active_display.columns:
            drugged = active_display[active_display["Regimen"].notna()].copy()
            if not drugged.empty:
                st.markdown("#### 📈 Tumor Volume by Regimen (Active Mice)")
                
                fig = px.box(
                    drugged,
                    x="Regimen",
                    y="TV (mm³)",
                    color="Regimen",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    points="all",
                )
                fig.update_layout(
                    plot_bgcolor="#0a0e1a",
                    paper_bgcolor="#0a0e1a",
                    font_color="#cbd5e1",
                    showlegend=False,
                    height=400,
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No Measurements sheet found in the uploaded file.")
    
    # New-To Do section
    if not df_todo.empty:
        st.markdown("---")
        st.markdown("### 📝 Weekly To-Do")
        
        # Clean and show to-do items
        todo_clean = df_todo.dropna(how="all")
        if not todo_clean.empty:
            # Find rows with actual mouse names (column index 4 typically)
            name_col = None
            for col in todo_clean.columns:
                vals = todo_clean[col].dropna().astype(str)
                if any("_p" in v for v in vals):
                    name_col = col
                    break
            
            if name_col:
                todo_with_mice = todo_clean[todo_clean[name_col].notna()].copy()
                if not todo_with_mice.empty:
                    st.dataframe(todo_with_mice.head(30), use_container_width=True, hide_index=True)
            else:
                st.dataframe(todo_clean.head(30), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────
# TAB 4: CYCLE COUNTER
# ─────────────────────────────────────────────────────────────────
with tab_cycles:
    
    st.markdown("### 🔄 Cumulative Drug Cycle Counter")
    st.markdown(
        "Track the **total number of drug cycles** a mouse's lineage has received. "
        "Cycles are summed along the entire ancestor chain back to origin. "
        "Single-cycle treatments (x1) are **skipped** — only x2 or more count as a real dosage."
    )
    
    st.markdown("---")
    
    # Model selector
    col_model_sel, col_mouse_sel = st.columns([1, 2])
    
    # Get models that have drugged mice
    drugged_models = sorted(
        df_list[df_list["Regimen"].notna()]["Model"].dropna().unique()
    )
    
    with col_model_sel:
        cycle_model = st.selectbox(
            "Select Model",
            options=drugged_models,
            index=drugged_models.index("MGH1501-1A") if "MGH1501-1A" in drugged_models else 0,
            key="cycle_model",
        )
    
    if cycle_model:
        model_mice = df_list[df_list["Model"] == cycle_model]
        model_mouse_ids = sorted(model_mice["Name"].unique())
        
        with col_mouse_sel:
            cycle_mouse = st.selectbox(
                "Select Mouse (or view all)",
                options=["📊 All mice in model"] + model_mouse_ids,
                key="cycle_mouse",
            )
        
        # ── All-mice summary for the model ──
        if cycle_mouse == "📊 All mice in model":
            st.markdown(f"### 📊 Cumulative Cycle Summary for **{cycle_model}**")
            
            # Compute cumulative cycles for every mouse in this model
            summary_rows = []
            for mid in model_mouse_ids:
                chain, total, drugs = get_cumulative_cycles(df_list, mid)
                mouse_row = model_mice[model_mice["Name"] == mid].iloc[0]
                reg = mouse_row.get("Regimen") if pd.notna(mouse_row.get("Regimen")) else None
                own_cycles, own_drug = extract_cycles(reg, mouse_row.get("Description"))
                
                summary_rows.append({
                    "Mouse": mid,
                    "Passage": int(mouse_row["Psg"]) if pd.notna(mouse_row.get("Psg")) else None,
                    "Source": mouse_row.get("Source Type"),
                    "Own Regimen": reg or "—",
                    "Own Cycles": own_cycles,
                    "Counted": "✓" if own_cycles >= 2 else ("skip" if own_cycles == 1 else "—"),
                    "Cumulative Cycles": total,
                    "Drugs": ", ".join(f"{d}: {c}" for d, c in drugs.items()) if drugs else "—",
                    "Active": "🟢" if mid in active_mice else "",
                })
            
            summary_df = pd.DataFrame(summary_rows)
            
            # Highlight mice with significant cumulative drugging
            st.markdown("#### Mice sorted by cumulative cycles")
            summary_sorted = summary_df.sort_values("Cumulative Cycles", ascending=False)
            
            st.dataframe(
                summary_sorted,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "Cumulative Cycles": st.column_config.ProgressColumn(
                        "Cumulative Cycles",
                        min_value=0,
                        max_value=int(max(summary_sorted["Cumulative Cycles"].max(), 1)),
                        format="%d cycles",
                    ),
                    "Own Cycles": st.column_config.NumberColumn("Own Cycles", width=80),
                    "Passage": st.column_config.NumberColumn("P", width=40),
                    "Active": st.column_config.TextColumn("", width=30),
                }
            )
            
            # Distribution chart
            if summary_df["Cumulative Cycles"].max() > 0:
                st.markdown("#### 📈 Cumulative Cycle Distribution")
                
                has_cycles = summary_df[summary_df["Cumulative Cycles"] > 0].copy()
                if not has_cycles.empty:
                    fig_dist = px.histogram(
                        has_cycles,
                        x="Cumulative Cycles",
                        nbins=int(max(has_cycles["Cumulative Cycles"].max(), 1)),
                        color_discrete_sequence=["#38bdf8"],
                        labels={"Cumulative Cycles": "Total Cumulative Cycles", "count": "Number of Mice"},
                    )
                    fig_dist.update_layout(
                        plot_bgcolor="#0a0e1a",
                        paper_bgcolor="#0a0e1a",
                        font_color="#cbd5e1",
                        height=300,
                        bargap=0.1,
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)
                
                # By passage level
                st.markdown("#### 📊 Average Cumulative Cycles by Passage")
                by_psg = summary_df.groupby("Passage")["Cumulative Cycles"].agg(["mean", "max", "count"]).reset_index()
                by_psg.columns = ["Passage", "Avg Cycles", "Max Cycles", "# Mice"]
                
                fig_psg = go.Figure()
                fig_psg.add_trace(go.Bar(
                    x=by_psg["Passage"], y=by_psg["Avg Cycles"],
                    name="Average", marker_color="#38bdf8",
                    text=by_psg["Avg Cycles"].round(1),
                    textposition="outside",
                ))
                fig_psg.add_trace(go.Bar(
                    x=by_psg["Passage"], y=by_psg["Max Cycles"],
                    name="Max", marker_color="#7c3aed", opacity=0.5,
                ))
                fig_psg.update_layout(
                    plot_bgcolor="#0a0e1a",
                    paper_bgcolor="#0a0e1a",
                    font_color="#cbd5e1",
                    height=350,
                    barmode="overlay",
                    xaxis_title="Passage",
                    yaxis_title="Cumulative Cycles",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                )
                st.plotly_chart(fig_psg, use_container_width=True)
        
        # ── Single mouse deep dive ──
        else:
            selected_mid = cycle_mouse
            chain, total_cycles, drugs_seen = get_cumulative_cycles(df_list, selected_mid)
            
            # Header with total
            st.markdown(f"### {selected_mid}")
            
            met1, met2, met3 = st.columns(3)
            with met1:
                color = "#22c55e" if total_cycles <= 4 else "#f59e0b" if total_cycles <= 8 else "#ef4444"
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-value" style="color:{color}">{total_cycles}</div>'
                    f'<div class="metric-label">Cumulative Cycles</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with met2:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-value" style="color:#38bdf8">{len(chain)}</div>'
                    f'<div class="metric-label">Generations</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with met3:
                drug_str = ", ".join(drugs_seen.keys()) if drugs_seen else "None"
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-value" style="color:#a78bfa;font-size:18px">{drug_str}</div>'
                    f'<div class="metric-label">Drugs Used</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            
            st.markdown("---")
            
            # Visual lineage with cycle accumulation
            st.markdown("#### 🧬 Lineage Cycle Breakdown")
            
            running_total = 0
            lineage_html_parts = []
            for c in chain:
                if c["Counted"]:
                    running_total += c["Cycles"]
                
                short = c["Name"].split("_")[-1] if "_" in c["Name"] else c["Name"]
                src = c.get("Source Type", "")
                
                if c["Counted"]:
                    border_color = "#2563eb"
                    bg = "#1e3a5f"
                    cycle_label = f'<div style="color:#38bdf8;font-weight:700;font-size:14px">+{c["Cycles"]} cycles</div>'
                    cycle_label += f'<div style="color:#cbd5e1;font-size:10px">Running: {running_total}</div>'
                elif c["Cycles"] == 1:
                    border_color = "#854d0e"
                    bg = "#451a03"
                    cycle_label = '<div style="color:#f59e0b;font-size:11px">x1 (skipped)</div>'
                elif c["Cycles"] == 0 and c.get("Regimen"):
                    border_color = "#6b7280"
                    bg = "#1f2937"
                    cycle_label = f'<div style="color:#6b7280;font-size:11px">{c["Regimen"]}</div>'
                else:
                    border_color = "#334155"
                    bg = "#1e293b"
                    cycle_label = '<div style="color:#475569;font-size:11px">No drug</div>'
                
                if src in ("ctc", "line", "bx", "stc"):
                    border_color = "#22c55e"
                    bg = "#064e3b"
                
                drug_badge = ""
                if c.get("Drug"):
                    info = get_drug_info(c["Drug"])
                    if info:
                        drug_badge = f'<span style="background:{info["bg"]};color:{info["fg"]};padding:1px 6px;border-radius:3px;font-size:10px">{info["label"]}</span>'
                
                lineage_html_parts.append(
                    f'<span class="lineage-node" style="border-color:{border_color};background:{bg};min-width:100px">'
                    f'<div style="font-size:10px;color:#cbd5e1">{src or "P" + str(int(c["Psg"])) if pd.notna(c.get("Psg")) else "?"}</div>'
                    f'<div style="font-weight:700;color:#f1f5f9;font-size:12px">{short}</div>'
                    f'{drug_badge}'
                    f'{cycle_label}'
                    f'</span>'
                )
            
            path_html = '<span class="lineage-arrow"> → </span>'.join(lineage_html_parts)
            st.markdown(f'<div class="lineage-path">{path_html}</div>', unsafe_allow_html=True)
            
            # Detail table
            st.markdown("#### 📋 Cycle Details")
            chain_df = pd.DataFrame(chain)
            display_chain = chain_df[["Name", "Source Type", "Psg", "Regimen", "Cycles", "Drug", "Counted", "Days"]].copy()
            display_chain["Status"] = display_chain.apply(
                lambda r: f"✓ +{r['Cycles']}" if r["Counted"] else ("⏭ skipped (x1)" if r["Cycles"] == 1 else "—"),
                axis=1,
            )
            st.dataframe(display_chain, use_container_width=True, hide_index=True)
            
            # Drugs breakdown
            if drugs_seen:
                st.markdown("#### 💊 Drug Breakdown")
                drug_cols = st.columns(len(drugs_seen))
                for i, (drug, count) in enumerate(drugs_seen.items()):
                    info = get_drug_info(drug)
                    color = info["bg"] if info else "#334155"
                    label = info["label"] if info else drug
                    with drug_cols[i]:
                        st.markdown(
                            f'<div class="metric-card">'
                            f'<div class="metric-value" style="color:{color}">{count}</div>'
                            f'<div class="metric-label">{label}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            
            # Lineage tree
            st.markdown("#### 🌲 Lineage Tree")
            fig_tree = build_tree_graph(df_list, selected_mid, active_mice)
            if fig_tree:
                st.plotly_chart(fig_tree, use_container_width=True)
            
            # Download
            st.download_button(
                "📥 Download Cycle Data CSV",
                pd.DataFrame(chain).to_csv(index=False),
                file_name=f"{selected_mid}_cycles.csv",
                mime="text/csv",
                key="cycle_download",
            )


# ─────────────────────────────────────────────────────────────────
# TAB 5: COLONY STATS
# ─────────────────────────────────────────────────────────────────
with tab_stats:
    
    # Summary metrics
    total = len(df_list)
    active_count = len(active_mice)
    drugged = df_list["Regimen"].notna().sum()
    model_count = df_list["Model"].nunique()
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:#38bdf8">{total}</div>'
            f'<div class="metric-label">🐁 Total Mice</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:#22c55e">{active_count}</div>'
            f'<div class="metric-label">🟢 Active</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:#a78bfa">{drugged}</div>'
            f'<div class="metric-label">💊 Drugged</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:#f59e0b">{model_count}</div>'
            f'<div class="metric-label">🧬 Models</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    
    st.markdown("---")
    
    # Drug Color Legend
    st.markdown("### 💊 Drug Color Legend")
    legend_html = ""
    for key, val in DRUG_COLORS.items():
        legend_html += (
            f'<span style="display:inline-block;background:{val["bg"]};color:{val["fg"]};'
            f'padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;'
            f'margin:3px 4px">{val["label"]}</span>'
        )
    st.markdown(legend_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_left, col_right = st.columns(2)
    
    # Top Models Chart
    with col_left:
        st.markdown("### 🧬 Top Models")
        model_counts = df_list["Model"].value_counts().head(20)
        model_counts = model_counts[model_counts.index != "Error"]  # exclude errors
        
        fig_models = px.bar(
            x=model_counts.values,
            y=model_counts.index,
            orientation="h",
            labels={"x": "Count", "y": "Model"},
            color=model_counts.values,
            color_continuous_scale="Blues",
        )
        fig_models.update_layout(
            plot_bgcolor="#0a0e1a",
            paper_bgcolor="#0a0e1a",
            font_color="#cbd5e1",
            showlegend=False,
            coloraxis_showscale=False,
            height=500,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=150),
        )
        st.plotly_chart(fig_models, use_container_width=True)
    
    # Top Regimens Chart
    with col_right:
        st.markdown("### 💊 Top Regimens")
        reg_counts = df_list["Regimen"].value_counts().head(20)
        
        colors = []
        for reg in reg_counts.index:
            info = get_drug_info(reg)
            colors.append(info["bg"] if info else "#475569")
        
        fig_regs = px.bar(
            x=reg_counts.values,
            y=reg_counts.index,
            orientation="h",
            labels={"x": "Count", "y": "Regimen"},
        )
        fig_regs.update_traces(marker_color=colors)
        fig_regs.update_layout(
            plot_bgcolor="#0a0e1a",
            paper_bgcolor="#0a0e1a",
            font_color="#cbd5e1",
            showlegend=False,
            height=500,
            yaxis=dict(autorange="reversed"),
            margin=dict(l=200),
        )
        st.plotly_chart(fig_regs, use_container_width=True)
    
    # Source Types
    st.markdown("### 📦 Source Types")
    source_counts = df_list["Source Type"].value_counts()
    
    fig_source = px.pie(
        values=source_counts.values,
        names=source_counts.index,
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.4,
    )
    fig_source.update_layout(
        plot_bgcolor="#0a0e1a",
        paper_bgcolor="#0a0e1a",
        font_color="#cbd5e1",
        height=350,
    )
    st.plotly_chart(fig_source, use_container_width=True)
    
    # Drug duration analysis
    st.markdown("### ⏱️ Drug Duration Analysis")
    drugged_df = df_list[df_list["Regimen"].notna() & df_list["Days"].notna()].copy()
    if not drugged_df.empty:
        drugged_df["Drug"] = drugged_df["Regimen"].apply(
            lambda r: get_drug_info(r)["label"] if get_drug_info(r) else r.split("_")[0]
        )
        
        fig_dur = px.box(
            drugged_df,
            x="Drug",
            y="Days",
            color="Drug",
            color_discrete_sequence=px.colors.qualitative.Set2,
            points="outliers",
        )
        fig_dur.update_layout(
            plot_bgcolor="#0a0e1a",
            paper_bgcolor="#0a0e1a",
            font_color="#cbd5e1",
            showlegend=False,
            height=400,
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig_dur, use_container_width=True)
    
    # Passage distribution
    st.markdown("### 📊 Passage Distribution")
    psg_counts = df_list["Psg"].dropna().astype(int).value_counts().sort_index()
    
    fig_psg = px.bar(
        x=psg_counts.index,
        y=psg_counts.values,
        labels={"x": "Passage Number", "y": "Count"},
        color=psg_counts.values,
        color_continuous_scale="Viridis",
    )
    fig_psg.update_layout(
        plot_bgcolor="#0a0e1a",
        paper_bgcolor="#0a0e1a",
        font_color="#cbd5e1",
        showlegend=False,
        coloraxis_showscale=False,
        height=300,
    )
    st.plotly_chart(fig_psg, use_container_width=True)
