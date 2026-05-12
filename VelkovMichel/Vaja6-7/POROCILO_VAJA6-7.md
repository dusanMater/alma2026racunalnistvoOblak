# Vaja 6–7 - Varna infrastruktura za spletno aplikacijo in podatkovno bazo

**Študent:** Velkov Michel  
**Datum:** 14. 4. 2026  
**Predmet:** Računalništvo v oblaku in mobilne rešitve

## 1) Namen naloge

Namen vaje 6 in 7 je bil povezati omrežni del AWS oblaka, podatkovno bazo in spletno aplikacijo v eno delujočo rešitev. Pri vaji sem najprej pripravil lastno AWS infrastrukturo z VPC omrežjem, tremi podomrežji, usmerjanjem, Internet Gateway, NAT Gateway, varnostnimi skupinami in EC2 instancami. Nato sem na eni EC2 instanci pripravil spletni strežnik, na drugi podatkovni strežnik MariaDB, ter preveril, da PHP aplikacija na spletnem strežniku uspešno zapisuje in bere podatke iz podatkovne baze.

Vaja je združena kot **Vaja 6–7**, ker sta se 6. in 7. srečanje vsebinsko nadaljevala. V 6. srečanju je bil poudarek na omrežju, podomrežjih, CIDR računanju, Availability Zone, route table, Internet Gateway in podatkovni bazi. V 7. srečanju pa je bil poudarek na spletni aplikaciji, ki prek PHP dostopa do podatkovne baze na EC2.

---

## 2) Teoretični del - 6. srečanje

### 2.1 CIDR in računanje podomrežij

CIDR zapis določa velikost omrežja oziroma podomrežja. IPv4 naslov je sestavljen iz 32 bitov. Pri zapisu `/24` pomeni, da je 24 bitov namenjenih omrežnemu delu naslova, preostalih 8 bitov pa je namenjenih naslovom naprav oziroma hostov.

V tej vaji sem uporabil VPC naslovni prostor:

```text
192.168.0.0/24
```

To pomeni, da celoten VPC obsega naslove od `192.168.0.0` do `192.168.0.255`.

Podomrežja v tej vaji:

| Podomrežje   |               CIDR |     Velikost | Namen                   |
| ------------ | -----------------: | -----------: | ----------------------- |
| Sub1 public  |   `192.168.0.0/25` | 128 naslovov | javni subnet za web EC2 |
| Sub2 private | `192.168.0.128/26` |  64 naslovov | zasebni subnet za DB1   |
| Sub3 private | `192.168.0.192/27` |  32 naslovov | zasebni subnet za DB2   |

Izračun velikosti:

```text
/25 -> 2^(32-25) = 2^7 = 128 naslovov
/26 -> 2^(32-26) = 2^6 = 64 naslovov
/27 -> 2^(32-27) = 2^5 = 32 naslovov
```

V AWS niso vsi naslovi uporabni, ker AWS v vsakem subnetu rezervira nekaj IP naslovov za svoje potrebe. Kljub temu CIDR zapis določa osnovni naslovni prostor, iz katerega nato AWS dodeljuje naslove instancam.

### 2.2 Datacenter, Availability Zone in Region

**Datacenter** je fizična lokacija z veliko količino strežniške opreme, omrežja, diskov, električnega napajanja, hlajenja in varnostnih sistemov. V podatkovnih centrih dejansko tečejo oblačne storitve.

**Availability Zone (AZ)** je ena ali več ločenih podatkovnih lokacij znotraj iste regije. Namen AZ je večja razpoložljivost. Če ima ena lokacija težavo, lahko storitve še vedno delujejo v drugi AZ.

**Region** je večje geografsko območje, ki vsebuje več Availability Zone. V tej vaji sem uporabljal regijo:

```text
eu-central-1
```

Podomrežja sem razporedil v različne AZ:

