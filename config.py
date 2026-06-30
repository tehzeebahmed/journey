from pathlib import Path
from dotenv import load_dotenv
import sys

print("Loading configurations.....")
python_bin_dir = Path(sys.executable).parent
print(python_bin_dir)
env_path = python_bin_dir / '.env'
print(env_path)
load_dotenv()