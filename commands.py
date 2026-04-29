import os
import subprocess

class CommandHandler:
    def __init__(self):
        self.commands = {
            "calc": self.open_calculator,
            "notepad": self.open_notepad,
            "cmd": self.open_command_prompt,
            "powershell": self.open_powershell,
            "explorer": self.open_explorer,
            "settings": self.open_settings,
            "browser": self.open_browser,
        }
    
    def open_calculator(self):
        subprocess.Popen("calc.exe")
    
    def open_notepad(self):
        subprocess.Popen("notepad.exe")
    
    def open_command_prompt(self):
        subprocess.Popen("cmd.exe")
    
    def open_powershell(self):
        subprocess.Popen("powershell.exe")
    
    def open_explorer(self):
        subprocess.Popen("explorer.exe")
    
    def open_settings(self):
        subprocess.Popen("start ms-settings:")
    
    def open_browser(self):
        subprocess.Popen("start https://www.google.com")
    
    def execute(self, command):
        cmd = command.lower().strip()
        if cmd in self.commands:
            self.commands[cmd]()
            return True
        return False
    
    def get_command_list(self):
        return list(self.commands.keys())