"""
Persistent Storage Manager for Lumina Projects
Handles auto-save and loading of projects from disk
"""
import time
import threading
import uuid
from pathlib import Path
from typing import Dict
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project_manager import ProjectManager


class PersistentStorage:
    """Manages persistent storage of projects"""
    
    def __init__(self, projects_dir: Path, auto_save_interval: int = 30):
        self.projects_dir = projects_dir
        self.projects_dir.mkdir(exist_ok=True)
        self.auto_save_interval = auto_save_interval
        self.auto_save_timer = None
        self.is_running = False
        
    def load_all_projects(self) -> Dict[str, ProjectManager]:
        """Load all projects from disk"""
        projects = {}
        
        try:
            for project_file in self.projects_dir.glob('*.json'):
                try:
                    project_id = project_file.stem
                    pm = ProjectManager.load_from_file(str(project_file))
                    projects[project_id] = pm
                    print(f"  ✓ Loaded: {pm.project_name} ({project_id[:8]}...)")
                except Exception as e:
                    print(f"  ✗ Failed to load {project_file.name}: {e}")
            
            if not projects:
                print("  No persisted projects found, creating sample project...")
                project_id = str(uuid.uuid4())
                pm = ProjectManager()
                pm.project_name = "Sample API Project"
                pm.create_sample_project()
                projects[project_id] = pm
                self.save_project(project_id, pm)
                
        except Exception as e:
            print(f"Error loading persisted projects: {e}")
            
        return projects
    
    def save_project(self, project_id: str, pm: ProjectManager):
        """Save a single project to disk"""
        try:
            project_file = self.projects_dir / f"{project_id}.json"
            pm.save_to_file(str(project_file))
        except Exception as e:
            print(f"Error saving project {project_id}: {e}")
    
    def save_all_projects(self, projects: Dict[str, ProjectManager]):
        """Save all projects to disk"""
        try:
            for project_id, pm in projects.items():
                self.save_project(project_id, pm)
            if projects:
                print(f"Auto-saved {len(projects)} projects")
        except Exception as e:
            print(f"Error during auto-save: {e}")
    
    def start_auto_save(self, get_projects_callback):
        """Start auto-save timer
        
        Args:
            get_projects_callback: Function that returns Dict[str, ProjectManager]
        """
        def auto_save_worker():
            while self.is_running:
                time.sleep(self.auto_save_interval)
                if self.is_running:
                    projects = get_projects_callback()
                    if projects:
                        self.save_all_projects(projects)
        
        self.is_running = True
        self.auto_save_timer = threading.Thread(target=auto_save_worker, daemon=True)
        self.auto_save_timer.start()
        print(f"Auto-save started (interval: {self.auto_save_interval}s)")
    
    def stop_auto_save(self):
        """Stop auto-save timer"""
        self.is_running = False
        if self.auto_save_timer:
            self.auto_save_timer.join(timeout=2)
        print("Auto-save stopped")
