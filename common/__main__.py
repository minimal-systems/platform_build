import subprocess

def get_git_version(repo_path="."):
    try:
        # Run the git command to get the short SHA of the latest commit in the specified path
        git_sha = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "--short", "HEAD"]
        ).decode("utf-8").strip()
        # Define your version format
        version = f"0.1-{git_sha}"
        return version
    except subprocess.CalledProcessError:
        return "0.1-unknown"

def common_version():
    # Check the Git version for the build/make/ directory
    return get_git_version(repo_path="build/make/")