Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\aubre\Desktop\New folder"
WshShell.Run "cmd /c run_bot.bat", 0, False
WshShell.Run "cmd /c run_dash.bat", 0, False
