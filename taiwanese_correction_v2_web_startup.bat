@echo off
rem ���ñҰ�.bat����k
if "%1"=="hide" goto CmdBegin
start mshta vbscript:createobject("wscript.shell").run("""%~0"" hide",0)(window.close)&&exit
:CmdBegin
rem ����A��python�ɮסA�ѩ�O�n���u�@�Ƶ{������A�ҥH�n�g�W������|�B�]�Apython�����۹���|���n�令������|�C
python3 "C:\Program Files\Taiwanese_Correction\Taiwanese_Correction_v2\app.py"
rem �s�g�����ɮ׫�A�N���[�Jwindows���u�@�Ƶ{�����A�]�w�n�JĲ�o�C