"""
Creates or refreshes the StudyShield desktop shortcut on the Windows desktop / home screen.
"""

import os
import sys

def create_shortcut():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "StudyShield.lnk")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_script = os.path.join(script_dir, "desktop_app.py")
    ico_path = os.path.join(script_dir, "studyshield.ico")
    
    # Locate pythonw.exe to prevent terminal window from popping up
    python_dir = os.path.dirname(sys.executable)
    pythonw_exe = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = sys.executable

    import subprocess
    ps_cmd = f'''
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{pythonw_exe}"
    $Shortcut.Arguments = '"{app_script}"'
    $Shortcut.WorkingDirectory = "{script_dir}"
    $Shortcut.IconLocation = "{ico_path},0"
    $Shortcut.Description = "StudyShield — AI Focus & Preference Control"
    $Shortcut.Save()
    '''
    subprocess.run(["powershell", "-Command", ps_cmd], check=True)
    print(f"Created desktop shortcut: {shortcut_path}")

if __name__ == "__main__":
    create_shortcut()
