# 🧬 PDX Lineage Tracker

A Streamlit app for tracking Patient-Derived Xenograft (PDX) mouse lineages, drug regimens, and colony management.

## Quick Start

### 1. Install Python (if not already installed)
Download from [python.org](https://www.python.org/downloads/) — version 3.9 or newer.

### 2. Install dependencies
Open a terminal/command prompt in this folder and run:

```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app.py
```

This opens a browser tab at `http://localhost:8501`. Upload your Mouse Directory Excel file and you're ready to go.

## Features

### 🔍 Search & Filter
- Free-text search across mouse IDs, models, regimens, and descriptions
- Filter by model, regimen, or active status
- Sortable results table with up to 300 results

### 🌳 Lineage Tracker
- Select any mouse to trace its full ancestry back to cell line origin
- Visual lineage path with drug color coding
- Interactive tree graph showing parent-child relationships
- View all descendants of any mouse
- Download lineage as CSV

### 📋 Active Mice
- Live view from the Measurements tab
- Tumor volume calculation (L × W² / 2)
- Tumor volume box plots by regimen
- Weekly to-do items from the New-To Do tab

### 📊 Colony Stats
- Total mice, active count, drugged count, model count
- Top models and regimens bar charts (color-coded by drug)
- Source type distribution
- Drug duration analysis (box plots)
- Passage number distribution

### 💊 Drug Color Coding
Every drug regimen gets a distinct color badge. The system recognizes many formats:
- "Double Dox + Dox Chow", "Double Dox", "Dox Chow"
- "CisEtop_7_10_x2", "CisEtop_5_8_14d_x2"
- "MRTX1133_30mpk", "MRTX1133_Veh"
- "Tarla_3q7_V05"
- And 25+ other drug patterns

Cycle information is also parsed: "x2" → 2-cycle, "14d" → 14-day, "biw" → twice weekly, etc.

## Dynamic Weekly Updates
Just upload the latest Excel file each time you open the app. The app reads directly from:
- **List** tab → all mouse records
- **Measurements** tab → currently active mice
- **New-To Do** tab → weekly tasks

No database needed — your Excel file IS the database.

## Sharing with Your Lab

### Option A: Run locally (simplest)
Each person installs Python + requirements and runs `streamlit run app.py`.

### Option B: Shared lab computer
Run the app on one computer and others access it via the network:
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```
Others visit `http://<computer-ip>:8501` in their browser.

### Option C: Streamlit Community Cloud (free hosting)
1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Deploy for free — anyone with the link can use it

## File Structure
```
pdx_tracker/
├── app.py              # Main application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
