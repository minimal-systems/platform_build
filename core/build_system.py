from colorama import Fore
from colorama import Style


# init log info
def print_ok(str):
    print(f"[{Fore.GREEN} OK {Style.RESET_ALL}] {str}")


def print_debug(str):
    print(f"[{Fore.MAGENTA} DEBUG {Style.RESET_ALL}] {str}")


def print_warn(str):
    print(f"[{Fore.YELLOW} WARNING {Style.RESET_ALL}] {str}")


def print_info(str):
    print(f"[{Fore.BLUE} INFO {Style.RESET_ALL}] {str}")


def print_err(str):
    print(f"[{Fore.RED} ERROR {Style.RESET_ALL}] {str}")
