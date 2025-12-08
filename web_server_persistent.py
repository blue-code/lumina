"""
Lumina Web Server with Persistent Storage
Enhanced version with auto-save functionality
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.web_server import LuminaWebServer, main
from core.persistent_storage import PersistentStorage


# Monkey patch the LuminaWebServer to add persistence
original_init = LuminaWebServer.__init__

def __init_with_persistence__(self, host='127.0.0.1', port=5000):
    # Call original init
    original_init(self, host, port)
    
    # Add persistence after initialization
    projects_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'projects'
    self.storage = PersistentStorage(projects_dir, auto_save_interval=30)
    
    # Load persisted projects
    print("\\n" + "="*60)
    print("Loading persisted projects...")
    print("="*60)
    persisted_projects = self.storage.load_all_projects()
    
    if persisted_projects:
        # Add to default session
        default_session = 'default'
        with self.sessions_lock:
            self.sessions[default_session] = persisted_projects
            # Set first project as active
            self.active_projects[default_session] = list(persisted_projects.keys())[0]
        print(f"✓ Loaded {len(persisted_projects)} project(s)")
        print("="*60 + "\\n")
    
    # Start auto-save
    def get_all_projects():
        all_projects = {}
        with self.sessions_lock:
            for session_projects in self.sessions.values():
                all_projects.update(session_projects)
        return all_projects
    
    self.storage.start_auto_save(get_all_projects)
    
    # Patch get_session_project_manager to use default session projects
    original_get_pm = self.get_session_project_manager
    
    def get_session_project_manager_with_defaults():
        # Get session ID
        from flask import session as flask_session
        if 'session_id' not in flask_session:
            flask_session['session_id'] = str(__import__('uuid').uuid4())
        
        session_id = flask_session['session_id']
        
        with self.sessions_lock:
            # Initialize session with new session if new
            if session_id not in self.sessions:
                self.sessions[session_id] = {}
                
                # Copy from default session if available
                if 'default' in self.sessions and self.sessions['default']:
                    self.sessions[session_id] = self.sessions['default']
                    if 'default' in self.active_projects:
                        self.active_projects[session_id] = self.active_projects['default']
        
        # Call original method
        return original_get_pm()
    
    self.get_session_project_manager = get_session_project_manager_with_defaults

# Apply the monkey patch
LuminaWebServer.__init__ = __init_with_persistence__

if __name__ == '__main__':
    main()
