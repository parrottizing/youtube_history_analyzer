
import os

def load_env():
    """Load environment variables from .env file in the project root."""
    # Find project root (assuming this file is in utils/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    env_path = os.path.join(project_root, '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove surrounding quotes if present
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value
    else:
        print(f"Warning: .env file not found at {env_path}")
