"""test_tuz_kimyo.py — "Kimyo 1-qism" mavzulariga AI bilan test va ikki xil daftar yechimi tuzadi.

Har mavzu uchun: 25 ta oson, 15 ta o'rta, 10 ta qiyin — jami 50 ta test, Ma'ruf Tongotarovning "Kimyo 2027 testlar
to'plami" uslubida: qisqa shart, so'raladigan birlik qavsda, "qaysi(lari)" va "moslang" turidagi savollar ham bor.
Rasm (jadval, grafik, idishlar sxemasi) faqat kerak bo'lganda qo'shiladi. Har bir testda ikkita daftar yechimi bo'ladi:
  1) qisqa yechim — Berilgan / Topish kerak / Formula yoki reaksiya tenglamasi (ramkada) / hisob / Javob;
     hisoblar kod bilan tekshiriladi;
  2) batafsil yechim — o'sha daftarda, ma'lumotlar jadvalga solinib (modda | M | n | m, "boshida | reaksiyada |
     oxirida"), eritmalar idish sxemasida chizilib, formulalar maydalab tushuntirilgan.

Eng oson yo'l — loyiha papkasidagi test_tuz_kimyo.cmd ni ikki marta bosish: menyu ochiladi.
Yoki terminalda (loyiha papkasida):
    docker compose exec backend python test_tuz_kimyo.py                       # menyu
    docker compose exec backend python test_tuz_kimyo.py --topics 1-5          # 1–5-mavzularga test (yetishmaganini)
    docker compose exec backend python test_tuz_kimyo.py --topics 1-5 --reset  # shu mavzular testlarini o'chirib, boshidan
    docker compose exec backend python test_tuz_kimyo.py --solutions 3,4       # qisqa daftar yechimini qayta yozish
    docker compose exec backend python test_tuz_kimyo.py --explainers 3,4      # batafsil yechimni to'ldirish
    docker compose exec backend python test_tuz_kimyo.py --fill                # boshlangan mavzularda kam test/yechimni to'ldirish
    docker compose exec backend python test_tuz_kimyo.py --status              # holat

Mavzu raqamlari kitobdagi tartib bo'yicha ketma-ket: 1.1 → 1, 1.2 → 2, …, 10.7 → 41 (--status da ko'rinadi).
Script to'xtab qolsa, qayta ishga tushiring: yaratilgan testlar saqlanib qoladi, faqat yetishmagani tuziladi.
"""

from app import ai_chemistry
from tutor_cli import Config, cli

