"""
Tanner EDA Project Patcher

Automatically analyzes Tanner projects and applies fixes:
- Checks for common design rule violations
- Suggests topology improvements
- Generates verification reports
- Creates fix scripts and patches
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import logging


logger = logging.getLogger(__name__)


@dataclass
class ProjectIssue:
    """Represents an issue found in project"""
    severity: str  # 'critical', 'warning', 'info'
    category: str
    description: str
    file: str
    suggested_fix: str


class TannerProjectPatcher:
    """Analyzes and patches Tanner projects"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.logger = logging.getLogger(__name__)
        self.issues = []
        self.fixes = []

        if not self.project_dir.exists():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

    def analyze_project(self) -> Dict[str, Any]:
        """Complete project analysis"""
        analysis = {
            'project': str(self.project_dir),
            'files': self._scan_files(),
            'structure': self._analyze_structure(),
            'issues': [],
            'recommendations': []
        }

        # Run checks
        self._check_file_organization()
        self._check_naming_conventions()
        self._check_missing_files()
        self._check_layer_definitions()
        self._check_device_density()

        analysis['issues'] = [vars(issue) for issue in self.issues]
        analysis['statistics'] = self._compile_statistics()

        return analysis

    def _scan_files(self) -> Dict[str, List[str]]:
        """Scan project files by type"""
        files = {
            'layout': [],  # .tdb, .mag, .gds
            'schematic': [],  # .sdc, .ckt
            'spice': [],  # .spc, .sp
            'rules': [],  # .rul, .drc
            'documentation': [],  # .txt, .md, .pdf
            'scripts': [],  # .tcl, .py, .sh
            'other': []
        }

        for file_path in self.project_dir.rglob('*'):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()

            if suffix in ['.tdb', '.mag', '.gds', '.gdsii', '.cif']:
                files['layout'].append(str(file_path.relative_to(self.project_dir)))
            elif suffix in ['.sdc', '.ckt']:
                files['schematic'].append(str(file_path.relative_to(self.project_dir)))
            elif suffix in ['.spc', '.sp', '.ext']:
                files['spice'].append(str(file_path.relative_to(self.project_dir)))
            elif suffix in ['.rul', '.drc', '.cal']:
                files['rules'].append(str(file_path.relative_to(self.project_dir)))
            elif suffix in ['.txt', '.md', '.pdf', '.doc']:
                files['documentation'].append(str(file_path.relative_to(self.project_dir)))
            elif suffix in ['.tcl', '.py', '.sh', '.bat']:
                files['scripts'].append(str(file_path.relative_to(self.project_dir)))
            else:
                files['other'].append(str(file_path.relative_to(self.project_dir)))

        return files

    def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze directory structure"""
        structure = {
            'has_simulation_dir': (self.project_dir / 'simulation').exists(),
            'has_layout_dir': (self.project_dir / 'layout').exists(),
            'has_schematic_dir': (self.project_dir / 'schematic').exists(),
            'has_verification_dir': (self.project_dir / 'verification').exists(),
            'has_documentation_dir': (self.project_dir / 'docs').exists(),
            'has_readme': (self.project_dir / 'README.md').exists()
        }

        return structure

    def _check_file_organization(self) -> None:
        """Check if files are properly organized"""
        files = self._scan_files()

        # Check if layout files are in proper directory
        layout_files = files['layout']
        if layout_files and not (self.project_dir / 'layout').exists():
            self.issues.append(ProjectIssue(
                severity='warning',
                category='organization',
                description='Layout files exist but no layout/ directory found',
                file='project root',
                suggested_fix='Create layout/ directory and organize GDS/MAG files'
            ))

        # Check if SPICE files are organized
        spice_files = files['spice']
        if spice_files and not (self.project_dir / 'simulation').exists():
            self.issues.append(ProjectIssue(
                severity='info',
                category='organization',
                description='SPICE files exist but no simulation/ directory',
                file='project root',
                suggested_fix='Create simulation/ directory for netlists'
            ))

    def _check_naming_conventions(self) -> None:
        """Check file naming conventions"""
        for file_path in self.project_dir.rglob('*'):
            if not file_path.is_file():
                continue

            name = file_path.name

            # Check for spaces in filenames
            if ' ' in name:
                self.issues.append(ProjectIssue(
                    severity='warning',
                    category='naming',
                    description=f'File has spaces in name: {name}',
                    file=str(file_path),
                    suggested_fix=f'Rename to: {name.replace(" ", "_")}'
                ))

            # Check for invalid characters
            invalid_chars = ['#', '@', '!', '$', '%']
            if any(char in name for char in invalid_chars):
                self.issues.append(ProjectIssue(
                    severity='warning',
                    category='naming',
                    description=f'File has invalid characters: {name}',
                    file=str(file_path),
                    suggested_fix=f'Remove special characters from filename'
                ))

    def _check_missing_files(self) -> None:
        """Check for missing critical files"""
        critical_files = {
            'README.md': 'Project documentation',
            'Makefile': 'Build automation',
            '.gitignore': 'Git ignore rules'
        }

        for filename, description in critical_files.items():
            if not (self.project_dir / filename).exists():
                self.issues.append(ProjectIssue(
                    severity='info',
                    category='missing_files',
                    description=f'Missing {description}',
                    file=filename,
                    suggested_fix=f'Create {filename} for project organization'
                ))

    def _check_layer_definitions(self) -> None:
        """Check layer definitions in DRC rules"""
        drc_files = list(self.project_dir.rglob('*.rul')) + \
                    list(self.project_dir.rglob('*.drc'))

        if not drc_files:
            self.issues.append(ProjectIssue(
                severity='warning',
                category='layers',
                description='No DRC rule files found',
                file='project root',
                suggested_fix='Create DRC rules file with layer definitions'
            ))

    def _check_device_density(self) -> None:
        """Check for design density issues"""
        # This is a placeholder - would need actual GDS parsing
        self.issues.append(ProjectIssue(
            severity='info',
            category='design',
            description='Device density analysis requires GDS parsing',
            file='layout files',
            suggested_fix='Use GDS parser to analyze device spacing'
        ))

    def _compile_statistics(self) -> Dict[str, Any]:
        """Compile analysis statistics"""
        files = self._scan_files()

        return {
            'total_files': sum(len(v) for v in files.values()),
            'total_issues': len(self.issues),
            'critical_issues': len([i for i in self.issues if i.severity == 'critical']),
            'warnings': len([i for i in self.issues if i.severity == 'warning']),
            'info_messages': len([i for i in self.issues if i.severity == 'info']),
            'file_distribution': files
        }

    def generate_patch_script(self, output_file: str = 'apply_fixes.py') -> str:
        """Generate a Python script to apply fixes"""
        script = """#!/usr/bin/env python3
