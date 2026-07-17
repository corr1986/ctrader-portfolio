@echo off
REM Sabato 10:00 - genera il recap settimanale X e lo invia su Telegram (pubblicazione manuale).
cd /d "C:\Users\corr8\Desktop\obsidian-vault\ctrader-portfolio"
git pull --rebase origin main >> weekly_recap.log 2>&1
"C:\Users\corr8\AppData\Local\Programs\Python\Python314\python.exe" -m copyfunnel.weekly_recap --no-link --telegram >> weekly_recap.log 2>&1
