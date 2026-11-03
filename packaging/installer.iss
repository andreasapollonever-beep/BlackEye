; Inno Setup script — builds Erisma-Setup.exe from dist\Erisma (see the GitHub workflow)
#define AppVersion GetEnv("ERISMA_VERSION")
[Setup]
AppId={{6F1E4C2A-8B7D-4E5F-9A31-ERISMA000001}
AppName=Erisma
AppVersion={#AppVersion}
AppPublisher=Erisma
DefaultDirName={autopf}\Erisma
DefaultGroupName=Erisma
OutputBaseFilename=Erisma-Setup-{#AppVersion}
OutputDir=..\dist
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\Erisma.exe

[Languages]
Name: "greek"; MessagesFile: "compiler:Languages\Greek.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\Erisma\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\docs\*.pdf"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{group}\Erisma"; Filename: "{app}\Erisma.exe"
Name: "{group}\Εγχειρίδιο Erisma"; Filename: "{app}\docs\Erisma_Egxeiridio.pdf"
Name: "{group}\{cm:UninstallProgram,Erisma}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Erisma"; Filename: "{app}\Erisma.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Erisma.exe"; Description: "{cm:LaunchProgram,Erisma}"; Flags: nowait postinstall skipifsilent