# Exercise families per topic, in the spirit of the book (same idea, different numbers). Each AI batch is pointed at
# a couple of these in turn, so a topic's tests cover the whole topic instead of one kind.
TOPIC_GUIDE: dict[int, list[str]] = {
    # 1. Kimyoning asosiy tushuncha va qonunlari
    1: ["sof modda va aralashma (qaysi biri sof modda: distillangan suv, ozon, havo, sintez gaz …)", "gomogen va geterogen aralashmalar",
        "aralashmalarni ajratish usullari: haydash, filtrlash, dekantatsiya, ajratuvchi voronka, bug'latish, xromatografiya",
        "moddaning fizik va kimyoviy xossalari", "agregat holatlar, atom va molekula tushunchalari"],
    2: ["valentlik bo'yicha formula tuzish (X₃N₂ hosil qilsa, xlor bilan qanday birikma)", "o'zgarmas va o'zgaruvchan valentli elementlar",
        "birikmalarning nomlanishi (mis (II) oksid, sulfat angidrid) va noto'g'ri nomni topish",
        "formuladagi atomlar soni va nisbati (kristallogidrat formulalarida ham)", "valentlik bo'yicha mavjud bo'lmagan birikmani topish"],
    3: ["kimyoviy element va oddiy modda farqi (\"kislorod\" so'zi qaysi ma'noda ishlatilgan)", "metallar va metallmaslar",
        "element belgilari va tarixiy nomlari (Sb — stibium, surma)", "elementlarning tabiatda va inson organizmida tarqalishi",
        "oddiy va murakkab moddalar"],
    4: ["allotropik shakl o'zgarishlar: O₂ / O₃; olmos, grafit, karbin, fulleren; oq, qizil, qora fosfor; rombik va monoklinik oltingugurt",
        "allotropiya sababi: tarkib yoki kristall tuzilish farqi", "O₂ va O₃ aralashmasi bo'yicha massa, mol va hajm hisoblari",
        "ozonlashda hajm kamayishi (3O₂ → 2O₃)", "allotroplarning xossalarini taqqoslash"],
    5: ["kimyoviy va fizik jarayonlarni ajratish (kundalik hayotdan misollar)", "kimyoviy reaksiya belgilari: gaz, cho'kma, rang, issiqlik, hid",
        "reaksiya turlari: birikish, parchalanish, o'rin olish, almashinish", "ekzotermik va endotermik reaksiyalar",
        "\"qaysi(lari)\" turidagi aralash jarayonlar ro'yxati"],
    # 2. Modda miqdori
    6: ["nisbiy molekulyar massa Mr ni hisoblash", "absolyut massa m₀ = M / NA (atom va molekula uchun)",
        "absolyut massadan elementni yoki modda formulasini topish", "formula xato yozilganda molyar massa qanchaga farq qiladi",
        "u (a.m.b.) va g/mol birliklari"],
    7: ["n = m / M va N = n · NA", "moddadagi ma'lum atomlar soni (1 g CaBr₂ dagi brom atomlari)", "gazlar uchun n = V / 22,4 (n.sh.)",
        "teng massa yoki teng hajm masalalari (8 g metan hajmicha is gazi; 4 mol argon massasicha geliy)",
        "noma'lum element X ni topish (0,2 mol CrX₃ 21,8 g; 0,2 mol X₂O₃ va 0,1 mol XO₂ aralashmasi)"],
    # 3. Modda tarkibi
    8: ["ω(E) = n · Ar / Mr · 100%", "massa ulushidan noma'lum elementni topish", "aralashmadagi elementning massa ulushi",
        "kristallogidratdagi suvning massa ulushi", "massa ulushi va mol ulushini taqqoslash"],
    9: ["birikmada elementlarning massa nisbati m(E₁) : m(E₂)", "massa nisbatidan formulani topish", "berilgan massadagi moddadagi element massasi",
        "ikki birikmada bir xil massa elementga to'g'ri keladigan massalar", "massa nisbati va atomlar soni nisbati"],
    10: ["massa ulushlaridan eng oddiy formula", "yonish mahsulotlari (CO₂, H₂O) massasidan formula", "nisbiy zichlik bilan haqiqiy formula",
         "atomlar soni nisbatidan formula", "binar birikma formulasini massa va mol ulushlaridan topish"],
    11: ["element ekvivalenti E = A / valentlik", "kislota, asos, tuz, oksidning ekvivalent massasi", "ekvivalentlar qonuni m₁ / E₁ = m₂ / E₂",
         "metall ekvivalentini ajralgan vodorod hajmidan topish", "ekvivalent hajm (H₂ — 11,2 l, O₂ — 5,6 l)"],
    12: ["karrali nisbatlar qonuni: azot oksidlarida kislorod massalari nisbati", "bir xil massa elementga to'g'ri keladigan ikkinchi element massalari",
         "qonun yordamida ikkinchi birikma formulasini topish", "tarkib doimiyligi qonuni", "temir yoki mis oksidlarida karrali nisbat"],
    13: ["kristallogidratning molyar massasi va suv ulushi (CuSO₄·5H₂O)", "kristallogidratdan suvsiz tuz massasi",
         "qizdirilganda massa kamayishidan suv molekulalari sonini topish", "kristallogidratdagi atomlar soni va nisbati",
         "kristallogidratni suvda eritib eritma tayyorlash (sodda)"],
    # 4. Massaning saqlanish qonuni
    14: ["reaksiya tenglamasi bo'yicha massa, mol va hajm hisoblari", "ekvimolyar yoki boshqa nisbatda olingan moddalar: ortib qolgan modda",
         "koeffitsiyentlarni tenglash va ularning yig'indisi", "aralashma tarkibini reaksiya mahsulotidan topish",
         "massaning saqlanish qonuni bilan noma'lum massani topish"],
    15: ["η = m(amaliy) / m(nazariy) · 100%", "unum berilganda mahsulot massasi yoki hajmi", "unum berilganda kerakli boshlang'ich modda",
         "ko'p bosqichli jarayonda umumiy unum", "qo'shimchali xomashyodan mahsulot olish"],
    # 5. Gaz qonunlari
    16: ["Mendeleyev–Klapeyron tenglamasi PV = nRT", "nisbiy zichlik D = M₁ / M₂ (havoga, vodorodga nisbatan)",
         "gaz aralashmasining o'rtacha molyar massasi; hajmiy ulush = mol ulush",
         "Avogadro qonuni: idishni turli gazlar bilan tortish masalasi", "Boyl–Mariott va Gey-Lyussak qonunlari"],
    # 6. Atom tarkibi, molekula tarkibi va yadro reaksiyalari
    17: ["atom va ionlardagi proton, neytron, elektron soni (³⁵Cl⁺, ¹⁸F⁻)", "izotoplar va o'rtacha nisbiy atom massasi",
         "izotop, izobar, izotonlar", "ion zaryadi va elektronlar sonidan elementni topish", "moddadagi jami elektron yoki proton miqdori (mol)"],
    18: ["molekula va murakkab ionlardagi elektronlar soni (NO₂, Al(OH)₂⁺)", "izotoplardan necha xil molekula hosil bo'ladi (H, D, T va ¹⁶O, ¹⁸O)",
         "molekuladagi zarrachalar nisbati", "eritmadagi jami elektronlar miqdori (mol)", "izotop tarkibli molekulalarning massasi"],
    19: ["α, β⁻, β⁺ yemirilish: massa soni va zaryad balansi", "yadro reaksiyasida noma'lum zarracha yoki yadroni topish",
         "α va β zarrachalar sonini topish (²³⁸U → ²⁰⁶Pb)", "yarim yemirilish davri: qolgan massa yoki o'tgan vaqt", "yadro sintezi va bo'linishi"],
    # 7. Elektron konfiguratsiya, kvant sonlar va davriy sistema
    20: ["atom va ionlarning elektron formulasi", "elektron \"sakrashi\" (Cr, Cu, Mo, Ag)", "s-, p-, d-elektronlar soni",
         "toq elektronlar soni; asosiy va qo'zg'algan holat", "pog'onachalarning to'lish tartibi (Klechkovskiy qoidasi)"],
    21: ["n, l, ml, ms kvant sonlarining qiymatlari", "oxirgi elektronning kvant sonlaridan elementni topish",
         "pog'onachadagi orbitallar va maksimal elektronlar soni", "n + l qoidasi", "Pauli prinsipi va Xund qoidasi"],
    22: ["davr va guruhda xossalarning o'zgarishi: radius, elektromanfiylik, metallik", "elementning o'rnidan elektron formulasi va aksincha",
         "yuqori oksid va uchuvchan vodorodli birikma formulasi", "oksid yoki vodorodli birikmadagi massa ulushidan elementni topish",
         "s-, p-, d-, f-elementlar"],
    # 8. Kimyoviy bog'lanish, gibridlanish, kristall panjara, valentlik va oksidlanish daraja
    23: ["ion, kovalent qutbli va qutbsiz, metall, vodorod bog'lanish", "molekuladagi σ- va π-bog'lar soni",
         "donor-akseptor bog'lanish (NH₄⁺, H₃O⁺)", "elektromanfiylik farqi va bog' qutbliligi", "bog' energiyasi va uzunligi"],
    24: ["sp, sp², sp³ gibridlanish turini aniqlash", "molekula shakli va valent burchak (CH₄, NH₃, H₂O, BF₃, CO₂)",
         "gibrid orbitallar soni", "organik molekulalarda uglerod atomlarining gibridlanishi", "molekula shakli va qutbliligi"],
    25: ["ionli, atomli, molekulyar, metall kristall panjaralar", "panjara turi va xossalar: suyuqlanish harorati, qattiqlik, elektr o'tkazuvchanlik",
         "moddalarni panjara turi bo'yicha guruhlash", "amorf va kristall moddalar", "misollar: olmos, NaCl, muz, yod, kvars"],
    26: ["birikma va ionlarda oksidlanish darajasini hisoblash", "valentlik va oksidlanish darajasi farq qiladigan moddalar (H₂O₂, N₂, CO)",
         "elementning eng yuqori va eng past oksidlanish darajasi", "oksidlanish darajalari yig'indisi",
         "organik birikmalarda uglerodning oksidlanish darajasi"],
    # 9. Eritmalar
    27: ["ω = m(modda) / m(eritma) · 100%", "eritmani suv qo'shib suyultirish yoki bug'latish", "ikki eritmani aralashtirish",
         "eritmaga qo'shimcha modda qo'shish", "kristallogidratdan eritma tayyorlash"],
    28: ["molyar konsentratsiya C = n / V", "normal (ekvivalent) konsentratsiya", "ω dan molyar konsentratsiyaga o'tish (zichlik bilan)",
         "eritmani suyultirish C₁V₁ = C₂V₂", "neytrallash uchun kerakli eritma hajmi"],
    29: ["konsentratsiya turlari orasida o'tish: ω, molyar, normal, molyal, mol ulush", "zichlik orqali bir konsentratsiyadan boshqasiga",
         "aralashtirilgan eritmalarning yangi konsentratsiyasi (diagonal sxema)", "eritmaning mol ulushidan massa ulushini topish",
         "kristallogidrat eritmasining konsentratsiyalari"],
    30: ["eruvchanlik koeffitsiyenti (100 g suvda eriydigan modda)", "to'yingan eritma: ω = S / (100 + S) · 100%",
         "sovutilganda cho'kkan tuz massasi", "eruvchanlik egri chizig'idan (grafikdan) hisob", "kristallogidrat holida cho'kish"],
    31: ["oleum tarkibi: SO₃ ning H₂SO₄ dagi eritmasi", "oleumga suv qo'shib sulfat kislota olish", "oleum va sulfat kislota eritmasini aralashtirish",
         "oleumdagi SO₃ ning massa ulushi", "oleumni ma'lum foizli kislotaga aylantirish uchun kerakli suv"],
    32: ["metall plastinkani tuz eritmasiga tushirish: plastinka massasining o'zgarishi (Fe + CuSO₄)", "massa o'zgarishidan ajralgan metall massasini topish",
         "eritmadagi tuz konsentratsiyasining o'zgarishi", "metallarning faollik qatori: reaksiya boradimi", "ikki tuz aralashmasi bilan plastinka"],
    33: ["eritmalar reaksiyasida cho'kma yoki gaz massasi", "reaksiyadan keyingi eritmada moddaning massa ulushi (cho'kma va gaz chiqib ketadi)",
         "ortiqcha olingan modda va eritma tarkibi", "neytrallash reaksiyasi", "reaksiyaga kirishgan eritmaning konsentratsiyasini topish"],
    34: ["eritma zichligi ρ = m / V", "zichlik orqali hajmdan massaga o'tish", "zichlik va massa ulushidan molyar konsentratsiya",
         "gaz zichligi ρ = M / 22,4 (n.sh.)", "nisbiy zichlik va zichlik"],
    # 10. Elektrolitlar
    35: ["kuchli va kuchsiz elektrolitlar", "dissotsilanish tenglamasi va hosil bo'ladigan ionlar soni", "dissotsilanish darajasi α",
         "eritmadagi ionlar miqdori (mol) va soni", "bosqichli dissotsilanish"],
    36: ["qaytmas reaksiya shartlari: cho'kma, gaz, suv hosil bo'lishi", "kimyoviy muvozanat va Le Shatelye prinsipi",
         "muvozanat konstantasi K", "muvozanat va boshlang'ich konsentratsiyalar", "harorat va bosim muvozanatga ta'siri"],
    37: ["to'liq va qisqa ionli tenglamalar", "qisqa ionli tenglamaga mos reaksiyani topish", "eritmada birga bo'la olmaydigan ionlar",
         "ionli tenglamadagi koeffitsiyentlar yig'indisi", "cho'kma hosil qiladigan juftliklar (eruvchanlik jadvali)"],
    38: ["ionlarni aniqlash reaktivlari (Cl⁻ — AgNO₃, SO₄²⁻ — BaCl₂, CO₃²⁻ — kislota, Fe³⁺ — KSCN, NH₄⁺ — ishqor)",
         "indikatorlar rangi: lakmus, fenolftalein, metilzarg'aldog'i turli muhitda", "moddalarni tanib olish ketma-ketligi",
         "cho'kmalarning rangi", "bitta reaktiv bilan bir nechta moddani farqlash"],
    39: ["tuz turlari va eritma muhiti (kuchli asos + kuchsiz kislota …)", "gidroliz tenglamasi (qisqa ionli)",
         "to'liq gidroliz (Al₂S₃, Cr₂S₃)", "tuz eritmasida indikator rangi", "gidrolizga uchramaydigan tuzlar"],
    40: ["pH = −lg[H⁺], pOH, pH + pOH = 14 (toza o'nning darajalari bilan)", "kuchli kislota yoki ishqor eritmasining pH i",
         "suyultirilganda pH ning o'zgarishi", "kislota va ishqor aralashmasining pH i", "[H⁺] va [OH⁻] berilganda muhitni aniqlash"],
    41: ["Ostvald suyultirish qonuni K = α² · C", "kuchsiz kislota uchun [H⁺] = √(K · C)", "dissotsilanish darajasi α ni topish",
         "kuchsiz kislota eritmasining pH i", "suyultirilganda α ning o'zgarishi"],
}

CONFIG = Config(
    label="Kimyo",
    book_title="Kimyo 1-qism",
    ai=ai_chemistry.CHEMISTRY,
    guide=TOPIC_GUIDE,
    style_note="Kitob uslubida (Ma'ruf Tongotarov, Kimyo 2027): qisqa shart, so'raladigan birlik qavsda; sonlari har xil; "
    "savol turlarini aralashtiring (oddiy, \"qaysi(lari)\", \"moslang\", EMAS); har bir savol mustaqil va to'liq bo'lsin.",
)

if __name__ == "__main__":
    cli(CONFIG)