| Subnet       | AZ            | Namen   |
| ------------ | ------------- | ------- |
| Sub1 public  | eu-central-1a | web EC2 |
| Sub2 private | eu-central-1b | DB1 EC2 |
| Sub3 private | eu-central-1c | DB2 EC2 |

S tem je infrastruktura bolj odporna na izpad posamezne AZ.

### 2.3 VPC, subnet, route table, Internet Gateway in NAT Gateway

**VPC (Virtual Private Cloud)** je zasebno omrežje v AWS oblaku. Znotraj VPC ustvarjamo podomrežja, EC2 instance, security group pravila, route table in povezave do interneta.

**Subnet** je manjši del VPC omrežja. V tej vaji sem uporabil en javni subnet in dva zasebna subneta.

**Route table** določa, kam se usmerja promet iz posameznega subneta. Če ima route table pot `0.0.0.0/0` do Internet Gateway, potem ima subnet pot do interneta in je javni subnet.

**Internet Gateway (IGW)** omogoča povezavo VPC omrežja z internetom. V tej vaji je bil Internet Gateway povezan z VPC in uporabljen za javni subnet, v katerem je web EC2 instanca.

**NAT Gateway** omogoča zasebnim instancam izhod v internet, na primer za `apt update` in nameščanje paketov. Zasebne instance prek NAT Gateway lahko dostopajo ven, vendar niso neposredno dosegljive iz interneta.

Poenostavljena skica:

```text
Internet
   |
Internet Gateway
   |
Public subnet 192.168.0.0/25
   |
WEB EC2 + Apache + PHP
   |
   | zasebna komunikacija po VPC
   |
Private subnet 192.168.0.128/26       Private subnet 192.168.0.192/27
DB1 EC2 + MariaDB                     DB2 EC2 + MariaDB
```

### 2.4 Security Groups

Security Group je navidezni požarni zid za EC2 instance. Z njim določimo, kateri promet je dovoljen do posamezne instance.

V tej vaji sem uporabil dve varnostni skupini:

| Security Group | Namen                         | Dovoljena vrata                           |
| -------------- | ----------------------------- | ----------------------------------------- |
| web SG         | dostop do spletnega strežnika | SSH 22 iz mojega IP, HTTP 80 iz interneta |
| db SG          | dostop do podatkovne baze     | SSH 22 iz web SG, MariaDB 3306 iz web SG  |

Podatkovna baza ni bila odprta neposredno na internet. Do nje je lahko dostopala samo web EC2 instanca prek zasebnega omrežja.

### 2.5 Podatkovna baza na EC2

Podatkovna baza je bila nameščena na EC2 instanci v zasebnem subnetu. Uporabil sem MariaDB, ki je relacijska podatkovna baza. V njej sem ustvaril bazo, tabelo, uporabnika in testne podatke.

Osnovni koraki:

```text
sudo apt update
sudo apt install mariadb-server
sudo systemctl enable mariadb
sudo systemctl start mariadb
```

Nato sem uredil konfiguracijo MariaDB tako, da se lahko nanjo poveže spletni strežnik znotraj VPC omrežja. V konfiguraciji je bila nastavljena možnost:

```text
bind-address = 0.0.0.0
```

To pomeni, da MariaDB ne posluša samo na lokalnem naslovu `127.0.0.1`, ampak sprejema povezave tudi iz dovoljenih omrežnih naslovov. Dostop pa je še vedno omejen z uporabniškimi pravicami v MariaDB in z AWS Security Group pravili.

---

## 3) Teoretični del - 7. srečanje

### 3.1 Web strežnik in podatkovni strežnik

Pri tej vaji sta vlogi ločeni:

- **web EC2**: strežnik s spletnim strežnikom Apache, PHP in PHP modulom za MySQL/MariaDB,
- **db EC2**: podatkovni strežnik z MariaDB.

Takšna delitev je bolj varna, ker spletna stran ni na istem strežniku kot podatkovna baza. Web strežnik mora biti javno dostopen uporabnikom, podatkovni strežnik pa mora ostati zaseben.

