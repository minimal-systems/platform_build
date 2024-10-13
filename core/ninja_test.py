import random
import glob
import os
from concurrent.futures import ThreadPoolExecutor
from ninja_printer import NinjaStyleTqdm

def run_task(progress, action, target_file):
    """Helper function to process a task."""
    progress.display_task(action, target_file)

def test_basic_usage():
    """Test normal usage with a sequence of tasks."""
    total_tasks = 10
    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    tasks = [
        ("compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a") for i in range(1, 11)
    ]

    with ThreadPoolExecutor() as executor:
        for action, target_file in tasks:
            executor.submit(run_task, progress, "compile", target_file)

    progress.finish()

def test_large_number_of_tasks():
    """Test behavior with a large number of tasks."""
    total_tasks = 1000
    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    with ThreadPoolExecutor() as executor:
        for i in range(total_tasks):
            executor.submit(run_task, progress, "compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a")

    progress.finish()

def test_random_number_of_tasks():
    """Test with a random number of tasks between 1 and 100,000."""
    total_tasks = random.randint(1, 100000)
    print(f"Running test with {total_tasks} random tasks.")

    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    with ThreadPoolExecutor() as executor:
        for i in range(total_tasks):
            action = random.choice(["compile", "link", "archive"])
            target_file = f"out/host/linux-x86/bin/go/pkg/random_module_{i}.a"
            executor.submit(run_task, progress, action, target_file)

    progress.finish()

def test_empty_task_list():
    """Test behavior with no tasks."""
    progress = NinjaStyleTqdm(total_tasks=0)
    progress.finish()  # Ensure it exits cleanly with no tasks.

def test_single_task():
    """Test usage with a single task."""
    progress = NinjaStyleTqdm(total_tasks=1)
    progress.display_task("compile", "out/host/linux-x86/bin/go/pkg/single_module.a")
    progress.finish()

def test_mismatched_task_count():
    """Test if the progress bar handles more tasks than expected."""
    progress = NinjaStyleTqdm(total_tasks=2)
    tasks = [
        ("compile", "out/host/linux-x86/bin/go/pkg/module1.a"),
        ("compile", "out/host/linux-x86/bin/go/pkg/module2.a"),
        ("link", "out/host/linux-x86/bin/go/libmodule.a")
    ]

    with ThreadPoolExecutor() as executor:
        for action, target_file in tasks:
            executor.submit(run_task, progress, action, target_file)

    progress.finish()

def test_glob_usage():
    """Test using glob to list files and process them."""
    # Create dummy files for testing glob
    os.makedirs("out/host/linux-x86/bin/go/pkg", exist_ok=True)
    for i in range(10):
        with open(f"out/host/linux-x86/bin/go/pkg/module{i}.a", "w") as f:
            f.write("dummy content")

    # Use glob to find all '.a' files in the directory
    files = glob.glob("out/host/linux-x86/bin/go/pkg/*.a")
    total_tasks = len(files)
    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    with ThreadPoolExecutor() as executor:
        for file in files:
            executor.submit(run_task, progress, "compile", file)

    progress.finish()

def test_zero_tasks_handled_correctly():
    """Test scenario where a task count of zero is passed."""
    progress = NinjaStyleTqdm(total_tasks=0)
    assert progress.current_task == 0, "Current task should be initialized to 0"
    progress.finish()

def test_finish_called_multiple_times():
    """Ensure multiple finish() calls do not break functionality."""
    progress = NinjaStyleTqdm(total_tasks=2)
    progress.display_task("compile", "out/host/linux-x86/bin/go/pkg/module1.a")
    progress.finish()
    progress.finish()  # Calling finish() again should not cause errors.

def test_stress_with_large_thread_pool():
    """Stress test with a large thread pool and many tasks."""
    total_tasks = 5000
    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    with ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(total_tasks):
            executor.submit(run_task, progress, "compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a")

    progress.finish()

def test_interrupt_handling():
    """Test behavior if the process is interrupted."""
    try:
        total_tasks = 100
        progress = NinjaStyleTqdm(total_tasks=total_tasks)

        with ThreadPoolExecutor() as executor:
            for i in range(total_tasks):
                if i == 50:  # Simulate interruption
                    raise KeyboardInterrupt("Simulating interruption...")
                executor.submit(run_task, progress, "compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a")

    except KeyboardInterrupt:
        print("\nInterrupted! Cleaning up...")
    finally:
        progress.finish()  # Ensure progress bar is closed properly.