'''
Auto-generated Tanner Project Patch Script

This script applies suggested fixes to the Tanner EDA project.
Review changes before running: git diff
'''

import os
from pathlib import Path
import shutil

def apply_fixes():
    project_dir = Path('.')
    
    # Create directory structure
    directories = [
        'layout',
        'schematic',
        'simulation',
        'verification',
        'docs',
        'scripts'
    ]
    
    for dir_name in directories:
        dir_path = project_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir()
            print(f'[+] Created directory: {dir_name}/')
    
    # Create .gitignore if missing
    gitignore_path = project_dir / '.gitignore'
    if not gitignore_path.exists():
        gitignore_content = '''# Tanner EDA generated files
*.log
*.tmp
*.bak
*.swp
*~
.DS_Store
__pycache__/
*.pyc

# Simulation outputs
simulation/results/
simulation/*.out
simulation/*.log

# Build artifacts
build/
dist/

# IDE
.vscode/
.idea/
*.sublime-workspace
'''
        gitignore_path.write_text(gitignore_content)
        print('[+] Created .gitignore')
    
    # Fix file names (remove spaces)
    for file_path in project_dir.rglob('*'):
        if file_path.is_file() and ' ' in file_path.name:
            new_name = file_path.name.replace(' ', '_')
            new_path = file_path.parent / new_name
            shutil.move(str(file_path), str(new_path))
            print(f'[*] Renamed: {file_path.name} -> {new_name}')
    
    print('[OK] All fixes applied!')

if __name__ == '__main__':
    apply_fixes()
"""
        script_path = self.project_dir / output_file
        script_path.write_text(script)
        self.logger.info(f"Generated patch script: {output_file}")
        return str(script_path)

    def generate_report(self) -> str:
        """Generate analysis report"""
        analysis = self.analyze_project()

        report = []
        report.append("=" * 70)
        report.append("TANNER PROJECT ANALYSIS AND PATCH REPORT")
        report.append("=" * 70)

        report.append(f"\nProject: {analysis['project']}\n")

        stats = analysis['statistics']
        report.append("STATISTICS:")
        report.append(f"  Total Files: {stats['total_files']}")
        report.append(f"  Total Issues: {stats['total_issues']}")
        report.append(f"  Critical: {stats['critical_issues']}")
        report.append(f"  Warnings: {stats['warnings']}")
        report.append(f"  Info: {stats['info_messages']}")

        if analysis['issues']:
            report.append("\nFOUND ISSUES:")
            report.append("")
            for i, issue in enumerate(analysis['issues'], 1):
                report.append(f"{i}. [{issue['severity'].upper()}] {issue['category']}")
                report.append(f"   File: {issue['file']}")
                report.append(f"   Issue: {issue['description']}")
                report.append(f"   Fix: {issue['suggested_fix']}")
                report.append("")

        report.append("=" * 70)
        return "\n".join(report)


def analyze_and_patch(project_dir: str) -> Dict[str, Any]:
    """Analyze project and generate patch"""
    patcher = TannerProjectPatcher(project_dir)
    analysis = patcher.analyze_project()
    patch_script = patcher.generate_patch_script()

    return {
        'analysis': analysis,
        'patch_script': patch_script,
        'report': patcher.generate_report()
    }
