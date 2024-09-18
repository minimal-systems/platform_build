import os
from build_logger import *

# Function to get environment variable with default
def get_env(var, default=None):
    return os.environ.get(var, default)

# Function to set environment variables
def set_env(var, value):
    os.environ[var] = value
    pr_debug(f"Set {var}={value}", log_tag="CCache")

# Function to handle ccache setup
def setup_ccache():
    ccache_exec = get_env('CCACHE_EXEC')
    use_ccache = get_env('USE_CCACHE')

    if ccache_exec and use_ccache and use_ccache.lower() != 'false':
        # Set default for CCACHE_COMPILERCHECK if not already set
        if not get_env('CCACHE_COMPILERCHECK'):
            set_env('CCACHE_COMPILERCHECK', 'content')

        # Set CCACHE_SLOPPINESS
        set_env('CCACHE_SLOPPINESS', 'time_macros,include_file_mtime,file_macro')

        # Set CCACHE_BASEDIR
        set_env('CCACHE_BASEDIR', '/')

        # Set CCACHE_CPP2
        set_env('CCACHE_CPP2', 'true')

        # Set CC_WRAPPER and CXX_WRAPPER if not already set
        if not get_env('CC_WRAPPER'):
            set_env('CC_WRAPPER', ccache_exec)
        if not get_env('CXX_WRAPPER'):
            set_env('CXX_WRAPPER', ccache_exec)

if __name__ == "__main__":
    setup_ccache()
    pr_info("CCache setup completed.")
