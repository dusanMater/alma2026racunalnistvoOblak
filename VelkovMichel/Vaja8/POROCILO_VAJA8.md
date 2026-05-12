# Vaja 8 - Prehod iz EC2 MariaDB na AWS RDS

**Student:** Velkov Michel  
**Datum:** 20. 4. 2026  
**Predmet:** Računalništvo v oblaku in mobilne rešitve

---

## 1) Namen naloge

Namen vaje je bil razumeti razliko med podatkovno bazo, ki jo sami namestimo na EC2 instanco, in podatkovno bazo, ki jo uporabljamo kot upravljano storitev AWS RDS.

V prejšnji vaji je bila podatkovna baza nameščena neposredno na EC2 instanci. V tej vaji sem aplikacijo prestavil tako, da spletna aplikacija še vedno teče na EC2 instanci, podatkovna baza pa teče na AWS RDS instanci.

Cilji naloge:

- razumeti, kaj je RDS,
- ustvariti RDS podatkovno bazo,
- pripraviti DB subnet group,
- nastaviti RDS security group,
- omogočiti dostop do RDS samo iz EC2 spletnega strežnika,
- povezati PHP aplikacijo na RDS,
- preveriti vnos in izpis podatkov iz RDS,
- primerjati EC2 podatkovno bazo in RDS.

---

## 2) Teoretični del predavanja

### 2.1 Kaj je EBS in zakaj je pomemben pri EC2 podatkovni bazi?

EBS pomeni Elastic Block Store. To je trajni disk, ki je povezan z EC2 instanco. Če na EC2 instanci namestimo podatkovno bazo, se podatki hranijo na EBS disku.

Prednost EBS je, da ga lahko povečamo, ko zmanjkuje prostora. Pri fizičnem računalniku bi morali pogosto kupiti nov disk, ustaviti sistem in ga ročno zamenjati. Pri AWS lahko velikost EBS diska povečamo prek oblaka, nato pa moramo v operacijskem sistemu razširiti še particijo oziroma datotečni sistem.

Pri EC2 podatkovni bazi smo sami odgovorni za:

- velikost in vzdrževanje diska,
- varnostne kopije,
- nadgradnje sistema,
- nadzor delovanja,
- varnostne nastavitve,
- obnovo ob napaki.

### 2.2 Povečanje zmogljivosti: up/down in in/out

Pri EC2 instancah lahko zmogljivost povečujemo na dva načina.

**Up/down scaling** pomeni, da eni instanci spremenimo velikost. Na primer instanci dodamo več CPU moči, RAM-a ali boljšo omrežno prepustnost. Pri tem moramo instanco običajno ustaviti, spremeniti tip instance in jo ponovno zagnati.

**In/out scaling** pomeni, da dodamo več instanc. Namesto da povečamo eno instanco, dodamo več strežnikov, promet pa razporejamo z load balancerjem. To je osnova za auto scaling.

### 2.3 Kaj je AWS RDS?

RDS pomeni Relational Database Service. To je upravljana storitev za relacijske podatkovne baze. Namesto da sami nameščamo in vzdržujemo podatkovni strežnik na EC2, AWS za nas pripravi in upravlja podatkovno storitev.

RDS lahko uporablja različne pogone podatkovnih baz, na primer MySQL, MariaDB, PostgreSQL in druge. V tej vaji je bila uporabljena RDS instanca z MySQL pogonom, do katere sem se povezal z MariaDB odjemalcem, ker je protokol združljiv.

RDS je primer upravljane oziroma managed storitve. To pomeni, da veliko operativnega dela prevzame AWS.

### 2.4 Primerjava EC2 podatkovne baze in RDS

| Lastnost       | Podatkovna baza na EC2                    | RDS                                               |
| -------------- | ----------------------------------------- | ------------------------------------------------- |
| Namestitev     | Ročna namestitev MariaDB/MySQL            | AWS ustvari DB instanco                           |
| Upravljanje OS | Upravljamo sami                           | AWS upravlja osnovno infrastrukturo               |
| Backup         | Sami nastavimo in izvajamo                | RDS podpira avtomatske varnostne kopije           |
| Posodobitve    | Sami posodabljamo sistem in DB            | RDS lahko pomaga pri vzdrževanju                  |
| Varnost        | Sami nastavimo OS, firewall, DB pravice   | Še vedno moramo nastaviti SG, uporabnike in gesla |
| Cena           | Lahko cenejše, več dela                   | Dražje, manj ročnega dela                         |
| Fleksibilnost  | Več nadzora                               | Manj nizkonivojskega nadzora                      |
| Primerno za    | Učenje, posebne nastavitve, popoln nadzor | Produkcijske baze, manj administracije            |

