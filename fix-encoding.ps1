# fix-encoding.ps1
param(
    [switch]$WithBackup = $false,
    [string]$Root = "."
)

Write-Host "🔎 Varredura em: $Root" -ForegroundColor Cyan

$backupDir = Join-Path $Root ".encoding_backup"

$pyFiles = Get-ChildItem -Path $Root -Recurse -Filter *.py |
    Where-Object { $_.FullName -notmatch "\\\.venv\\" -and $_.FullName -notmatch "\\htmlcov\\" }

if ($pyFiles.Count -eq 0) {
    Write-Host "Nenhum arquivo .py encontrado." -ForegroundColor Yellow
    exit 0
}

if ($WithBackup) {
    Write-Host "📦 Backup habilitado em: $backupDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $backupDir -ErrorAction SilentlyContinue | Out-Null
}

$errors = @()
foreach ($f in $pyFiles) {
    try {
        $rel = Resolve-Path -Relative $f.FullName
        Write-Host "➡️  Convertendo: $rel" -ForegroundColor Green

        if ($WithBackup) {
            $dest = Join-Path $backupDir $rel
            $destDir = Split-Path $dest -Parent
            New-Item -ItemType Directory -Path $destDir -ErrorAction SilentlyContinue | Out-Null
            Copy-Item -Path $f.FullName -Destination $dest -Force
        }

        $content = Get-Content -Path $f.FullName -Raw
        Set-Content -Path $f.FullName -Value $content -Encoding UTF8
    }
    catch {
        $errors += "Falha ao converter: $($f.FullName) — $($_.Exception.Message)"
    }
}

if ($errors.Count -gt 0) {
    Write-Host "`n⚠️ Ocorreram erros:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    exit 1
}

Write-Host "`n✅ Conversão concluída. Todos os .py foram regravados em UTF-8." -ForegroundColor Cyan

Write-Host "🔁 Verificando imports..." -ForegroundColor Cyan
try {
    python - << 'PYCODE'
import importlib
mods = [
    "clientes_api.app.main",
    "clientes_api.app.routers.clientes",
    "clientes_db.app.main",
    "clientes_db.app.routers.clientes",
]
for m in mods:
    importlib.import_module(m)
print("OK: imports funcionaram.")
PYCODE
} catch {
    Write-Host "⚠️ Verificação de import encontrou problemas." -ForegroundColor Yellow
}
