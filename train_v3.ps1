# On se place dans le dossier du script pour que les chemins relatifs fonctionnent
Set-Location $PSScriptRoot

# Nettoyage des vieux logs v3 pour repartir sur une base propre
if (Test-Path "logs_v3") { Remove-Item -Recurse -Force "logs_v3" }

# On lance l'entraînement V3
Write-Host "--- LANCEMENT DE L'ENTRAINEMENT IA SUPER BASE V3 ---" -ForegroundColor Cyan
python src/rl/train_agent_v3.py
