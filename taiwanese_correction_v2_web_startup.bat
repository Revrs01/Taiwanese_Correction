@echo off
rem 隱藏啟動.bat的方法
if "%1"=="hide" goto CmdBegin
start mshta vbscript:createobject("wscript.shell").run("""%~0"" hide",0)(window.close)&&exit
:CmdBegin
rem 執行你的python檔案，由於是要給工作排程器執行，所以要寫上絕對路徑、包括python內的相對路徑都要改成絕對路徑。
python3 "C:\Program Files\Taiwanese_Correction\Taiwanese_Correction_v2\app.py"
rem 編寫完此檔案後，將它加入windows的工作排程器中，設定登入觸發。