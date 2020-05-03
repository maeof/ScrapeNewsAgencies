testpage = httpget("https://www.delfi.lt/archive/index.php?query=&tod=31.12.2019&fromd=01.01.2019&channel=0&category=0")
t = open("test\\A1.htm", "w+", encoding="utf-8")
t.writelines(testpage)
t.close()

testpage = httpget2(
    "https://www.delfi.lt/archive/index.php?query=&tod=31.12.2019&fromd=01.01.2019&channel=0&category=0")
t = open("test\\A2.htm", "w+", encoding="utf-8")
t.writelines(testpage)
t.close()

testpage = httpget("https://www.15min.lt/naujienos/aktualu/lietuva?offset=2019-07-05%2023:59:59")
t = open("test\\B1.htm", "w+", encoding="utf-8")
t.writelines(testpage)
t.close()

testpage = httpget2("https://www.15min.lt/naujienos/aktualu/lietuva?offset=2019-07-05%2023:59:59")
t = open("test\\B2.htm", "w+", encoding="utf-8")
t.writelines(testpage)
t.close()

testpage = httpget(
    "https://www.15min.lt/naujiena/aktualu/lietuva/10-dalios-grybauskaites-prezidentavimo-metu-trumpas-bandymas-perkrauti-santykius-su-baltarusija-56-1167730")
t = open("test\\C1.htm", "w+", encoding="utf-8")
t.writelines(testpage)
t.close()

testpage = httpget2(
    "https://www.15min.lt/naujiena/aktualu/lietuva/10-dalios-grybauskaites-prezidentavimo-metu-trumpas-bandymas-perkrauti-santykius-su-baltarusija-56-1167730")
t = open("test\\C2.htm", "w+", encoding="utf-8")
t.writelines(testpage)
t.close()