### 3.2 PHP program, ki dostopa do podatkovne baze

Spletna aplikacija je sestavljena iz naslednjih datotek:

| Datoteka     | Namen                                |
| ------------ | ------------------------------------ |
| `index.html` | obrazec za vnos elementa in količine |
| `config.php` | nastavitve povezave na MariaDB       |
| `vstavi.php` | shrani podatke iz obrazca v bazo     |
| `izpis.php`  | izpiše podatke iz baze               |
| `style.css`  | oblikovanje spletne strani           |

Delovanje aplikacije:

1. Uporabnik odpre `index.html`.
2. V obrazec vnese element in količino.
3. Obrazec pošlje podatke v `vstavi.php`.
4. `vstavi.php` se poveže na MariaDB in izvede SQL `INSERT`.
5. `izpis.php` se poveže na isto bazo in izvede SQL `SELECT`.
6. Brskalnik prikaže vse shranjene elemente iz tabele.

### 3.3 Zakaj web v javnem subnetu in DB v privatnem subnetu

Web strežnik mora biti v javnem subnetu, ker morajo uporabniki prek interneta dostopati do spletne strani. Zato ima web EC2 javni IP naslov in pot do interneta prek Internet Gateway.

Podatkovna baza mora biti v zasebnem subnetu, ker je ne želimo izpostaviti javnemu internetu. Do nje dostopa samo web EC2 instanca prek zasebnega IP naslova znotraj VPC. To zmanjša možnost napada in ščiti podatke.

---

## 4) Brisanje starih AWS storitev

Pred novo postavitvijo sem pobrisal stare vire, da ne bi prišlo do konflikta imen, podvojenih pravil ali nepotrebnih stroškov. Pobrisani oziroma očiščeni so bili:

- VPC,
- key pairs,
- security groups,
- route tables,
- internet gateways,
- S3,
- EC2.

Za čiščenje sem uporabil skripto:

```text
scripts/00_cleanup_old_resources.sh
```

![Zagon cleanup skripte](slike/cleanup/01-cleanup-script-run.png)
![Brez starih virov po ciscenju](slike/cleanup/02-no-old-resources.png)

---

## 5) Nova infrastruktura

Ustvarjena je bila naslednja topologija:

- VPC: `192.168.0.0/24`,
- Sub1 public: `192.168.0.0/25` v AZ `eu-central-1a`,
- Sub2 private: `192.168.0.128/26` v AZ `eu-central-1b`,
- Sub3 private: `192.168.0.192/27` v AZ `eu-central-1c`,
- 1 key pair za vse 3 EC2 instance,
- 2 security group: web in db,
- 3 EC2 instance: web, db1 in db2,
- Internet Gateway in public route table,
- NAT Gateway in private route table.

Glavna skripta za postavitev infrastrukture:

```text
scripts/01_setup_infra.sh
```

Ta skripta ustvari VPC, tri subnete, Internet Gateway, route table, NAT Gateway, key pair, security group pravila in EC2 instance.

![VPC](slike/infra/01-vpc.png)
![Subneti](slike/infra/02-subnets.png)
![Route tables](slike/infra/03-route-tables.png)
![IGW in NAT](slike/infra/04-igw-nat.png)
![Security groups](slike/infra/05-security-groups.png)
![EC2 instance](slike/infra/06-ec2-instances.png)

---

## 6) Namestitev in konfiguracija podatkovne baze

Podatkovna baza je bila nameščena na instanci DB1 v zasebnem subnetu. Za namestitev in konfiguracijo sem uporabil skripti:

```text
scripts/02_configure_db1.sh
scripts/helper_db1_commands.sh
```

Skripta naredi naslednje:

