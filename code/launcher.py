import sys
import os
import subprocess
import platform
import ctypes
import shlex  

try:
    import tkinter as tk
    from tkinter import filedialog
    TK_AVAILABLE = True
except Exception:
    tk = None
    filedialog = None
    TK_AVAILABLE = False

import server

def attach_console():
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.FreeConsole()
            ctypes.windll.kernel32.AllocConsole()
            sys.stdout = open("CONOUT$", "w")
            sys.stderr = open("CONOUT$", "w")
        except Exception:
            pass

def _escape_applescript_arg(arg: str) -> str:
    # Basic escaping for AppleScript strings
    return arg.replace("\\", "\\\\").replace('"', '\\"')

def open_folder_picker():
    system = platform.system()

    # Tkinter GUI dialog
    if TK_AVAILABLE:
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_selected = filedialog.askdirectory(title="Select Folder to Serve")
            root.destroy()
            if folder_selected:
                return folder_selected
        except Exception:
            pass

    # OS-native fallbacks (no Tkinter)
    
    # macOS: use AppleScript
    if system == "Darwin":
        try:
            script = 'POSIX path of (choose folder with prompt "Select Folder to Serve")'
            result = subprocess.run(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            folder = result.stdout.strip()
            if folder:
                return folder
        except Exception:
            pass

    # Linux: try zenity or kdialog
    if system == "Linux":
        zenity_cmd = ["zenity", "--file-selection", "--directory", "--title=Select Folder to Serve"]
        kdialog_cmd = ["kdialog", "--getexistingdirectory", os.path.expanduser("~")]

        for cmd in (zenity_cmd, kdialog_cmd):
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                folder = result.stdout.strip()
                if folder:
                    return folder
            except (FileNotFoundError, Exception):
                continue
    # CLI input
    print("\n--- Folder Selection ---")
    while True:
        try:
            path_input = input("Enter folder path to serve (or 'q' to quit): ").strip('"').strip()
            if path_input.lower() == 'q':
                return None
            if not path_input:
                continue # Ignore empty enter presses
                
            if os.path.isdir(path_input):
                return path_input
            else:
                print(f"Error: '{path_input}' is not a valid directory. Try again.")
        except (EOFError, KeyboardInterrupt):
            return None

def launch_server_process(target_folder):
    system = platform.system()

    if getattr(sys, 'frozen', False):
        executable = sys.executable
        args = [executable, target_folder]
    else:
        executable = sys.executable
        script_path = os.path.abspath(__file__)
        args = [executable, script_path, target_folder]

    proc = None

    if system == "Windows":
        proc = subprocess.Popen(
            args,
            close_fds=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

    elif system == "Darwin":
        safe_args = " ".join(f'"{_escape_applescript_arg(a)}"' for a in args)
        osascript_cmd = f'tell application "Terminal" to do script "{safe_args}"'
        try:
            subprocess.run(['osascript', '-e', osascript_cmd])
            # macOS Terminal launches async; we don't get a Popen object back usually
            return None 
        except Exception as e:
            print(f"Failed to launch Terminal: {e}")
            print("Running server in the current process instead.")
            run_server_in_process(target_folder)
        return None

    elif system == "Linux":
        terminals = [
            "gnome-terminal", "xfce4-terminal", "konsole", "lxterminal",
            "tilix", "mate-terminal", "qterminal", "terminator",
            "alacritty", "xterm"
        ]

        for term in terminals:
            try:
                if term == "gnome-terminal":
                    proc = subprocess.Popen([term, "--"] + args, close_fds=True)
                
                elif term == "xfce4-terminal":
                    safe_command = " ".join(shlex.quote(arg) for arg in args)
                    proc = subprocess.Popen(
                        [term, "--command", safe_command],
                        close_fds=True,
                    )
                
                elif term in ["konsole", "lxterminal", "tilix", "mate-terminal", 
                              "qterminal", "terminator", "alacritty", "xterm"]:
                    proc = subprocess.Popen([term, "-e"] + args, close_fds=True)
                else:
                    continue
                break
            except (FileNotFoundError, Exception):
                proc = None
                continue

        if proc is None:
            print("Could not find a suitable terminal emulator.")
            print("Running server in the current process instead.")
            run_server_in_process(target_folder)
            return None

    return proc

def run_server_in_process(target_folder):
    if os.path.isdir(target_folder):
        server.FOLDER_TO_SERVE = target_folder
        try:
            server.run_server()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"Critical Error: {e}")
            input("Press Enter to exit...")
    else:
        print("Error: Invalid folder path.")
        input("Press Enter to exit...")

def main():
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]
        if getattr(sys, 'frozen', False):
            attach_console()
        if sys.platform == "win32":
            os.system(f"title WiFi Server - {target_folder}")
        run_server_in_process(target_folder)
    else:
        folder = open_folder_picker()
        if folder:
            process = launch_server_process(folder)
            if process:
                try:
                    process.wait()
                except KeyboardInterrupt:
                    pass
        sys.exit()

if __name__ == "__main__":
    main()
