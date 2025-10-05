#!/usr/bin/env python3
"""
GitHub Issues Import with Global IDs
Custom configuration for nested submodule structure
"""

import re
import subprocess
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Issue:
    """Represents a GitHub issue with global ID"""
    number: int
    title: str
    body: str
    labels: List[str]
    milestone: Optional[str]
    epic: Optional[str]
    estimated_time: Optional[str]
    is_epic: bool = False
    dependencies: List[str] = field(default_factory=list)
    global_id: Optional[str] = None


class GlobalIDAssigner:
    """Assigns and tracks global IDs with custom project codes"""
    
    # Map repository names to project codes
    PROJECT_CODES = {
        # Core components
        "space-colony-modelica-core": "MODELICA",
        "modelica-rust-ffi": "FFI",
        "modelica-rust-modbus-server": "MODBUS",
        "godot-modelica-rust-integration": "GODOT",
        
        # Parent projects
        "v-ics-le": "VICS",
        "V-ICS": "VICS",
        "lunaco-sim": "LUNACO",
        "godot-colony-sim": "COLONY",
        
        # Legacy names (if used)
        "modelica-godot-integration": "CORE",
        "colony-sim-framework": "COLONY",
        "mars-irrigation": "IRRIGATION"
    }
    
    # Enhanced component mapping for better categorization
    COMPONENT_MAP = {
        # Environment & Setup
        "setup": "ENV",
        "environment": "ENV",
        "installation": "ENV",
        
        # Proof of Concept
        "poc": "POC",
        "proof-of-concept": "POC",
        "validation": "POC",
        
        # Build & Compilation
        "build": "BUILD",
        "automation": "BUILD",
        "compilation": "BUILD",
        "ci": "BUILD",
        
        # Modeling
        "modeling": "MODEL",
        "model": "MODEL",
        "physics": "MODEL",
        "simulation": "MODEL",
        
        # Rust/FFI specific
        "rust": "RUST",
        "ffi": "FFI",
        "bindings": "FFI",
        "safety": "RUST",
        "concurrency": "RUST",
        
        # Networking & Protocols
        "modbus": "PROTO",
        "protocol": "PROTO",
        "networking": "NET",
        "tcp": "NET",
        
        # Integration
        "integration": "INTEG",
        "godot": "GODOT",
        "api": "API",
        
        # Configuration
        "config": "CONFIG",
        "configuration": "CONFIG",
        
        # Deployment
        "deployment": "DEPLOY",
        "docker": "DEPLOY",
        
        # Performance
        "performance": "PERF",
        "optimization": "PERF",
        
        # Visualization
        "visualization": "VIZ",
        "ui": "VIZ",
        "frontend": "VIZ",
        
        # Backend
        "backend": "BACKEND",
        "server": "BACKEND",
        
        # Power Systems
        "power-systems": "POWER",
        "electrical": "POWER",
        
        # Life Support
        "life-support": "LIFE",
        "eclss": "LIFE",
        
        # Thermal
        "thermal": "THERMAL",
        "heating": "THERMAL",
        
        # Security
        "security": "SEC",
        "attacks": "SEC",
        
        # PLC
        "plc": "PLC",
        
        # Testing
        "testing": "TEST",
        "test": "TEST",
        
        # Documentation
        "documentation": "DOC",
        "docs": "DOC",
        
        # Data
        "data": "DATA"
    }
    
    def __init__(self, repo_name: str, registry_file: str = "global_registry.json"):
        self.repo_name = repo_name
        self.project_code = self._get_project_code(repo_name)
        self.registry_file = Path(registry_file)
        self.registry = self._load_registry()
        
        # Warn if using MISC
        if self.project_code == "MISC":
            print(f"WARNING: Repository '{repo_name}' not in PROJECT_CODES, using MISC")
            print(f"Consider adding to PROJECT_CODES dictionary")
    
    def _load_registry(self) -> Dict:
        """Load existing registry or create new one"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_registry(self):
        """Save registry to disk"""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2, sort_keys=True)
    
    def _get_project_code(self, repo_name: str) -> str:
        """Extract project code from repo name"""
        # Handle org/repo format
        clean_name = repo_name.split('/')[-1] if '/' in repo_name else repo_name
        
        # Try exact match first
        if clean_name in self.PROJECT_CODES:
            return self.PROJECT_CODES[clean_name]
        
        # Try partial match
        for key, code in self.PROJECT_CODES.items():
            if key in clean_name or clean_name in key:
                return code
        
        return "MISC"
    
    def _get_component_code(self, labels: List[str]) -> str:
        """Determine component from labels with priority order"""
        # Check each label for matches
        for label in labels:
            label_lower = label.lower().strip()
            if label_lower in self.COMPONENT_MAP:
                return self.COMPONENT_MAP[label_lower]
        
        # Fallback based on common patterns in label text
        label_text = ' '.join(labels).lower()
        
        if 'rust' in label_text or 'ffi' in label_text:
            return "RUST"
        elif 'modbus' in label_text or 'protocol' in label_text:
            return "PROTO"
        elif 'godot' in label_text:
            return "GODOT"
        elif 'model' in label_text or 'physics' in label_text:
            return "MODEL"
        elif 'config' in label_text:
            return "CONFIG"
        
        return "MISC"
    
    def _count_existing(self, prefix: str) -> int:
        """Count existing issues with given prefix"""
        count = 0
        for gid in self.registry.keys():
            if gid.startswith(prefix):
                count += 1
        return count
    
    def assign_id(self, issue: Issue) -> str:
        """Assign global ID to issue"""
        component = self._get_component_code(issue.labels)
        prefix = f"{self.project_code}-{component}"
        
        # Count existing issues with this prefix
        next_num = self._count_existing(prefix) + 1
        global_id = f"{prefix}-{next_num:03d}"
        
        # Store in registry
        self.registry[global_id] = {
            "global_id": global_id,
            "project": self.project_code,
            "component": component,
            "local_number": issue.number,
            "github_repo": self.repo_name,
            "github_number": None,
            "title": issue.title,
            "labels": issue.labels,
            "milestone": issue.milestone,
            "status": "open"
        }
        
        issue.global_id = global_id
        return global_id
    
    def update_github_number(self, global_id: str, github_number: int):
        """Update GitHub issue number after creation"""
        if global_id in self.registry:
            self.registry[global_id]["github_number"] = github_number
            self._save_registry()
    
    def save(self):
        """Save registry"""
        self._save_registry()
    
    def show_summary(self):
        """Show summary of assigned IDs"""
        if not self.registry:
            print("No issues in registry yet")
            return
        
        # Group by project-component
        groups = {}
        for gid, data in self.registry.items():
            key = f"{data['project']}-{data['component']}"
            if key not in groups:
                groups[key] = []
            groups[key].append(gid)
        
        print("\nGlobal ID Summary:")
        print("=" * 60)
        for key in sorted(groups.keys()):
            count = len(groups[key])
            print(f"{key}: {count} issues")
        print("=" * 60)


class GitHubImporter:
    """Imports issues with global IDs"""
    
    def __init__(self, repo: str, markdown_file: str, dry_run: bool = True):
        self.repo = repo
        self.markdown_file = markdown_file
        self.dry_run = dry_run
        self.milestones: Dict[str, int] = {}
        self.epics: Dict[str, int] = {}
        self.issues: Dict[int, int] = {}
        self.id_assigner = GlobalIDAssigner(repo)
        
    def run(self):
        """Main execution flow"""
        print(f"Starting GitHub import for {self.repo}")
        print(f"Reading from: {self.markdown_file}")
        print(f"Project Code: {self.id_assigner.project_code}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}\n")
        
        # Parse markdown
        milestones, epics, issues = self.parse_markdown()
        
        # Assign global IDs
        print(f"Assigning global IDs...")
        for issue in epics + issues:
            global_id = self.id_assigner.assign_id(issue)
            print(f"  {global_id}: {issue.title[:60]}")
        
        # Show summary
        self.id_assigner.show_summary()
        
        if not self.dry_run:
            # Save registry after assignment
            self.id_assigner.save()
            print(f"\nSaved registry to {self.id_assigner.registry_file}")
        
        # Create milestones
        print(f"\nCreating {len(milestones)} milestones...")
        for milestone in milestones:
            self.create_milestone(milestone)
        
        # Create epics
        if epics:
            print(f"\nCreating {len(epics)} epics...")
            for epic in epics:
                github_number = self.create_issue(epic)
                if github_number:
                    self.epics[epic.title] = github_number
                    if not self.dry_run:
                        self.id_assigner.update_github_number(epic.global_id, github_number)
        
        # Create regular issues
        print(f"\nCreating {len(issues)} issues...")
        for issue in issues:
            github_number = self.create_issue(issue)
            if github_number:
                self.issues[issue.number] = github_number
                if not self.dry_run:
                    self.id_assigner.update_github_number(issue.global_id, github_number)
        
        # Generate instructions
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        if self.dry_run:
            print("\n1. Review the global IDs above")
            print("2. If project code is MISC, update PROJECT_CODES in script")
            print("3. Run with --live flag to create issues")
            print(f"4. Command: python {Path(__file__).name} {self.repo} {self.markdown_file} --live")
        else:
            print(f"\n1. Issues created in {self.repo}")
            print(f"2. Registry saved to {self.id_assigner.registry_file}")
            print(f"3. Add issues to project board manually or via GitHub Actions")
    
    def parse_markdown(self):
        """Parse markdown file"""
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        milestones = []
        epics = []
        issues = []
        
        # Parse milestones
        milestone_pattern = r'## MILESTONE: (.+?)\n\*\*Duration:\*\* (.+?)\n\*\*Goal:\*\* (.+?)(?=\n---|\n##|$)'
        for match in re.finditer(milestone_pattern, content, re.DOTALL):
            milestones.append({
                'title': match.group(1).strip(),
                'duration': match.group(2).strip(),
                'description': match.group(3).strip()
            })
        
        # Parse epics
        epic_pattern = r'### EPIC: (.+?)\n\*\*Labels:\*\* (.+?)\n'
        for match in re.finditer(epic_pattern, content):
            title = match.group(1).strip()
            labels = [l.strip() for l in match.group(2).split(',')]
            epics.append(Issue(
                number=0,
                title=title,
                body="Epic (see original markdown for details)",
                labels=labels,
                milestone=None,
                epic=None,
                estimated_time=None,
                is_epic=True
            ))
        
        # Parse issues
        issue_pattern = r'### ISSUE #(\d+): (.+?)\n\*\*Labels:\*\* (.+?)\n(?:\*\*Epic:\*\* (.+?)\n)?\*\*Milestone:\*\* (.+?)\n\*\*Estimated Time:\*\* (.+?)\n+#### Problem\n(.+?)\n+#### Solution Tasks\n(.+?)\n+#### Acceptance Criteria\n(.+?)(?=\n+####|\n---|\n###|$)'
        for match in re.finditer(issue_pattern, content, re.DOTALL):
            number = int(match.group(1))
            title = match.group(2).strip()
            labels = [l.strip() for l in match.group(3).split(',')]
            milestone = match.group(5).strip()
            estimated_time = match.group(6).strip()
            problem = match.group(7).strip()
            solution_tasks = match.group(8).strip()
            acceptance = match.group(9).strip()
            
            body = f"**Estimated Time:** {estimated_time}\n\n"
            body += f"## Problem\n{problem}\n\n"
            body += f"## Solution Tasks\n{solution_tasks}\n\n"
            body += f"## Acceptance Criteria\n{acceptance}"
            
            issues.append(Issue(
                number=number,
                title=title,
                body=body,
                labels=labels,
                milestone=milestone,
                epic=None,
                estimated_time=estimated_time,
                is_epic=False
            ))
        
        return milestones, epics, issues
    
    def create_milestone(self, milestone_data: Dict):
        """Create milestone"""
        title = milestone_data['title']
        
        if self.dry_run:
            print(f"  [DRY RUN] Would create milestone: {title}")
            self.milestones[title] = 999
            return
        
        try:
            result = subprocess.run(
                ['gh', 'api', f'repos/{self.repo}/milestones', '--jq', f'.[] | select(.title=="{title}") | .number'],
                capture_output=True, text=True, check=False
            )
            
            if result.stdout.strip():
                milestone_number = int(result.stdout.strip())
                print(f"  Milestone exists: {title} (#{milestone_number})")
                self.milestones[title] = milestone_number
                return
            
            result = subprocess.run(
                ['gh', 'api', f'repos/{self.repo}/milestones', '-X', 'POST',
                 '-f', f'title={title}',
                 '-f', f'description={milestone_data["description"]}'],
                capture_output=True, text=True, check=True
            )
            
            milestone_data = json.loads(result.stdout)
            milestone_number = milestone_data['number']
            self.milestones[title] = milestone_number
            print(f"  Created milestone: {title} (#{milestone_number})")
            
        except subprocess.CalledProcessError as e:
            print(f"  Failed to create milestone {title}: {e.stderr}")
    
    def create_issue(self, issue: Issue) -> Optional[int]:
        """Create issue with global ID"""
        labels = ','.join(issue.labels)
        body_with_id = f"**Global ID:** `{issue.global_id}`\n\n---\n\n{issue.body}"
        
        cmd = [
            'gh', 'issue', 'create',
            '--repo', self.repo,
            '--title', issue.title,
            '--body', body_with_id,
            '--label', labels
        ]
        
        if self.dry_run:
            issue_type = "epic" if issue.is_epic else "issue"
            print(f"  [DRY RUN] Would create {issue_type}: {issue.global_id}")
            return issue.number
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            url = result.stdout.strip()
            issue_number = int(url.split('/')[-1])
            print(f"  Created {issue.global_id} (#{issue_number})")
            
            # Add milestone using GitHub API directly (more reliable)
            if issue.milestone and issue.milestone in self.milestones:
                milestone_number = self.milestones[issue.milestone]
                try:
                    # Use API directly instead of gh CLI
                    api_cmd = [
                        'gh', 'api',
                        f'repos/{self.repo}/issues/{issue_number}',
                        '-X', 'PATCH',
                        '-f', f'milestone={milestone_number}'
                    ]
                    subprocess.run(api_cmd, capture_output=True, text=True, check=True)
                    print(f"    → Added to milestone #{milestone_number}")
                except subprocess.CalledProcessError as e:
                    # If that fails too, just skip milestones
                    print(f"    ⚠ Milestone assignment failed (will add manually)")
            
            return issue_number
        except subprocess.CalledProcessError as e:
            print(f"  Failed to create {issue.title}: {e.stderr}")
            return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Import issues with global IDs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run
  python import_issues.py bondlegend4/godot-modelica-rust-integration modelica-rust-integration-issues.md
  
  # Live import
  python import_issues.py bondlegend4/godot-modelica-rust-integration modelica-rust-integration-issues.md --live
        """
    )
    
    parser.add_argument('repo', help='GitHub repository (owner/repo)')
    parser.add_argument('markdown_file', help='Path to markdown file')
    parser.add_argument('--live', action='store_true', help='Actually create issues')
    
    args = parser.parse_args()
    
    # Check prerequisites
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: GitHub CLI not installed")
        return 1
    
    try:
        subprocess.run(['gh', 'auth', 'status'], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("ERROR: Not authenticated")
        return 1
    
    importer = GitHubImporter(
        repo=args.repo,
        markdown_file=args.markdown_file,
        dry_run=not args.live
    )
    
    try:
        importer.run()
        return 0
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
