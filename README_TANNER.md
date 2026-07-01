# Tanner EDA Topology Analysis & Verification

## Overview

AgentAI now includes comprehensive support for analyzing **Tanner EDA** projects:
- Parse and analyze GDS, SPICE, and DRC rule files
- Integrate with open-source EDA tools (KLayout, Netgen, Magic, ngspice)
- Automatic project patching and fixing
- DRC, LVS, and parasitic extraction

## Features

### 1. Tanner File Parsing
- **GDS/GDSII** - Read layout files and extract topology information
- **SPICE** (.spc, .sp) - Parse netlists and identify devices/nets
- **DRC Rules** (.rul, .drc) - Extract design rules
- **Extracted** (.ext) - Read extracted netlists

### 2. Topology Analysis
```bash
python main.py <tanner_project_dir> --mode tanner
```

Generates:
- Topology structure analysis
- Layer distribution statistics
- Cell hierarchy information
- Device inventory
- Net connectivity map

### 3. Automatic Project Patching
```bash
python main.py <tanner_project_dir> --mode patch
```

Automatically:
- Scans project structure
- Identifies organization issues
- Detects naming convention violations
- Generates fix suggestions
- Creates auto-fix script

### 4. Open-Source Verification
```bash
python main.py <tanner_project_dir> --mode verify
```

Runs verification using free tools:
- **KLayout** - DRC checking
- **Netgen** - LVS verification
- **Magic** - Layout extraction and DRC
- **ngspice** - Circuit simulation

## Installation

### Prerequisites
```bash
# Core dependencies
pip install anthropic

# Optional: EDA tools (on Windows)
# Download and install from:
# - KLayout: https://www.klayout.de/
# - Netgen: http://www.opencircuitdesign.com/netgen/
# - Magic: http://opencircuitdesign.com/magic/
```

## Usage

### Mode 1: Analyze Tanner Project Structure
```bash
$env:ANTHROPIC_API_KEY='your_key'
python main.py C:\path\to\tanner\project --mode tanner
```

**Output:**
- `tanner_analysis.txt` - Human-readable report
- `tanner_analysis.json` - Structured data

### Mode 2: Patch Tanner Project
```bash
python main.py C:\path\to\project --mode patch
```

**Output:**
- `tanner_patch_report.txt` - Issues found
- `tanner_patch_analysis.json` - Detailed analysis
- `apply_fixes.py` - Auto-fix script

**Apply fixes:**
```bash
cd <tanner_project_dir>
python apply_fixes.py
```

### Mode 3: Open-Source Verification
```bash
python main.py C:\path\to\project --mode verify
```

**Output:**
- `verification_report.txt` - Verification results
- `verification_results.json` - Structured results

## Architecture

### TannerAnalyzer.py
Main module for file parsing:
- `GDSParser` - Parse GDS files
- `SPICENetlistParser` - Parse netlists
- `DRCRulesParser` - Parse DRC rules
- `TannerProjectAnalyzer` - Project-level analysis

### EDAToolchain.py
Integration with open-source tools:
- `ToolManager` - Detect installed tools
- `KLayoutWrapper` - KLayout integration
- `NetgenWrapper` - Netgen LVS
- `MagicWrapper` - Magic integration
- `NgspiceWrapper` - ngspice simulation
- `OpenSourceEDAToolchain` - Unified interface

### TannerPatcher.py
Project fixing and patching:
- `TannerProjectPatcher` - Analyze issues
- Auto-fix script generation
- Best practices recommendations

## File Format Support

| Format | Extension | Support | Read | Write |
|--------|-----------|---------|------|-------|
| GDS/GDSII | .gds, .gdsii | Full | ✓ | - |
| Caltech Intermediate Form | .cif | Full | ✓ | - |
| SPICE Netlist | .spc, .sp | Full | ✓ | ✓ |
| DRC Rules | .rul, .drc | Full | ✓ | - |
| Extracted | .ext | Full | ✓ | - |
| Magic | .mag | Basic | - | ✓ |
| Tanner Native | .tdb, .tdo | Import | - | - |

## Example Workflow

```bash
# 1. Analyze topology
python main.py ./quartus_project --mode tanner --output ./results

# 2. Review issues found
cat ./results/tanner_analysis.txt

# 3. Patch project automatically
python main.py ./quartus_project --mode patch --output ./patches

# 4. Apply fixes
cd ./quartus_project
python ../patches/apply_fixes.py

# 5. Verify with open-source tools (if installed)
python main.py ./quartus_project --mode verify --output ./verification

# 6. Full AI analysis with Claude
python main.py ./quartus_project --mode review
```