RDS ne pomeni, da je vse avtomatsko varno. Še vedno moramo pravilno nastaviti security group, gesla, uporabnike in dostop do podatkov.

### 2.5 Kaj RDS potrebuje za pravilno delovanje?

Za RDS potrebujemo:

1. **VPC**, v katerem deluje aplikacija.
2. **Vsaj dva subneta v različnih Availability Zone**, ker RDS zahteva DB subnet group z več subneti.
3. **DB subnet group**, ki pove, v katerih subnetih lahko RDS deluje.
4. **Security group za RDS**, ki določa, kdo se lahko poveže na podatkovno bazo.
5. **EC2 spletni strežnik**, ki se poveže na RDS endpoint.
6. **RDS endpoint**, ki ga aplikacija uporablja namesto lokalnega IP naslova podatkovne baze.

---

## 3) Arhitektura pred in po spremembi

### 3.1 Arhitektura pred spremembo

Pred vajo 8 je bila arhitektura naslednja:

- spletna aplikacija je tekla na EC2 instanci v javnem subnetu,
- MariaDB podatkovna baza je tekla na EC2 instanci v privatnem subnetu,
- aplikacija se je na bazo povezovala prek privatnega IP naslova EC2 podatkovnega strežnika.

### 3.2 Arhitektura po spremembi

Po spremembi je arhitektura naslednja:

- spletna aplikacija ostane na EC2 instanci v javnem subnetu,
- podatkovna baza teče na AWS RDS instanci,
- RDS je v privatnih subnetih oziroma DB subnet group,
- RDS nima javnega dostopa,
- dostop do RDS je dovoljen samo iz security group spletne EC2 instance,
- aplikacija se na bazo poveže prek RDS endpointa.

S tem je podatkovna baza bolje ločena od spletnega strežnika in ni neposredno dostopna z interneta.

---

## 4) Priprava RDS odvisnosti

Za RDS sem uporabil že obstoječo infrastrukturo iz vaje 6-7, kjer so bili ustvarjeni VPC, javni subnet za spletni strežnik in privatna subneta za podatkovno plast.

Ustvarjeno oziroma uporabljeno je bilo:

- dva privatna subneta v različnih AZ,
- DB subnet group,
- RDS security group,
- inbound pravilo na RDS SG za MySQL port 3306,
- source za port 3306 je bil nastavljen na security group spletne EC2 instance.

Pomembno je, da RDS security group ne dovoljuje dostopa iz `0.0.0.0/0`, ampak samo iz security group spletnega strežnika.

Dokazi:

![DB subnet group](slike/rds/01-db-subnet-group.png)

![RDS security group pravila](slike/rds/02-rds-sg-rules.png)

---

## 5) Ustvarjanje RDS instance

Za RDS instanco sem uporabil naslednje nastavitve:

- Engine: MySQL,
- razred instance: db.t3.micro,
- velikost diska: 20 GB,
- Public access: No,
- Credentials: self managed,
- VPC: isti VPC kot spletna aplikacija,
- DB subnet group: privatna subneta,
- Security group: RDS SG,
- DB name: `nakupni_seznam`.

RDS je bil ustvarjen kot privatna podatkovna baza, zato ni neposredno dosegljiv iz interneta. Do njega lahko dostopa samo spletna EC2 instanca prek varnostnih pravil.

Dokazi:

![RDS create settings](slike/rds/03-rds-create-settings.png)

![RDS endpoint in status available](slike/rds/04-rds-endpoint-available.png)

---

## 6) Povezava EC2 aplikacije na RDS

Na spletni EC2 instanci sem namestil `mariadb-client`, da sem lahko iz EC2 preveril povezavo na RDS endpoint.

Primer povezave:

```bash
mariadb -h <RDS_ENDPOINT> -u admin -p
```

Po uspešni povezavi sem na RDS ustvaril podatkovno bazo, tabelo in testne podatke.

Uporabljena baza:

```sql
CREATE DATABASE IF NOT EXISTS nakupni_seznam;
USE nakupni_seznam;
```

Uporabljena tabela:

```sql
CREATE TABLE IF NOT EXISTS nakup (
  id INT AUTO_INCREMENT PRIMARY KEY,
  element VARCHAR(255) NOT NULL,
  kolicina INT NOT NULL
);
```

Vstavljeni testni podatki:

