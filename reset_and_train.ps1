# Script de reset total pour repartir sur un entrainement tout propre
# Shoko-official - 2026-02-05

$ErrorActionPreference = "Stop"

Write-Host "--- NETTOYAGE DES ANCIENNES DONNEES ---" -ForegroundColor Cyan

# On degage les vieux modeles et les logs de Tensorboard
$FoldersToDelete = @("models", "logs")

foreach ($folder in $FoldersToDelete) {
    if (Test-Path $folder) {
        Write-Host "Suppression de : $folder..." -ForegroundColor Yellow
        Remove-Item -Path $folder -Recurse -Force
    }
}

Write-Host "`n--- LANCEMENT DE L'ENTRAINEMENT ---" -ForegroundColor Green
Write-Host "Le bot va decouvrir les nouvelles regles anti-bunnyhop." -ForegroundColor Gray

# On s'assure d'etre au bon endroit pour les imports
$env:PYTHONPATH = "src"

# Lancement de l'entrainement dans une nouvelle fenetre pour voir les logs
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='src'; python src/rl/train_agent.py"

# Lancement de la preview visuelle dans la fenetre actuelle
Write-Host "Lancement de la preview visuelle..." -ForegroundColor Magenta
python watch_bot.py
