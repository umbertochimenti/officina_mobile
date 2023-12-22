cd officine_mobili

PERSONAL_TOKEN=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
PASSWD=GHJ786%%$$dsdba123
USERNAME=umbertochimenti
FULL_URL_GIT=https://$USERNAME:$PERSONAL_TOKEN@github.com/umbertochimenti/officina_mobile.git
# echo $FULL_URL_GIT
git commit -m "review update code"
git remote set-url origin $FULL_URL_GIT
git push -u origin main


# git remote set-url origin https://<PERSONAL_TOKEN>@github.com/umbertochimenti/officina_mobile.git