- namesti `mariadb-server`,
- omogoči in zažene MariaDB servis,
- spremeni `bind-address` na `0.0.0.0`,
- ustvari bazo `nakupni_seznam`,
- ustvari tabelo `nakup`,
- vstavi testna podatka,
- ustvari uporabnika za aplikacijo,
- nastavi pravice za dostop iz zasebnega omrežja `192.168.%`.

Podatkovna baza:

```text
DB: nakupni_seznam
Tabela: nakup(id, element, kolicina)
```

Struktura tabele:

```sql
CREATE TABLE nakup (
  id INT AUTO_INCREMENT PRIMARY KEY,
  element VARCHAR(100) NOT NULL,
  kolicina INT NOT NULL
);
```

Testni podatki:

```sql
INSERT INTO nakup (element, kolicina) VALUES
('kruh', 1),
('mleko', 2);
```

![MariaDB namestitev na db1](slike/app-db/01-db-install-db1.png)
![Ustvarjena baza in tabela](slike/app-db/02-db-created-table.png)
![Vstavljeni testni podatki](slike/app-db/03-test-data-insert.png)

---

## 7) Namestitev spletnega strežnika in PHP aplikacije

Web EC2 instanca je bila ustvarjena v javnem subnetu. Na njej so bili nameščeni:

- Apache2,
- PHP,
- `libapache2-mod-php`,
- `php-mysql`,
- MariaDB client.

Spletna aplikacija je bila prenesena na web EC2 instanco in skopirana v mapo:

```text
/var/www/html
```

Za prenos aplikacije sem uporabil skripto:

```text
scripts/03_deploy_app.sh
```

Skripta pri prenosu zamenja oznako `DB1_PRIVATE_IP` v `config.php` z dejanskim zasebnim IP naslovom DB1 instance. To pomeni, da se PHP aplikacija ne povezuje na javni IP baze, ampak na zasebni IP znotraj VPC.

Aplikacija omogoča:

- vnos novega elementa nakupnega seznama,
- shranjevanje podatkov v MariaDB,
- izpis vseh elementov iz tabele `nakup`.

![Spletni obrazec index](slike/app-db/04-web-index-form.png)
![Uspesen vnos prek obrazca](slike/app-db/05-web-insert-success.png)
![Izpis vseh elementov](slike/app-db/06-web-izpis.png)

---

## 8) Preverjanje DB2 instance

V infrastrukturi je bila ustvarjena tudi tretja EC2 instanca DB2 v tretjem subnetu. Namen DB2 je bil pokazati, da lahko infrastrukturo razširimo na več zasebnih podomrežij in več Availability Zone.

Za preverjanje DB2 sem uporabil skripto:

```text
scripts/04_verify_db2.sh
```

Skripta preveri, ali je na DB2 nameščen MariaDB strežnik in ali servis deluje.

---

## 9) Ustavitev instanc po delu

Po zaključku testiranja sem EC2 instance ustavil, da ne nastajajo nepotrebni stroški. Instance niso bile izbrisane, ampak samo ustavljene.

Za ustavitev sem uporabil skripto:

```text
scripts/05_stop_instances.sh
```

![Ustavljene instance](slike/shutdown/01-instances-stopped.png)

---

## 10) Varnostne opombe

Pri tej nalogi sem uporabil ločitev med javnim in zasebnim delom sistema. Web strežnik je javno dostopen, podatkovni strežnik pa ni neposredno dostopen iz interneta.

Pomembne varnostne nastavitve:

- SSH na web EC2 je dovoljen samo iz mojega IP naslova.
- HTTP na web EC2 je dovoljen iz interneta.
- MariaDB port 3306 je dovoljen samo iz web security group.
- DB instance nimajo javnega IP naslova.
- Podatkovna baza uporablja zasebni IP naslov.
- Zasebnega SSH ključa `.pem` ne smemo naložiti na GitHub.
- Gesla in zasebni ključi se v produkcijskem okolju ne smejo hraniti neposredno v kodi.