## Supported Tanner EDA File Types

### Layout Files
- `.tdb` - Tanner L-Edit (native format) - requires export to GDS
- `.gds` / `.gdsii` - GDS Layout (industry standard) ✓ Full support
- `.cif` - Caltech Intermediate Format ✓ Full support
- `.mag` - Magic VLSI layout ✓ Basic support

### Simulation & Netlist
- `.spc` / `.sp` - SPICE netlist ✓ Full support
- `.ext` - Extracted netlist ✓ Full support
- `.ttx` - Tanner text format ✓ Parse support

### Verification & Rules
- `.rul` - Tanner DRC rules ✓ Parse support
- `.drc` - Generic DRC rules ✓ Parse support
- `.lyt` - KLayout layer definitions ✓ Support

### Schematics (via exports)
- `.sdc` - Schematics ✓ Parse support
- `.ckt` - Circuit files ✓ Parse support

## Verification Flow

```
Tanner Project
     ↓
┌────────────────────┐
│ Topology Analysis  │ ← TannerAnalyzer.py
└────────────────────┘
     ↓
┌────────────────────┐
│ Issue Detection    │ ← TannerPatcher.py
└────────────────────┘
     ↓
┌────────────────────┐
│ Open-Source Tools  │ ← EDAToolchain.py
│ (DRC/LVS/PEX)      │   (if installed)
└────────────────────┘
     ↓
┌────────────────────┐
│ AI Analysis        │ ← ModelProcessor.py
│ (Claude Review)    │   (optional: --mode review)
└────────────────────┘
     ↓
   Reports
   (JSON + Text)
```

## Open-Source Tools Integration

### KLayout
```bash
# Windows: Download from https://www.klayout.de/
# Run DRC: klayout -b -r script.ly input.gds
```

### Netgen
```bash
# For LVS verification
# Compares layout netlist vs schematic netlist
```

### Magic VLSI
```bash
# Layout extraction and DRC
# magic -nox -noconsole script.tcl
```

### ngspice
```bash
# Post-layout simulation
# ngspice -b netlist.spc -o output.log
```

## Advanced Usage

### Parse GDS Programmatically
```python
from TannerAnalyzer import parse_gds

result = parse_gds('design.gds')
print(f"Cells: {result['cells']}")
print(f"Layers: {result['details']['layer_summary']}")
```

### Parse SPICE Netlist
```python
from TannerAnalyzer import parse_spice

result = parse_spice('netlist.spc')
print(f"Devices: {result['device_count']}")
print(f"Nets: {result['net_count']}")
```

### Run Full Verification
```python
from EDAToolchain import run_full_verification

results = run_full_verification('./project')
print(results['drc'])
print(results['lvs'])
```

## Troubleshooting

### Issue: "Model not supported"
- Check tool installation
- For KLayout: Ensure it's in system PATH
- For Netgen: Verify installation

### Issue: GDS file too large
- Increase `max_file_size` in ContextBuilder
- Consider analyzing specific cells/layers

### Issue: DRC errors persist
- Review DRC rule file syntax
- Check layer definitions match PDK
- Use KLayout GUI for visual inspection

## Performance Tips

1. **Large Projects**: Use `--mode tanner` for quick analysis
2. **Detailed Analysis**: Use `--mode review` with Claude AI
3. **Batch Processing**: Create scripts for multiple projects
4. **Memory**: Monitor for large GDS files (>100MB)

## Limitations

- `.tdb` (Tanner native) requires export to GDS/CIF for analysis
- Binary GDS parsing is simplified (full spec complex)
- Some Tanner-specific metadata lost in export

## Next Steps

1. Install optional open-source tools (KLayout, Netgen)
2. Try `--mode tanner` on your Tanner project
3. Review generated reports
4. Apply suggested fixes with `--mode patch`
5. Optional: Use `--mode verify` for tool verification

## References

- **KLayout**: https://www.klayout.de/
- **Netgen**: http://www.opencircuitdesign.com/netgen/
- **Magic**: http://opencircuitdesign.com/magic/
- **ngspice**: http://ngspice.sourceforge.net/
- **GDSII Format**: http://www.gdsinformation.com/
- **Tanner EDA**: https://www.siemens-eda.com/

## Support

For issues with Tanner analysis:
1. Check generated logs in output files
2. Review file format and structure
3. Verify open-source tools (if using)
4. Run with `--mode tanner` first to identify issues
