; Установщик Склей-ки. Собирается через build_installer.bat
#define AppName "Sclayka"
#define AppVersion "1.1.0"
#define AppPublisher "Койне-софт"
#define AppExe "Sclayka.exe"

[Setup]
AppId={{28F903AF-95CA-4912-864F-5649B6E4A21F}
AppName={cm:LocalizedAppName}
AppVersion={#AppVersion}
AppVerName={cm:NameAndVersion,{cm:LocalizedAppName},{#AppVersion}}
AppPublisher={#AppPublisher}
VersionInfoDescription={#AppName} Setup
VersionInfoProductName={#AppName}
VersionInfoVersion={#AppVersion}
; По умолчанию ставится только для текущего пользователя — права администратора не нужны.
; В начале можно выбрать установку для всех пользователей.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\Sclayka
DefaultGroupName={cm:LocalizedAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Sclayka-setup-{#AppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={cm:LocalizedAppName}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
en.LocalizedAppName=Sclayka
ru.LocalizedAppName=Склей-ка

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\Sclayka\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{cm:LocalizedAppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{cm:UninstallProgram,{cm:LocalizedAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{cm:LocalizedAppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{cm:LocalizedAppName}}"; Flags: nowait postinstall skipifsilent