V tej nalogi so bila gesla uporabljena samo za testno šolsko okolje. V resnem okolju bi uporabil AWS Secrets Manager, okoljske spremenljivke ali drugo varno shranjevanje skrivnosti.

---

## 11) Odgovori na vprašanja

1. **Kako se imenuje naslov računalnika, s katerim ga identificiramo v omrežju?**  
   To je IP naslov.

2. **Kaj je data center?**  
   Data center je fizična lokacija z infrastrukturo, kot so strežniki, omrežje, napajanje, hlajenje in varnostni sistemi. V njem tečejo IT in oblačne storitve.

3. **Kaj pomeni CIDR zapis `192.168.0.16/28`?**  
   Pomeni subnet z masko `/28`. Ker ima IPv4 naslov 32 bitov, ostane za hoste `32 - 28 = 4` bite. To pomeni `2^4 = 16` naslovov skupaj. Del naslovov je rezerviran, zato je uporabnih manj naslovov.

4. **Kako naredimo podomrežje privatno?**  
   Podomrežje je privatno, če njegova route table nima poti `0.0.0.0/0` do Internet Gateway in instance nimajo javnega IP naslova. Za izhodni promet lahko uporabljajo NAT Gateway.

5. **Kako naredimo podomrežje javno?**  
   Podomrežje je javno, če je povezano z route table, ki ima pot `0.0.0.0/0` do Internet Gateway, in če lahko instance dobijo javni IP naslov.

6. **Kaj dosežemo, če imamo vire v različnih AZ?**  
   Dosežemo večjo razpoložljivost in odpornost na izpad ene Availability Zone.

7. **Kaj je `scp`? Čemu služi? Kaj lahko uporabimo namesto `scp`?**  
   `scp` je program za varen prenos datotek prek SSH. Uporabimo ga lahko za kopiranje datotek med lokalnim računalnikom in strežnikom ali med strežniki. Namesto `scp` lahko uporabimo SFTP, `rsync`, WinSCP ali MobaXterm.

8. **Čemu je namenjena route table?**  
   Route table določa, kam se usmerja promet iz subneta. Primeri ciljev so lokalno VPC omrežje, Internet Gateway ali NAT Gateway.

9. **Kaj moramo nastaviti, da so računalniki v podomrežjih vidni med seboj?**  
   Računalniki morajo biti v istem VPC ali povezani prek ustreznega omrežja. Potrebna so pravilna route table pravila in security group pravila, ki promet dovolijo.

10. **Zakaj uporabljamo ločena podomrežja za web in db?**  
    Zaradi varnosti in segmentacije. Web strežnik je javno dostopen, podatkovna baza pa ostane v zasebnem delu omrežja.

11. **Zakaj mora biti web v javnem subnetu, DB pa v privatnem?**  
    Web mora biti dosegljiv uporabnikom z interneta, DB pa naj bo dosegljiva samo iz notranjega omrežja oziroma iz web strežnika.

12. **Zakaj ne dovolimo neposrednega dostopa iz interneta do baze?**  
    S tem zmanjšamo napadno površino in tveganje nepooblaščenega dostopa, kraje ali brisanja podatkov.

13. **Zakaj uporabljamo security groups, če imamo že subnet?**  
    Subnet določa omrežni del infrastrukture, security group pa natančno določa, kateri porti, protokoli in izvori so dovoljeni do posamezne instance.

14. **Zakaj morata biti subnet2 in subnet3 v različnih AZ?**  
    Zaradi višje razpoložljivosti. Če ena AZ odpove, lahko druga še vedno deluje.

15. **Zakaj uporabljamo SSH ključ in ne gesla?**  
    SSH ključ je varnejši od gesla, ker je težje uganljiv in bolj odporen na brute-force napade. Omogoča tudi varnejšo avtomatizacijo dostopa.

