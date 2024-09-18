# ninja_printer.py

import sys
from termcolor import colored



# This will erase all content in the current line (wherever the cursor is).
# It does not move the cursor, so this is usually followed by \r to move to
# column 0.
csi_erase_line = "\x1b[2K"
# This will erase all content in the current line after the cursor.  This is
# useful for partial updates & progress messages as the terminal can display
# it better.
csi_erase_line_after = "\x1b[K"

def print_status(index, total, path, action, name):
    """
    Prints the current status of a task in progress.

    Args:
        index (int): The current index (e.g., the task being processed).
        total (int): The total number of tasks.
        path (str): The path currently being processed.
        action (str): The action being performed.
        name (str): The name of the item being processed.

    This function prints a formatted status line showing progress in the terminal.
    """
    status_line = f"[{index}/{total}] //{path} {action} {name}"
    sys.stdout.write(f"{colored(status_line, attrs=['bold'])}{csi_erase_line_after}")
    sys.stdout.flush()



def print_newline():
    sys.stdout.write("\n")
    sys.stdout.flush()


