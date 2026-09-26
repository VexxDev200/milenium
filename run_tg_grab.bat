@echo off
chcp 866 >nul
cd /d C:\Users\smird\Downloads\milenium
python -m milenium.cli tg_grab "https://t.me/+3RnTj-8fCSs5OWQ0" "https://t.me/+mFFLoewnHoNjZWQy" "https://t.me/bazamydannix" "https://t.me/Free_Data_Base" "https://t.me/gosuslugi_ruu" "https://t.me/+CGN3PisJp1gzNzIy" "https://t.me/+kFlXTE50D2FjZDNi" "https://t.me/+imnDS9H3Pwg2MGMy" --accounts-file data/tg_accounts.json --output data/tg_dumps --limit 100000 --tg-upload-target "https://t.me/+pQduDv2K9gE2MTMy" --delete-local >> data/tg_grab.log 2>&1
echo DONE >> data/tg_grab.log