def test_progress_with_delays():
    """Test progress updates with random delays between tasks to simulate real-world latency."""
    total_tasks = 50
    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    def delayed_task(action, target_file):
        """Simulate task with random delay."""
        import time
        time.sleep(random.uniform(0.01, 0.1))  # Simulate random delay
        progress.display_task(action, target_file)

    tasks = [("compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a") for i in range(total_tasks)]

    with ThreadPoolExecutor() as executor:
        for action, target_file in tasks:
            executor.submit(delayed_task, action, target_file)

    progress.finish()

def test_large_file_handling():
    """Test behavior when handling large files."""
    # Create a large dummy file
    large_file = "out/host/linux-x86/bin/go/pkg/large_module.a"
    os.makedirs(os.path.dirname(large_file), exist_ok=True)
    with open(large_file, "wb") as f:
        f.seek(1024 * 1024 * 50)  # 50 MB file
        f.write(b"\0")

    progress = NinjaStyleTqdm(total_tasks=1)

    with ThreadPoolExecutor() as executor:
        executor.submit(run_task, progress, "compile", large_file)

    progress.finish()

def test_task_failure_handling():
    """Test handling of failed tasks."""
    total_tasks = 10
    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    def faulty_task(action, target_file):
        """Simulate a task that raises an exception."""
        if random.random() < 0.2:  # 20% chance of failure
            raise RuntimeError(f"Failed to process {target_file}")
        progress.display_task(action, target_file)

    tasks = [("compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a") for i in range(total_tasks)]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(faulty_task, action, target_file) for action, target_file in tasks]

        # Collect results and handle exceptions
        for future in futures:
            try:
                future.result()  # Raise exception if task failed
            except Exception as e:
                print(f"Error: {e}")

    progress.finish()

def test_dynamic_task_addition():
    """Test adding tasks dynamically during execution."""
    progress = NinjaStyleTqdm(total_tasks=5)

    def dynamic_task(action, target_file):
        """Simulate task processing with dynamic task addition."""
        progress.display_task(action, target_file)

    # Initial set of tasks
    tasks = [("compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a") for i in range(5)]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(dynamic_task, action, target_file) for action, target_file in tasks]

        # Dynamically add more tasks
        for i in range(5, 10):
            futures.append(executor.submit(dynamic_task, "link", f"out/host/linux-x86/bin/go/pkg/module{i}.a"))
            progress.total_tasks += 1  # Adjust total task count

        for future in futures:
            future.result()  # Ensure all tasks complete

    progress.finish()

def test_parallel_execution_with_multiple_progress_bars():
    """Test multiple progress bars running in parallel."""
    progress1 = NinjaStyleTqdm(total_tasks=5)
    progress2 = NinjaStyleTqdm(total_tasks=5)

    def process_with_progress(progress, action, target_file):
        """Simulate task processing with separate progress bars."""
        progress.display_task(action, target_file)

    tasks1 = [("compile", f"out/host/linux-x86/bin/go/pkg/module{i}.a") for i in range(5)]
    tasks2 = [("link", f"out/host/linux-x86/bin/go/pkg/libmodule{i}.a") for i in range(5)]

    with ThreadPoolExecutor() as executor:
        for action, target_file in tasks1:
            executor.submit(process_with_progress, progress1, action, target_file)
        for action, target_file in tasks2:
            executor.submit(process_with_progress, progress2, action, target_file)

    progress1.finish()
    progress2.finish()

def test_cancel_tasks_midway():
    """Test cancelling all tasks midway through execution."""
    total_tasks = 20
    progress = NinjaStyleTqdm(total_tasks=total_tasks)

    def cancellable_task(action, target_file):
        """Simulate a task that can be cancelled."""
        import time
        for _ in range(5):  # Simulate a long-running task
            time.sleep(0.1)
            progress.display_task(action, target_file)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(cancellable_task, "compile", f"module{i}.a") for i in range(total_tasks)]

        # Cancel tasks midway
        print("Cancelling tasks...")
        for future in futures[:10]:  # Cancel the first 10 tasks
            future.cancel()

        for future in futures[10:]:  # Let the rest complete
            future.result()

    progress.finish()

if __name__ == "__main__":
    # Run all tests
    test_basic_usage()
    test_empty_task_list()
    test_single_task()
    test_mismatched_task_count()
    test_zero_tasks_handled_correctly()
    test_finish_called_multiple_times()
    test_large_number_of_tasks()
    test_random_number_of_tasks()
    test_glob_usage()
    test_stress_with_large_thread_pool()
    test_interrupt_handling()
    test_progress_with_delays()
    test_large_file_handling()
    test_task_failure_handling()
    test_dynamic_task_addition()
    test_parallel_execution_with_multiple_progress_bars()
    test_cancel_tasks_midway()

    print("All tests passed.")
