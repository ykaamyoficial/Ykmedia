#define AppName "YkMedia"
#define AppVersion "0.3.3"
#define AppPublisher "YkMedia"

[Setup]
AppId={{C32EA060-C739-4E2C-B2B9-86E9BB878A28}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=output
OutputBaseFilename=YkMedia-Setup-{#AppVersion}-x64
SetupIconFile=..\src-tauri\icons\icon.ico
UninstallDisplayIcon={app}\YkMedia.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\src-tauri\target\release\ykmedia.exe"; DestDir: "{app}"; DestName: "YkMedia.exe"; Flags: ignoreversion
Source: "..\src-tauri\target\release\ykmedia-backend.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\YkMedia.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\YkMedia.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Run]
Filename: "{app}\YkMedia.exe"; Description: "Abrir o YkMedia"; Flags: nowait postinstall skipifsilent

[Code]
function StopYkMediaProcesses(): Boolean;
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM YkMedia.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM ykmedia-backend.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  StopYkMediaProcesses();
  Result := '';
end;
