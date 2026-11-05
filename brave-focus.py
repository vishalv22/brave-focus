"""
Brave Focus Toggle
------------------
Blocks distracting sites in Brave using browser policies.
Run it, type the option number, done.

1 = Focus ON    (block the sites in your list)
2 = Focus OFF   (remove the block - your list is kept)
3 = Show status and list
4 = Add a site to the list
5 = Remove a site from the list
6 = Debloat Brave (one-way: turns off Rewards, Wallet, VPN,
    News, Talk, Leo AI and the telemetry pings - no undo here)
0 = Exit

Your site list lives in "focus_sites.txt" next to this script
(one site per line - you can also edit that file by hand).
Focus options touch only the URLBlocklist policy; the debloat
option writes its own separate policies. Nothing else changes.
"""

import ctypes
import os
import sys
import winreg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(BASE_DIR, "focus_sites.txt")

# Starts empty on purpose - you add your own sites with option 4.
DEFAULT_SITES = []

POLICY_PATH = r"SOFTWARE\Policies\BraveSoftware\Brave"
BLOCKLIST_PATH = POLICY_PATH + r"\URLBlocklist"


# ---------- colors ----------

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[90m"


def enable_colors():
    """Turn on ANSI color support in the Windows console."""
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            # 0x0004 = ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass  # colors are decoration - never crash over them


def c(text, color):
    """Wrap text in a color."""
    return f"{color}{text}{RESET}"


# ---------- admin ----------

def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def restart_as_admin():
    # Reopen this script with admin rights (registry policies need them).
    script = os.path.abspath(__file__)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}"', None, 1
    )
    sys.exit(0)


# ---------- the site list (saved in focus_sites.txt) ----------

def load_sites():
    if not os.path.exists(LIST_FILE):
        save_sites(DEFAULT_SITES)
        return list(DEFAULT_SITES)
    with open(LIST_FILE, "r") as f:
        sites = [line.strip() for line in f if line.strip()]
    # Safety net: if the file was edited by hand and a site
    # appears twice, keep only the first copy.
    return list(dict.fromkeys(sites))


def save_sites(sites):
    with open(LIST_FILE, "w") as f:
        f.write("\n".join(sites) + "\n")


# ---------- the Brave block (in the Windows registry) ----------

def block_is_on():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, BLOCKLIST_PATH)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def apply_block(sites):
    remove_block()  # rebuild cleanly, so numbering stays 1, 2, 3...
    key = winreg.CreateKeyEx(
        winreg.HKEY_LOCAL_MACHINE, BLOCKLIST_PATH, 0, winreg.KEY_SET_VALUE
    )
    for i, site in enumerate(sites, start=1):
        winreg.SetValueEx(key, str(i), 0, winreg.REG_SZ, site)
    winreg.CloseKey(key)


def remove_block():
    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, BLOCKLIST_PATH)
    except FileNotFoundError:
        pass


# ---------- debloat (option 6, one-way) ----------

# *Disabled policies take 1 (= disabled), *Enabled policies take 0 (= off).
DEBLOAT_POLICIES = {
    "BraveRewardsDisabled": 1,      # Rewards / BAT ads
    "BraveWalletDisabled": 1,       # built-in crypto wallet
    "BraveVPNDisabled": 1,          # Brave VPN prompts
    "BraveNewsDisabled": 1,         # news feed on the new tab page
    "BraveTalkDisabled": 1,         # Brave Talk video calls
    "BraveAIChatEnabled": 0,        # Leo AI assistant
    "BraveStatsPingEnabled": 0,     # daily "still installed" ping
    "BraveP3AEnabled": 0,           # anonymous usage metrics
    "BraveWebDiscoveryEnabled": 0,  # Web Discovery data contribution
}


