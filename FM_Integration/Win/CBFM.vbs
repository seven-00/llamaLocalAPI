Set WshShell = CreateObject("WScript.Shell")

' Define the log file
logFile = "installation_log.txt"

' Start logging
Call WriteLog("Log file started at " & Now)

' Check if Python is installed
Call WriteLog("Checking for Python installation...")
pythonCheck = RunCommand("python --version")
If pythonCheck <> 0 Then
    Call WriteLog("Python is not installed. Installing Python...")
    
    ' Install Python 3.3 silently via winget
    Call WriteLog("Installing Python 3.3...")
    wingetInstall = RunCommand("winget install -e --id Python.Python.3.3")
    
    ' Check if Python installed correctly
    pythonCheck = RunCommand("python --version")
    If pythonCheck <> 0 Then
        Call WriteLog("Python installation failed. Exiting...")
        WScript.Quit
    End If
    Call WriteLog("Python 3.3 successfully installed.")
Else
    Call WriteLog("Python is already installed. Checking version...")

    ' Check Python version
    pythonCheck = RunCommand("python --version")
    If pythonCheck >= 3.3 Then
        Call WriteLog("Python version is sufficient.")
    Else
        Call WriteLog("Python version is lower than 3.3. Upgrading to Python 3.3...")
        wingetInstall = RunCommand("winget install -e --id Python.Python.3.3")
        
        ' Check if Python 3.3 installed correctly
        pythonCheck = RunCommand("python --version")
        If pythonCheck <> 0 Then
            Call WriteLog("Python installation failed. Exiting...")
            WScript.Quit
        End If
        Call WriteLog("Python 3.3 successfully installed and upgraded.")
    End If
End If

' Set up a virtual environment
Call WriteLog("Setting up the virtual environment...")
RunCommand("python -m venv venv")

' Activate the virtual environment and run commands
Call WriteLog("Running commands in the virtual environment...")

' Use the full path to the virtual environment's python executable
venv_python = "venv\Scripts\python.exe"

' Upgrade pip in the virtual environment
Call RunCommand(venv_python & " -m pip install --upgrade pip")

' Install required libraries
Call RunCommand(venv_python & " -m pip install flask requests pypdf flask-session redis")

' Check if Redis is running via WSL
Call WriteLog("Checking Redis status in WSL...")
redisCheck = RunCommand("wsl redis-cli ping")
If redisCheck <> 0 Then
    Call WriteLog("Redis server is not running. Starting Redis in WSL...")
    RunCommand("wsl sudo service redis-server start")
End If

' Deactivate the virtual environment
Call WriteLog("Deactivation of virtual environment is handled automatically.")

Call WriteLog("Installation complete.")

' Write to log file
Sub WriteLog(message)
    Set objFSO = CreateObject("Scripting.FileSystemObject")
    Set objFile = objFSO.OpenTextFile(logFile, 8, True)
    objFile.WriteLine message
    objFile.Close
End Sub

' Run a command and return the exit code, minimized
Function RunCommand(cmd)
    WshShell.Run cmd, 2, True ' The '2' here means "minimized"
    RunCommand = WshShell.Exec(cmd).ExitCode
End Function