```sql
INSERT INTO nakup (element, kolicina)
VALUES ('kruh', 1), ('mleko', 2), ('pivo', 6);
```

Dokazi:

![EC2 test povezava na RDS](slike/povezava/01-ec2-rds-connect-test.png)

![CREATE DATABASE in CREATE TABLE](slike/povezava/02-create-db-table.png)

![Seed podatki v RDS](slike/povezava/03-seed-data.png)

---

## 7) Posodobitev PHP aplikacije

V aplikaciji sem posodobil `config.php`, da se ne povezuje več na EC2 podatkovni strežnik, ampak na RDS endpoint.

Prej je aplikacija uporabljala privatni IP naslov EC2 podatkovnega strežnika. Po spremembi uporablja RDS endpoint.

PHP aplikacija vsebuje:

- `index.html` - obrazec za vnos elementa in količine,
- `vstavi.php` - vstavi podatke v tabelo `nakup`,
- `izpis.php` - izpiše podatke iz tabele `nakup`,
- `config.php` - nastavitve za povezavo na RDS,
- `style.css` - oblikovanje spletne strani.

Spletna aplikacija je torej ostala enaka po funkcionalnosti, spremenjen je bil predvsem cilj povezave do podatkovne baze.

---

## 8) Test aplikacije

Po povezavi aplikacije na RDS sem preveril:

- da se začetna stran odpre,
- da obrazec za vnos deluje,
- da se nov podatek shrani v RDS,
- da izpis prikaže podatke iz RDS.

Dokazi:

![Web index](slike/app/01-web-index.png)

![Web insert success](slike/app/02-web-insert-success.png)

![Web izpis](slike/app/03-web-izpis.png)

---

## 9) Varnost in odgovornosti

Pri oblaku velja model deljene odgovornosti. AWS skrbi za fizično infrastrukturo, podatkovne centre, osnovno strojno opremo in del upravljanja storitve RDS. Uporabnik pa je še vedno odgovoren za pravilno konfiguracijo.

Moje odgovornosti pri tej nalogi:

- pravilna nastavitev security group,
- RDS ne sme biti javno dostopen,
- uporaba močnih gesel,
- varovanje dostopnih ključev,
- varovanje `rds_outputs.env`, ker vsebuje občutljive podatke,
- pravilne pravice uporabnikov podatkovne baze,
- preverjanje stroškov in brisanje oziroma ustavitev virov po koncu dela.

Opomba: V šolski nalogi so bila gesla uporabljena za testno okolje. V produkcijskem okolju gesel ne bi smeli hraniti neposredno v skriptah ali jih nalagati v GitHub repozitorij.

---

## 10) Stroški in upravljanje virov

AWS storitve niso vedno brezplačne. RDS lahko hitro povzroči stroške, če instanca ostane prižgana ali če uporablja večje vire. Zato je treba po koncu testiranja preveriti, ali je RDS še potreben.

Za čiščenje sem pripravil skripto, ki izbriše:

- RDS instanco,
- RDS security group,
- DB subnet group.

Pri brisanju RDS instance sem uporabil možnost brez final snapshota, ker gre za šolsko testno okolje. V resnem okolju bi bilo treba pred brisanjem narediti varnostno kopijo.

---

## 11) Odgovori na vprašanja

### 1. Kaj je RDS?

RDS je AWS upravljana storitev za relacijske podatkovne baze. Uporabniku ni treba ročno nameščati podatkovnega strežnika na EC2, ker AWS pripravi in upravlja podatkovno instanco.

### 2. Kakšna je glavna razlika med podatkovno bazo na EC2 in RDS?

Pri EC2 podatkovni bazi sami namestimo, nastavimo in vzdržujemo MariaDB/MySQL. Pri RDS veliko operativnega dela prevzame AWS, na primer pripravo instance, del vzdrževanja, možnost backupov in upravljanje podatkovne storitve.

### 3. Zakaj RDS potrebuje DB subnet group?

DB subnet group določa, v katerih subnetih lahko RDS deluje. AWS zahteva vsaj dva subneta v različnih Availability Zone, ker je RDS zasnovan za večjo razpoložljivost in možnost uporabe več AZ.

### 4. Zakaj RDS ne sme biti javno dostopen?

Podatkovna baza naj ne bo neposredno izpostavljena internetu. Če je RDS javno dostopen, se poveča možnost napadov in nepooblaščenega dostopa. Bolj varno je, da je RDS dosegljiv samo znotraj VPC in samo iz spletne EC2 instance.

### 5. Zakaj je bolje, da source v RDS security group nastavimo na EC2 security group in ne na IP naslov?