def debloat_brave():
    print("\nThis turns OFF, with no undo in this tool:")
    print("  Rewards, Wallet, VPN, News, Talk, Leo AI,")
    print("  stats ping, P3A metrics, Web Discovery.")
    confirm = input("Type y and press Enter to continue: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    key = winreg.CreateKeyEx(
        winreg.HKEY_LOCAL_MACHINE, POLICY_PATH, 0, winreg.KEY_SET_VALUE
    )
    for name, value in DEBLOAT_POLICIES.items():
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
    winreg.CloseKey(key)
    print(c("\nDone. Debloat applied - these are now off:", GREEN + BOLD))
    for name in DEBLOAT_POLICIES:
        print("  -", name)


# ---------- menu actions ----------

def focus_on(sites):
    if not sites:
        print(c("\nYour list is empty - add a site first (option 4).", YELLOW))
        return
    apply_block(sites)
    print(c("\nFocus is ON. Blocked:", GREEN + BOLD))
    for site in sites:
        print("  -", site)


def focus_off():
    if block_is_on():
        remove_block()
        print(c("\nFocus is OFF. Blocklist removed (your list is kept).", YELLOW))
    else:
        print(c("\nFocus was already OFF - nothing to remove.", DIM))


def show_status(sites):
    state = c("ON", GREEN + BOLD) if block_is_on() else c("OFF", YELLOW)
    print(f"\nStatus: {state}")
    print("Your list:")
    if sites:
        for i, site in enumerate(sites, start=1):
            print(f"  {i}. {site}")
    else:
        print("  (empty)")


def add_site(sites):
    while True:
        site = input("\nSite to block (example: youtube.com/shorts): ").strip()
        site = site.replace("https://", "").replace("http://", "").strip()
        if not site:
            print("Nothing entered - back to menu.")
            return
        if site in sites:
            print(c(f"'{site}' is already in your list.", YELLOW))
        else:
            sites.append(site)
            save_sites(sites)
            print(c(f"Added: {site}", GREEN))
            if block_is_on():
                apply_block(sites)
                print("Focus is ON, so the block was updated right away.")
        print("\n1. Add another site")
        print("2. Back to main menu")
        nxt = input("Enter option number: ").strip()
        if nxt != "1":
            return


def remove_site(sites):
    while True:
        if not sites:
            print("\nYour list is empty - nothing to remove.")
            return
        print("\nYour list:")
        for i, site in enumerate(sites, start=1):
            print(f"  {i}. {site}")
        choice = input("Number to remove (or Enter to cancel): ").strip()
        if not choice:
            print("Cancelled.")
            return
        try:
            index = int(choice) - 1
            removed = sites.pop(index)
        except (ValueError, IndexError):
            print("That number is not in the list - back to menu.")
            return
        save_sites(sites)
        print(c(f"Removed: {removed}", GREEN))
        if block_is_on():
            if sites:
                apply_block(sites)
            else:
                remove_block()
            print("Focus is ON, so the block was updated right away.")
        if not sites:
            print("Your list is now empty.")
            return
        print("\n1. Remove another site")
        print("2. Back to main menu")
        nxt = input("Enter option number: ").strip()
        if nxt != "1":
            return


RELOAD_HINT = (
    "For Brave to notice: restart it fully, or open brave://policy "
    "and click 'Reload policies'."
)


def print_menu():
    print("=== Brave Focus Toggle ===")
    print("1. Focus ON   (block sites)")
    print("2. Focus OFF  (remove block)")
    print("3. Show status and list")
    print("4. Add a site")
    print("5. Remove a site")
    print("6. Debloat Brave (one-way, no undo)")
    print("0. Exit")


def main():
    if not is_admin():
        print("Asking Windows for admin permission...")
        restart_as_admin()

    enable_colors()

    while True:
        sites = load_sites()
        print_menu()
        choice = input("\nEnter option number: ").strip()

        if choice == "1":
            focus_on(sites)
            print(RELOAD_HINT)
        elif choice == "2":
            focus_off()
            print(RELOAD_HINT)
        elif choice == "3":
            show_status(sites)
        elif choice == "4":
            add_site(sites)
        elif choice == "5":
            remove_site(sites)
        elif choice == "6":
            debloat_brave()
            print(RELOAD_HINT)
        elif choice == "0":
            print("\nBye.")
            return
        else:
            print(c("\nNot a valid option.", RED))
        print()


if __name__ == "__main__":
    main()
