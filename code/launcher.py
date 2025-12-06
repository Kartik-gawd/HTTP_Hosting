import sys
import os
import subprocess
import platform
import tkinter as tk
from tkinter import filedialog
import ctypes
import server

# Attach a console window when running as a frozen Windows executable
def attach_console():
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.FreeConsole()
            ctypes.windll.kernel32.AllocConsole()
            sys.stdout = open("CONOUT$", "w")
            sys.stderr = open("CONOUT$", "w")
        except Exception:
            pass

# Open a standard folder picker dialog and return the chosen path
def open_folder_picker():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_selected = filedialog.askdirectory(title="Select Folder to Serve")
    root.destroy()
    return folder_selected if folder_selected else None

# Launch the server script in a new console window depending on OS
def launch_server_process(target_folder):
    system = platform.system()
    
    # Determine how to pass args depending on if script is frozen or not
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        args = [executable, target_folder]
    else:
        executable = sys.executable
        script = os.path.abspath(__file__)
        args = [executable, script, target_folder]

    proc = None

    # Windows: open a new console
    if system == "Windows":
        proc = subprocess.Popen(
            args,
            close_fds=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
    # macOS: open the script in Terminal via AppleScript
    elif system == "Darwin":
        safe_args = " ".join(f'"{a}"' for a in args)
        osascript_cmd = f'tell application "Terminal" to do script "{safe_args}"'
        subprocess.run(['osascript', '-e', osascript_cmd])
        return None 
        
    # Linux: try common terminal emulators
    elif system == "Linux":
        terminals = ['gnome-terminal', 'xterm', 'konsole']
        for term in terminals:
            try:
                if term == 'gnome-terminal':
                    proc = subprocess.Popen([term, '--'] + args, close_fds=True)
                elif term == 'xterm':
                    proc = subprocess.Popen([term, '-e'] + args, close_fds=True)
                break
            except FileNotFoundError:
                continue
    
    return proc

# Main entry point: either run server directly or open folder picker
def main():
    if len(sys.argv) > 1:
        # Running as server instance with folder argument
        target_folder = sys.argv[1]
        
        # Attach console if running as packaged exe
        if getattr(sys, 'frozen', False):
            attach_console()
            
        # Set console title on Windows
        if sys.platform == "win32":
            os.system(f"title WiFi Server - {target_folder}")

        # Validate folder and run server
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

    else:
        # No folder passed in — prompt user to choose one
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
