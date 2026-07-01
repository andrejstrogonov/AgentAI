"""
Open-Source EDA Tools Integration Module

Integrates with open-source tools for Tanner EDA project verification:
- KLayout - GDS viewing and DRC checking
- Netgen - LVS (Layout Versus Schematic) verification
- Magic VLSI - Topology editor and extractor
- OpenRCX - Parasitic extraction
- Ngspice - Circuit simulation

This module provides wrappers and utilities to use these tools
without requiring expensive commercial licenses.
"""

import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ToolInfo:
    """Information about an EDA tool"""
    name: str
    executable: str
    version: Optional[str] = None
    installed: bool = False
    path: Optional[str] = None
    description: str = ""


class ToolManager:
    """Manage and detect installed EDA tools"""

    def __init__(self):
        self.tools = {
            'klayout': ToolInfo(
                name='KLayout',
                executable='klayout',
                description='GDS viewer and DRC checker',
                installed=False
            ),
            'magic': ToolInfo(
                name='Magic VLSI',
                executable='magic',
                description='Open-source VLSI layout editor',
                installed=False
            ),
            'netgen': ToolInfo(
                name='Netgen',
                executable='netgen',
                description='LVS (Layout Versus Schematic) verification',
                installed=False
            ),
            'ngspice': ToolInfo(
                name='ngspice',
                executable='ngspice',
                description='Open-source SPICE simulator',
                installed=False
            ),
        }
        self._detect_tools()

    def _detect_tools(self) -> None:
        """Detect installed tools"""
        for tool_key, tool_info in self.tools.items():
            result = self._find_executable(tool_info.executable)
            if result:
                tool_info.installed = True
                tool_info.path = result
                logger.info(f"Found {tool_info.name}: {result}")
            else:
                logger.warning(f"{tool_info.name} not found")

    def _find_executable(self, name: str) -> Optional[str]:
        """Find executable in system PATH"""
        if sys.platform == 'win32':
            name = name + '.exe'

        for path in os.environ['PATH'].split(os.pathsep):
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path

        return None

    def get_installed_tools(self) -> List[ToolInfo]:
        """Get list of installed tools"""
        return [tool for tool in self.tools.values() if tool.installed]

    def get_tool(self, tool_key: str) -> Optional[ToolInfo]:
        """Get tool by key"""
        return self.tools.get(tool_key)


