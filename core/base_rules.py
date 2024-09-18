import os
import sys

class BuildError(Exception):
    pass

def warning(message):
    print(f"WARNING: {message}")

def error(message):
    raise BuildError(f"ERROR: {message}")

# Catch users that directly include base_rules.mk
module_type = "base_rules"

# Users can define base-rules-hook in their buildspec.mk to perform
# arbitrary operations as each module is included.
base_rules_hook = os.getenv('BASE_RULES_HOOK')
_has_warned_about_base_rules_hook = False

if base_rules_hook and not _has_warned_about_base_rules_hook:
    warning("base-rules-hook is deprecated, please remove usages of it.")
    _has_warned_about_base_rules_hook = True

###########################################################
## Common instructions for a generic module.
###########################################################

LOCAL_MODULE = os.getenv('LOCAL_MODULE', '').strip()
if not LOCAL_MODULE:
    error("LOCAL_MODULE is not defined")

LOCAL_IS_HOST_MODULE = os.getenv('LOCAL_IS_HOST_MODULE', '').strip()

if LOCAL_IS_HOST_MODULE:
    if LOCAL_IS_HOST_MODULE != "true":
        error(f"LOCAL_IS_HOST_MODULE must be 'true' or empty, not '{LOCAL_IS_HOST_MODULE}'")
    my_prefix = os.getenv('LOCAL_HOST_PREFIX', 'HOST_')
    my_host = 'host-'
    my_kind = 'HOST'
else:
    my_prefix = 'TARGET_'
    my_kind = ''
    my_host = ''

if my_prefix == 'HOST_CROSS_':
    my_host_cross = True
else:
    my_host_cross = False

###########################################################
## Module path setup
###########################################################

module_path = os.getenv('LOCAL_MODULE_PATH', '').strip()

LOCAL_PRODUCT_MODULE = os.getenv('LOCAL_PRODUCT_MODULE', '').strip()
if LOCAL_PRODUCT_MODULE == 'true':
    if LOCAL_MODULE in os.getenv('PRODUCT_FORCE_PRODUCT_MODULES_TO_SYSTEM_PARTITION', '').split():
        LOCAL_PRODUCT_MODULE = None

# Use Linux paths instead of Android-specific directories
if module_path.startswith('/usr/lib/'):
    LOCAL_SYSTEM_EXT_MODULE = True
elif module_path.startswith('/lib64/'):
    LOCAL_PRODUCT_MODULE = True

###########################################################
## Fallbacks and validation for LOCAL_* variables
###########################################################

LOCAL_UNINSTALLABLE_MODULE = os.getenv('LOCAL_UNINSTALLABLE_MODULE', '').strip()

if 'tests' not in LOCAL_MODULE and 'samples' not in LOCAL_MODULE:
    error("unusual tags in LOCAL_MODULE_TAGS")

LOCAL_MODULE_CLASS = os.getenv('LOCAL_MODULE_CLASS', '').strip()
if not LOCAL_MODULE_CLASS or len(LOCAL_MODULE_CLASS.split()) != 1:
    error("LOCAL_MODULE_CLASS must contain exactly one word")

my_multilib_module_path = os.getenv(f'LOCAL_MODULE_PATH_{my_prefix}64', '').strip() or os.getenv(f'LOCAL_MODULE_PATH', '').strip()

###########################################################
## Set the install path
###########################################################

if LOCAL_IS_HOST_MODULE:
    install_path_var = f'{my_prefix}OUT_{LOCAL_MODULE_CLASS}'
else:
    partition_tag = '_SYSTEM_EXT' if LOCAL_SYSTEM_EXT_MODULE else '_PRODUCT'
    install_path_var = f'{my_prefix}OUT{partition_tag}_{LOCAL_MODULE_CLASS}'

my_module_path = os.getenv(install_path_var, '')

###########################################################
## Installation rules and symlinks
###########################################################

my_installed_symlinks = []

LOCAL_BUILT_MODULE = f'{my_module_path}/{LOCAL_MODULE}.built'

if LOCAL_UNINSTALLABLE_MODULE != 'true':
    LOCAL_INSTALLED_MODULE = f'{my_module_path}/{LOCAL_MODULE}.installed'

    print(f"Install: {LOCAL_INSTALLED_MODULE}")
    os.system(f'cp {LOCAL_BUILT_MODULE} {LOCAL_INSTALLED_MODULE}')

    for symlink in my_installed_symlinks:
        os.symlink(LOCAL_INSTALLED_MODULE, symlink)

###########################################################
## VINTF manifest and init.rc goals removed for Linux build
###########################################################

###########################################################
## Build verification and targets
###########################################################

def verify_build():
    if not os.path.exists(LOCAL_BUILT_MODULE):
        error(f"Build verification failed: {LOCAL_BUILT_MODULE} not found.")

verify_build()

###########################################################
## Clean-up rules
###########################################################

def clean_module():
    print(f"Clean: {LOCAL_MODULE}")
    os.system(f'rm -rf {LOCAL_BUILT_MODULE} {LOCAL_INSTALLED_MODULE}')

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean_module()
