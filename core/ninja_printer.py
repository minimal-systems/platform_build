import sys
from tqdm import tqdm
from datetime import timedelta

# Define ANSI escape code for clearing the current line
CSI_ERASE_LINE = "\x1b[2K"  # Clears the entire line where the cursor is located


class NinjaStyleTqdm:
    """
    A custom progress display class that simulates the `ninja` build system's behavior,
    while also utilizing `tqdm` for compatibility and additional functionality.

    Attributes:
        total_tasks (int): Total number of tasks to process.
        tqdm_instance (tqdm): An instance of `tqdm` to manage progress.
    """
    def __init__(self, total_tasks: int):
        """
        Initializes the NinjaStyleTqdm class with the given total number of tasks.
        Uses `tqdm` to manage progress tracking internally.

        Args:
            total_tasks (int): Total number of tasks to be processed.
        """
        self.total_tasks = total_tasks
        # Customize the bar format to exclude iterations per second and timing details
        self.tqdm_instance = tqdm(
            total=total_tasks,
            bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}",  # Custom format excluding timing and rate information
            ncols=0,  # Set ncols=0 to automatically adjust to the terminal width
            disable=True  # Disable the built-in progress bar display
        )
        self.current_task = 0  # Start with task index 0

    def _format_time(self, seconds: float) -> str:
        """
        Formats the given time in seconds to a human-readable string (e.g., 1h 48m).

        Args:
            seconds (float): The time in seconds to be formatted.

        Returns:
            str: A string representing the formatted time (e.g., "1h 48m").
        """
        remaining_time = timedelta(seconds=int(seconds))
        hours, remainder = divmod(remaining_time.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m"

    def display_task(self, action: str, target_file: str):
        """
        Displays the progress of the current task in a ninja-like format by overwriting the same terminal line.

        Args:
            action (str): The action being performed (e.g., "compile").
            target_file (str): The file or target being processed.
        """
        # Calculate the percentage of tasks completed
        percent_complete = (self.current_task / self.total_tasks) * 100

        # Estimate time remaining
        elapsed_time = self.tqdm_instance.format_dict['elapsed']
        if self.current_task > 0:
            estimated_total_time = (elapsed_time / self.current_task) * self.total_tasks
            remaining_time = estimated_total_time - elapsed_time
            time_remaining_str = self._format_time(remaining_time)
        else:
            time_remaining_str = "Calculating..."

        # Format the output string
        task_output = (
            f"[{percent_complete:3.0f}% {time_remaining_str} "
            f"{self.current_task}/{self.total_tasks}] {action} {target_file}"
        )

        # Clear the current line and overwrite it with the formatted output
        sys.stdout.write(f"\r{CSI_ERASE_LINE}{task_output}")
        sys.stdout.flush()

        # Increment the task index and update the tqdm progress bar
        self.tqdm_instance.update(1)
        self.current_task += 1

    def finish(self):
        """
        Completes the tqdm progress bar and prints a final newline to ensure the last line is not overwritten.
        """
        self.tqdm_instance.close()  # Close the tqdm progress bar
        sys.stdout.write("\n")  # Ensure a newline is printed to avoid overwriting the last task output
