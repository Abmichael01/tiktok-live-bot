[Setup]
AppName=TikTokLiveBot
AppVersion=1.0
DefaultDirName={autopf}\TikTokLiveBot
DefaultGroupName=TikTokLiveBot
UninstallDisplayIcon={app}\TikTokLiveBot.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=TikTokLiveBot_Setup
SetupIconFile=icon.ico
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\TikTokLiveBot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TikTokLiveBot"; Filename: "{app}\TikTokLiveBot.exe"
Name: "{autodesktop}\TikTokLiveBot"; Filename: "{app}\TikTokLiveBot.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TikTokLiveBot.exe"; Description: "{cm:LaunchProgram,TikTokLiveBot}"; Flags: nowait postinstall skipifsilent
