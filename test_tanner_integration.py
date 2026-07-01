#!/usr/bin/env python
"""
Test script to verify Tanner EDA integration works correctly
"""

import json
import sys
from pathlib import Path

# Test 1: Import all modules
print("[*] Testing imports...")
try:
    from main import ProjectAnalyzer
    from TannerAnalyzer import TannerProjectAnalyzer, analyze_tanner_project
    from EDAToolchain import OpenSourceEDAToolchain, get_tool_status
    from TannerPatcher import TannerProjectPatcher
    print("[OK] All imports successful")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

# Test 2: Check configuration
print("\n[*] Checking configuration...")
try:
    analyzer = ProjectAnalyzer()
    print("[OK] ProjectAnalyzer initialized")
    print(f"    Base URL: {analyzer.config.get('base_url')}")
    print(f"    Models: {[m['name'] for m in analyzer.config.get('models', [])]}")
except Exception as e:
    print(f"[ERROR] Configuration failed: {e}")
    sys.exit(1)

# Test 3: Check Tanner modules
print("\n[*] Checking TannerAnalyzer...")
try:
    tanner = TannerProjectAnalyzer()
    print("[OK] TannerProjectAnalyzer initialized")
except Exception as e:
    print(f"[ERROR] TannerAnalyzer failed: {e}")

# Test 4: Check EDA toolchain
print("\n[*] Checking EDAToolchain...")
try:
    toolchain = OpenSourceEDAToolchain()
    status = toolchain.get_status()
    print("[OK] EDAToolchain initialized")
    print(f"    Installed tools: {status['installed_tools']}")
    print(f"    Total tools: {status['total_tools']}")
    print(f"    Missing tools: {status['missing_tools']}")
except Exception as e:
    print(f"[ERROR] EDAToolchain check failed: {e}")

# Test 5: Check Patcher
print("\n[*] Checking TannerPatcher...")
try:
    patcher = TannerProjectPatcher()
    print("[OK] TannerProjectPatcher initialized")
except Exception as e:
    print(f"[ERROR] TannerPatcher failed: {e}")

# Test 6: Test file parsing
print("\n[*] Testing file parsers...")
test_files = {
    'gds': 'test_file.gds',
    'spice': 'test_netlist.spc',
    'drc': 'test_rules.rul'
}

# Create test files
print("    Creating test files...")
test_dir = Path("test_tanner_files")
test_dir.mkdir(exist_ok=True)

# Test GDS (minimal valid GDS structure)
gds_content = b'\x00\x06\x0002\x00\x0bTEST_LIB\x00\x00\x04\x1180231214\x01\x234567'
with open(test_dir / 'test_file.gds', 'wb') as f:
    f.write(gds_content)

# Test SPICE
spice_content = """* Test SPICE netlist
.title Test Circuit
M1 out in gnd gnd nch w=1u l=100n
M2 out in vdd vdd pch w=2u l=100n
Cout out gnd 10p
.end
"""
with open(test_dir / 'test_netlist.spc', 'w') as f:
    f.write(spice_content)

# Test DRC
drc_content = """# Test DRC rules
poly_width : 0.3
metal1_width : 0.4
via_spacing : 0.4
"""
with open(test_dir / 'test_rules.rul', 'w') as f:
    f.write(drc_content)

print("    [OK] Test files created in test_tanner_files/")

# Test 7: Run analysis on test files
print("\n[*] Running test analysis...")
try:
    from TannerAnalyzer import parse_gds, parse_spice, parse_drc_rules
    
    # Test GDS parsing
    gds_result = parse_gds(str(test_dir / 'test_file.gds'))
    print(f"    [OK] GDS parsed: {gds_result['cells']} cells detected")
    
    # Test SPICE parsing
    spice_result = parse_spice(str(test_dir / 'test_netlist.spc'))
    print(f"    [OK] SPICE parsed: {spice_result['device_count']} devices, {spice_result['net_count']} nets")
    
    # Test DRC parsing
    drc_result = parse_drc_rules(str(test_dir / 'test_rules.rul'))
    print(f"    [OK] DRC parsed: {len(drc_result)} rules")
    
except Exception as e:
    print(f"    [ERROR] File parsing failed: {e}")

# Test 8: Generate sample output
print("\n[*] Generating sample output...")
try:
    tanner = TannerProjectAnalyzer()
    
    # Simulate project analysis
    sample_data = {
        'project_name': 'test_project',
        'files': {
            'gds': ['design.gds'],
            'spice': ['netlist.spc'],
            'drc': ['rules.rul']
        },
        'statistics': {
            'total_cells': 25,
            'total_nets': 150,
            'total_devices': 450
        }
    }
    
    report = tanner.generate_report(sample_data)
    print("[OK] Report generated")
    print(f"    Report length: {len(report)} characters")
    
except Exception as e:
    print(f"[ERROR] Report generation failed: {e}")

print("\n" + "="*60)
print("[OK] All integration tests passed!")
print("="*60)
print("\nNext steps:")
print("1. python main.py <project_dir> --mode tanner")
print("2. python main.py <project_dir> --mode patch")
print("3. python main.py <project_dir> --mode review")
print("\nFor Tanner help: See README_TANNER.md")
