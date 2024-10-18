import os
import subprocess
from definitions import intermediates_dir_for
from envsetup import *

# Intermediates paths for passwd and property contexts
passwd_system = intermediates_dir_for("ETC", "passwd_system")
passwd_recovery = intermediates_dir_for("ETC", "passwd_recovery")
passwd_containers = intermediates_dir_for("ETC", "passwd_containers")

plat_property_contexts = intermediates_dir_for("ETC", "plat_property_contexts")
recovery_property_contexts = intermediates_dir_for("ETC", "recovery_property_contexts")
containers_property_contexts = intermediates_dir_for("ETC", "containers_property_contexts")

# Output paths for system directories using variables from envsetup
out_rootfs = target_system_out
out_recovery = target_copy_out_recovery
out_containers = target_copy_out_containers

# Output file
host_init_verifier_output = os.path.join(product_out, "host_init_verifier_output.txt")
host_init_verifier = f"{out_dir}/host/linux-x86/bin/host_init_verifier"

def run_host_init_verifier():
    """
    Run the host_init_verifier on the partition staging directories.
    """
    command = [
        host_init_verifier,
        "-p", passwd_system,
        "-p", passwd_recovery,
        "-p", passwd_containers,
        "--property-contexts=" + plat_property_contexts,
        "--property-contexts=" + recovery_property_contexts,
        "--property-contexts=" + containers_property_contexts,
        "--out_system", out_rootfs,
        "--out_recovery", out_recovery,
        "--out_containers", out_containers
    ]

    with open(host_init_verifier_output, "w") as output_file:
        result = subprocess.run(command, stdout=output_file, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Error running host_init_verifier: {result.stderr.decode()}")
        else:
            print(f"host_init_verifier completed successfully, output saved to {host_init_verifier_output}")


def dist_for_goals(goal, target):
    """
    Placeholder function for 'dist-for-goals' behavior.
    """
    print(f"Distributing {target} for goal {goal}")
    # This could copy the file to a specific location or perform other actions as necessary.


if __name__ == "__main__":
    run_host_init_verifier()
    dist_for_goals("droidcore-unbundled", host_init_verifier_output)