class KLayoutWrapper:
    """Wrapper for KLayout DRC/LVS operations"""

    def __init__(self, klayout_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.klayout_path = klayout_path or 'klayout'

    def run_drc(self, gds_file: str, drc_script: str, output_file: str) -> Dict[str, Any]:
        """
        Run DRC check using KLayout

        Args:
            gds_file: Path to GDS file
            drc_script: Path to DRC script (Ruby or Python)
            output_file: Output report file

        Returns:
            DRC result dictionary
        """
        try:
            cmd = [
                self.klayout_path,
                '-b',  # Batch mode
                '-r', drc_script,
                '-rd', f'input={gds_file}',
                '-rd', f'output={output_file}',
                gds_file
            ]

            self.logger.info(f"Running DRC: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'output_file': output_file
            }

        except Exception as e:
            self.logger.error(f"DRC error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def view_gds(self, gds_file: str) -> None:
        """Open GDS file in KLayout GUI"""
        try:
            subprocess.Popen([self.klayout_path, gds_file])
            self.logger.info(f"Opened {gds_file} in KLayout")
        except Exception as e:
            self.logger.error(f"Failed to open KLayout: {e}")

    def extract_netlist(self, gds_file: str, output_netlist: str) -> Dict[str, Any]:
        """Extract netlist from GDS"""
        try:
            cmd = [
                self.klayout_path,
                '-b',
                '-r', self._get_extraction_script(),
                '-rd', f'input={gds_file}',
                '-rd', f'output={output_netlist}',
                gds_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': output_netlist,
                'details': result.stdout
            }

        except Exception as e:
            self.logger.error(f"Extraction error: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_extraction_script(self) -> str:
        """Get or create extraction script"""
        # This would point to a KLayout extraction script
        return 'extract.ly'


class NetgenWrapper:
    """Wrapper for Netgen LVS verification"""

    def __init__(self, netgen_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.netgen_path = netgen_path or 'netgen'

    def run_lvs(self, layout_netlist: str, schematic_netlist: str,
                output_report: str) -> Dict[str, Any]:
        """
        Run LVS comparison

        Args:
            layout_netlist: Extracted netlist from layout
            schematic_netlist: Netlist from schematic
            output_report: LVS report file

        Returns:
            LVS result
        """
        try:
            # Create Netgen command file
            cmd_file = self._create_netgen_script(
                layout_netlist, schematic_netlist, output_report
            )

            cmd = [self.netgen_path, '-batch', 'source', cmd_file]

            self.logger.info(f"Running LVS: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            # Parse output
            lvs_match = 'match' in result.stdout.lower()

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'lvs_match': lvs_match,
                'return_code': result.returncode,
                'report': output_report,
                'details': result.stdout,
                'errors': result.stderr
            }

        except Exception as e:
            self.logger.error(f"LVS error: {e}")
            return {'status': 'error', 'error': str(e)}

    def _create_netgen_script(self, layout_nl: str, schematic_nl: str,
                             output: str) -> str:
        """Create Netgen command script"""
        script_content = f"""
readnet spice {layout_nl}
readnet spice {schematic_nl}
lvs
exit
"""
        script_file = 'netgen_lvs.cmd'
        with open(script_file, 'w') as f:
            f.write(script_content)

        return script_file


class MagicWrapper:
    """Wrapper for Magic VLSI operations"""

    def __init__(self, magic_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.magic_path = magic_path or 'magic'

    def extract_netlist_from_mag(self, mag_file: str, output_spice: str) -> Dict[str, Any]:
        """Extract SPICE netlist from Magic .mag file"""
        try:
            # Create Magic Tcl script for extraction
            tcl_script = self._create_magic_extraction_script(mag_file, output_spice)

            cmd = [self.magic_path, '-nox', '-noconsole', '-rcfile', '.magicrc',
                   tcl_script]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output': output_spice,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        except Exception as e:
            self.logger.error(f"Magic extraction error: {e}")
            return {'status': 'error', 'error': str(e)}

    def run_drc_check(self, mag_file: str, output_report: str) -> Dict[str, Any]:
        """Run DRC check in Magic"""
        try:
            tcl_script = f"""
load {mag_file}
drc check
drc why
save {output_report}
exit
"""
            script_file = 'magic_drc.tcl'
            with open(script_file, 'w') as f:
                f.write(tcl_script)

            cmd = [self.magic_path, '-nox', '-noconsole', script_file]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # Parse DRC results
            drc_errors = len(re.findall(r'error', result.stdout, re.IGNORECASE))

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'drc_errors': drc_errors,
                'report': output_report,
                'details': result.stdout
            }

        except Exception as e:
            self.logger.error(f"Magic DRC error: {e}")
            return {'status': 'error', 'error': str(e)}

    def _create_magic_extraction_script(self, mag_file: str, output_spice: str) -> str:
        """Create Magic Tcl extraction script"""
        script_content = f"""
load {mag_file}
extract all
ext2spice cthresh 0
ext2spice {output_spice}
quit
"""
        script_file = 'magic_extract.tcl'
        with open(script_file, 'w') as f:
            f.write(script_content)

        return script_file


class NgspiceWrapper:
    """Wrapper for ngspice simulation"""

    def __init__(self, ngspice_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.ngspice_path = ngspice_path or 'ngspice'

    def run_simulation(self, spice_file: str, output_file: str) -> Dict[str, Any]:
        """Run SPICE simulation"""
        try:
            cmd = [self.ngspice_path, '-b', spice_file, '-o', output_file]

            self.logger.info(f"Running simulation: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            return {
                'status': 'success' if result.returncode == 0 else 'error',
                'output_file': output_file,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
            return {'status': 'error', 'error': str(e)}


class OpenSourceEDAToolchain:
    """Unified interface for all open-source EDA tools"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tool_manager = ToolManager()
        self.klayout = None
        self.netgen = None
        self.magic = None
        self.ngspice = None

        self._initialize_tools()

    def _initialize_tools(self) -> None:
        """Initialize available tools"""
        tools_info = self.tool_manager.get_installed_tools()

        for tool in tools_info:
            if tool.name == 'KLayout':
                self.klayout = KLayoutWrapper(tool.path)
            elif tool.name == 'Netgen':
                self.netgen = NetgenWrapper(tool.path)
            elif tool.name == 'Magic VLSI':
                self.magic = MagicWrapper(tool.path)
            elif tool.name == 'ngspice':
                self.ngspice = NgspiceWrapper(tool.path)

    def get_status(self) -> Dict[str, Any]:
        """Get status of all tools"""
        return {
            'klayout_available': self.klayout is not None,
            'netgen_available': self.netgen is not None,
            'magic_available': self.magic is not None,
            'ngspice_available': self.ngspice is not None,
            'installed_tools': [tool.name for tool in self.tool_manager.get_installed_tools()]
        }

    def full_verification_flow(self, project_dir: str) -> Dict[str, Any]:
        """Run complete verification flow: DRC -> LVS -> Simulation"""
        results = {
            'project': project_dir,
            'drc': {},
            'lvs': {},
            'simulation': {},
            'overall_status': 'not_run'
        }

        # Find files
        project_path = Path(project_dir)
        gds_files = list(project_path.rglob('*.gds*'))
        spice_files = list(project_path.rglob('*.spc'))

        # Run DRC if KLayout available
        if self.klayout and gds_files:
            for gds in gds_files:
                drc_result = self.klayout.run_drc(
                    str(gds),
                    'drc_rules.ly',
                    f'{gds.stem}_drc_report.txt'
                )
                results['drc'][gds.name] = drc_result

        # Run LVS if Netgen available
        if self.netgen and spice_files:
            # This would require layout netlist extraction first
            results['lvs']['status'] = 'requires_extraction'

        # Run simulation if ngspice available
        if self.ngspice and spice_files:
            for spice in spice_files:
                sim_result = self.ngspice.run_simulation(
                    str(spice),
                    f'{spice.stem}_sim.out'
                )
                results['simulation'][spice.name] = sim_result

        results['overall_status'] = 'complete'
        return results


# Convenience functions
def get_tool_status() -> Dict[str, Any]:
    """Get status of all available EDA tools"""
    toolchain = OpenSourceEDAToolchain()
    return toolchain.get_status()


def run_full_verification(project_dir: str) -> Dict[str, Any]:
    """Run full verification on project"""
    toolchain = OpenSourceEDAToolchain()
    return toolchain.full_verification_flow(project_dir)


# For imports
import re
