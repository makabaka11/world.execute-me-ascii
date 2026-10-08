param([Parameter(ValueFromRemainingArguments = $true)][string[]]$PlayerArgs)
$ErrorActionPreference = 'Stop'
$mvRoot = $PSScriptRoot
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'

$mvPython = $null
foreach ($mvName in @('python', 'python3', 'py')) {
    $mvCommand = Get-Command $mvName -ErrorAction SilentlyContinue
    if ($mvCommand -and $mvCommand.Source -notmatch '\\WindowsApps\\') {
        $mvPython = $mvCommand.Source
        break
    }
}
if (-not $mvPython) {
    foreach ($mvBase in @("$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles\Python")) {
        if (Test-Path -LiteralPath $mvBase) {
            $mvCandidate = Get-ChildItem -LiteralPath $mvBase -Filter python.exe -Recurse |
                Sort-Object FullName -Descending | Select-Object -First 1
            if ($mvCandidate) { $mvPython = $mvCandidate.FullName; break }
        }
    }
}
if (-not $mvPython) { throw 'Python 3.9+ is required. Install Python or add it to PATH.' }
$mvPlayer = Join-Path $mvRoot 'player.py'
if (-not (Test-Path -LiteralPath $mvPlayer)) { $mvPlayer = Join-Path $mvRoot 'world-execute-mv.pyz' }
& $mvPython -X utf8 $mvPlayer @PlayerArgs
exit $LASTEXITCODE
