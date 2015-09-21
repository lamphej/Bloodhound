import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os", "scapy"], "excludes": ["tkinter"]}

setup(  name = "TrafficMonitor",
        version = "0.1",
        description = "Traffic Monitoring System",
        options = {"build_exe": build_exe_options},
        executables = [Executable("main.py")])