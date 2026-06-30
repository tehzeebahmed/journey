"""
tee_logger.py
Reusable dual-output logger: mirrors all print() output to both
the terminal and a .txt file named after the calling script.
 
Usage in any script:
 
    from tee_logger import start_tee, stop_tee
 
    tee = start_tee(__file__)
    ...
    print("this goes to terminal AND file")
    ...
    stop_tee(tee)
"""
 
import sys
from pathlib import Path
 
 
class Tee:
    """Duplicate stdout to both terminal and file."""
    def __init__(self, filename):
        self.terminal = sys.__stdout__
        self.file = open(filename, "a", encoding="utf-8", buffering=1)
 
    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)
 
    def flush(self):
        self.terminal.flush()
        self.file.flush()
 
    def close(self):
        self.file.close()
 
 
def start_tee(calling_file: str) -> Tee:
    """
    Call this once near the top of any script with start_tee(__file__).
    Creates <script_name>.txt next to the script and redirects stdout to it.
    Returns the Tee instance — keep it if you want to call stop_tee() later,
    though stop_tee() will also work without it (see below).
    """
    text_filename = Path(calling_file).with_suffix(".txt")
    tee = Tee(text_filename)
    sys.stdout = tee
    print(f"[tee_logger] logging to {text_filename}")
    return tee
 
 
def stop_tee(tee: "Tee | None" = None):
    """
    Call this once at the end of any script to restore normal stdout
    and close the log file cleanly. Safe to call even if tee logging
    was never started, or if you don't have a reference to the Tee object.
    """
    current = sys.stdout
    if isinstance(current, Tee):
        sys.stdout = sys.__stdout__   # restore terminal first
        current.file.close()
    elif tee is not None and isinstance(tee, Tee):
        # stdout was already restored elsewhere; close the file directly
        tee.file.close()