; — Chiron Installer Inno Setup Script —

[Setup]
; Nome prodotto e versione
AppName=Chiron
AppVersion=0.1.0
; Cartella di default in Program Files
DefaultDirName={pf}\Chiron
; Crea icone sul Desktop e in Start Menu
DefaultGroupName=Chiron
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=Chiron-Installer
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Copia tutto il contenuto di C:\build\chiron\ in {app}\ 
Source: "*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
; Crea collegamento “Chiron” nel menu Start
Name: "{group}\Chiron"; Filename: "{app}\chiron.bat"
; (opzionale) icona desktop
Name: "{userdesktop}\Chiron"; Filename: "{app}\chiron.bat"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Registry]
; (opzionale) aggiungi {app} al PATH
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Flags: preservestringtype

[Run]
; (opzionale) al termine apri una finestra di conferma
Filename: "{app}\chiron.bat"; Description: "Run Chiron now"; Flags: nowait postinstall skipifsilent