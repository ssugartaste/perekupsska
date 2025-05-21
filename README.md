 Perekupsska
Telegram bots, kas seko jaunam SS.lv sludinajumu publikacijam un automatiski suta tos saviem abonentiem---
 Funkcionalitate
- Lietotaja registracija un vina aktivo URL saglabasana
- Jaunu meklesanas URL pievienosana ar komandu `/addurl <URL>`
- Periodiska skenesana: parbauda visus unikalaos URL, lai atrastu jaunus sludinajumus
- Sludinajuma detalu parsesana: modelis, cena, nobraukums, foto
- Pazinojumu sutisana ar foto un isu aprakstu par katru jauno sludinajumu
- Redzeto sludinajumu uzskaite, lai izvairitos no dubletiem pazinojumiem
---
 Projektu struktura
perekupsska/
db.py  SQLite datu bazes logika (tabulas: users, user_urls, seen_ads)
main.py  Galvenais bota kods (Aiogram)
test.py  Viegls echo-bots testa vajadibam
requirements.txt  Atkaribas
main.env  Vides mainigie (nav repozitorija)
bot_database.sqlite  Automatiski genereta datu baze
---
 Instalacija
1. Klonet repozitoriju:
 git clone https://github.com/ssugartaste/perekupsska.git
 cd perekupsska
2. Izveidot un aktivizet virtualo vidi:
 python3 -m venv venv
 source venv/bin/activate
3. Uzstadit atkaribas:
 pip install -r requirements.txt
---
 Konfiguracija
1. Iegustiet bot tokenu no @BotFather (https://t.me/BotFather).
2. Izveidojiet failu `main.env` projekta sakne un pievienojiet:
 BOT_TOKEN=JUSU_BOT_TOKEN
---
 Palaisana
python main.py
- Bots saks skenet pievienotos URL ik pec 10 sekundem.
- Telegram cata nosutiet:
 1. /start — lai registretos
 2. /addurl <SS.lv URL> — lai pievienotu jaunu meklesanas saiti
---
## Testesana
python test.py (izmantojiet to pasu BOT_TOKEN no main.env)