Security group je bolj stabilna in varna izbira kot IP naslov. Javni ali privatni IP naslov instance se lahko spremeni, security group pa ostane povezana z vlogo strežnika. Tako dovolimo dostop samo strežnikom, ki imajo pravo security group.

### 6. Kaj pomeni port 3306?

Port 3306 je privzeti omrežni port za MySQL oziroma MariaDB. Spletna aplikacija ga uporablja za povezavo na RDS podatkovno bazo.

### 7. Kaj je RDS endpoint?

RDS endpoint je DNS ime, prek katerega se aplikacija poveže na RDS podatkovno bazo. Namesto da uporabljamo IP naslov, uporabimo endpoint, ki ga poda AWS.

### 8. Kaj bi se zgodilo, če bi bil RDS SG odprt na 0.0.0.0/0 za port 3306?

Podatkovna baza bi bila dostopna iz interneta, kar je zelo nevarno. Poveča se možnost poskusov vdora, brute-force napadov in kraje podatkov.

### 9. Kaj pomeni managed storitev?

Managed storitev pomeni, da del upravljanja prevzame ponudnik storitve. Pri RDS AWS upravlja osnovno infrastrukturo in podatkovno storitev, uporabnik pa še vedno skrbi za konfiguracijo, dostop, uporabnike in podatke.

### 10. Kdaj bi izbral EC2 podatkovno bazo in kdaj RDS?

EC2 podatkovno bazo bi izbral, ko potrebujem popoln nadzor, posebne nastavitve ali nižje stroške in sem pripravljen sam upravljati sistem. RDS bi izbral, ko želim manj ročnega vzdrževanja, lažje upravljanje, večjo zanesljivost in možnost upravljanih funkcij.

---

## 12) Uporabljene skripte

### 12.1 `01_setup_rds.sh`

Skripta pripravi RDS okolje:

- poišče web EC2 instanco,
- po potrebi jo zažene,
- poišče VPC in security group spletne instance,
- poišče privatna subneta,
- ustvari RDS security group,
- dovoli MySQL promet samo iz web EC2 security group,
- ustvari DB subnet group,
- ustvari RDS instanco,
- počaka, da RDS postane `available`,
- izpiše RDS endpoint in ostale vrednosti v `rds_outputs.env`.

### 12.2 `02_migrate_app_to_rds.sh`

Skripta prestavi aplikacijo na RDS:

- prebere `rds_outputs.env`,
- najde SSH ključ,
- se poveže na web EC2 instanco,
- namesti `mariadb-client`,
- ustvari bazo, tabelo in uporabnika,
- vstavi testne podatke,
- posodobi `config.php`,
- testira `index.html`, `vstavi.php` in `izpis.php`.

### 12.3 `99_cleanup_rds.sh`

Skripta počisti RDS vire:

- izbriše RDS instanco,
- izbriše RDS security group,
- izbriše DB subnet group.

---

## 13) Seznam oddanih datotek

- `POROCILO_VAJA8.md`
- `scripts/01_setup_rds.sh`
- `scripts/02_migrate_app_to_rds.sh`
- `scripts/99_cleanup_rds.sh`
- `slike/rds/*`
- `slike/povezava/*`
- `slike/app/*`

---

## 14) Seznam zahtevanih screenshotov

- `slike/rds/01-db-subnet-group.png`
- `slike/rds/02-rds-sg-rules.png`
- `slike/rds/03-rds-create-settings.png`
- `slike/rds/04-rds-endpoint-available.png`
- `slike/povezava/01-ec2-rds-connect-test.png`
- `slike/povezava/02-create-db-table.png`
- `slike/povezava/03-seed-data.png`
- `slike/app/01-web-index.png`
- `slike/app/02-web-insert-success.png`
- `slike/app/03-web-izpis.png`

---

## 15) Zaključek

Naloga je bila uspešno izvedena. Obstoječo PHP spletno aplikacijo sem povezal z AWS RDS podatkovno bazo. S tem sem zamenjal self-managed MariaDB na EC2 z managed podatkovno bazo RDS.

Pri nalogi sem spoznal, da RDS poenostavi upravljanje podatkovne baze, vendar še vedno zahteva pravilne varnostne nastavitve. Najpomembnejše nastavitve so, da RDS ni javno dostopen, da je v DB subnet group z več subneti in da security group dovoljuje promet samo iz spletne EC2 instance.

Aplikacija je uspešno prikazala obrazec, shranila podatke v RDS in jih nato izpisala iz podatkovne baze.