16. **Kaj bi se zgodilo, če bi bila MariaDB v javnem subnetu z odprtim portom 3306?**  
    Baza bi bila javno izpostavljena internetu. To bi močno povečalo tveganje napadov, nepooblaščenega dostopa in izgube podatkov.

17. **Zakaj naj web dostopa do DB prek privatnega omrežja in ne javnega IP?**  
    Privatna povezava je varnejša, ni javno izpostavljena in ostane znotraj VPC omrežja.

18. **Kaj bi se zgodilo, če izbrišemo Internet Gateway iz VPC?**  
    Javne instance ne bi bile več dosegljive z interneta. Spletna stran in SSH dostop od zunaj bi prenehala delovati. Tudi NAT Gateway ne bi mogel pravilno posredovati prometa v internet.

---

## 12) Seznam oddanih datotek

```text
scripts/00_cleanup_old_resources.sh
scripts/01_setup_infra.sh
scripts/02_configure_db1.sh
scripts/03_deploy_app.sh
scripts/04_verify_db2.sh
scripts/05_stop_instances.sh
scripts/helper_db1_commands.sh
app/index.html
app/config.php
app/vstavi.php
app/izpis.php
app/style.css
db/init.sql
slike/*
```

---

## 13) Seznam zahtevanih screenshotov

```text
slike/cleanup/01-cleanup-script-run.png
slike/cleanup/02-no-old-resources.png
slike/infra/01-vpc.png
slike/infra/02-subnets.png
slike/infra/03-route-tables.png
slike/infra/04-igw-nat.png
slike/infra/05-security-groups.png
slike/infra/06-ec2-instances.png
slike/app-db/01-db-install-db1.png
slike/app-db/02-db-created-table.png
slike/app-db/03-test-data-insert.png
slike/app-db/04-web-index-form.png
slike/app-db/04-web-index-form2.png
slike/app-db/05-web-insert-success.png
slike/app-db/05-web-insert-success2.png
slike/app-db/06-web-izpis.png
slike/app-db/06-web-izpis2.png
slike/shutdown/01-instances-stopped.png
```

---

## 14) Pokritost zahtev iz Excela

| Zahteva iz Excela                                                           | Kje je pokrito v poročilu |
| --------------------------------------------------------------------------- | ------------------------- |
| CIDR - računanje                                                            | poglavje 2.1              |
| Datacenter + Availability Zone + Region                                     | poglavje 2.2              |
| PB: nameščanje, konfiguracija, uporabniki, povezovanje, PB, tabele, vrstice | poglavje 2.5 in 6         |
| Routing                                                                     | poglavje 2.3 in 5         |
| Internet Gateway                                                            | poglavje 2.3 in 5         |
| PB na EC2                                                                   | poglavje 6                |
| PHP program, ki dostopa do PB                                               | poglavje 3.2 in 7         |
| Tri podomrežja                                                              | poglavje 2.1 in 5         |
| EC2, subnets, AZ, spletna stran                                             | poglavje 5 in 7           |
| Vprašanja                                                                   | poglavje 11               |

---

## 15) Zaključek

Vaja 6–7 je bila uspešno izvedena. Ustvaril sem novo AWS infrastrukturo z VPC omrežjem, tremi podomrežji v različnih Availability Zone, Internet Gateway, NAT Gateway, route table pravili, security group pravili in tremi EC2 instancami.

Na zasebni EC2 instanci sem namestil in konfiguriral MariaDB, ustvaril podatkovno bazo, tabelo, testne podatke in uporabnika za aplikacijo. Na javni web EC2 instanci sem pripravil Apache, PHP in aplikacijo, ki omogoča vnos in izpis podatkov iz baze.

S tem sem praktično preveril razliko med javnim in zasebnim subnetom, pomen route table, Internet Gateway, NAT Gateway in security group pravil. Poleg tega sem preveril, zakaj je smiselno ločiti spletni strežnik in podatkovno bazo ter zakaj mora podatkovna baza ostati v zasebnem delu omrežja.
