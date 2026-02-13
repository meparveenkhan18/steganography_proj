@echo off
setlocal

echo checking for git from PATH...
where git >nul 2>nul
if %errorlevel% equ 0 (
    echo Git found in PATH.
    goto :found_path
)

echo Git not found in PATH. Checking common locations...
if exist "C:\Program Files\Git\cmd\git.exe" (
    set "PATH=%PATH%;C:\Program Files\Git\cmd"
    echo Found Git in Program Files. Added to PATH temporarily.
    goto :found_path
)

if exist "C:\Program Files (x86)\Git\cmd\git.exe" (
    set "PATH=%PATH%;C:\Program Files (x86)\Git\cmd"
    echo Found Git in Program Files (x86). Added to PATH temporarily.
    goto :found_path
)

echo Git is still not found.
echo Please ensure Git is installed correctly or add it to your PATH manually.
pause
exit /b

:found_path
echo.
if exist ".git" (
    echo Repository already initialized.
    goto :push_logic
)

echo Initializing Git repository...
git init
if %errorlevel% neq 0 goto :error

echo Adding files...
git add .
if %errorlevel% neq 0 goto :error

echo Committing files...
git commit -m "Initial commit of Steganography Web App"
if %errorlevel% neq 0 goto :error

echo.
echo Repository initialized and committed successfully!

:push_logic
echo.
echo ---------------------------------------------------------
echo                 PUSH TO REMOTE (GitHub/GitLab)
echo ---------------------------------------------------------
echo.
set /p push_choice="Do you want to push to a remote repository now? (Y/N): "
if /i "%push_choice%" neq "Y" goto :finish

echo.
echo Please enter your remote repository URL (e.g., https://github.com/username/repo.git):
set /p remote_url="Remote URL: "

if "%remote_url%"=="" (
    echo No URL provided. Exiting.
    goto :finish
)

echo.
echo Setting remote 'origin' to %remote_url%...
git remote add origin %remote_url% 2>nul
if %errorlevel% neq 0 (
    echo Remote 'origin' might already exist. Updating it...
    git remote set-url origin %remote_url%
)

echo.
echo Renaming branch to 'main'...
git branch -M main

echo.
echo Pushing to remote...
echo (You may be asked to sign in via a browser window or enter credentials)
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Project pushed to remote repository!
) else (
    echo.
    echo ERROR: Push failed. Please check your URL and credentials.
)

:finish
echo.
echo Done.
pause
exit /b

:error
echo An error occurred. Please check the output above.
pause
