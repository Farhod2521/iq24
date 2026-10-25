"""test_tuz_fizika.py — "Fizika 1-qism" mavzulariga AI bilan test va ikki xil daftar yechimi tuzadi.

Har mavzu uchun: 25 ta oson, 15 ta o'rta, 10 ta qiyin — jami 50 ta test. Rasm (chizma, grafik) soni oldindan
belgilanmaydi: AI masalaga rasm kerak bo'lsa o'zi qo'shadi (richag, qiya tekislik, blok, idish, v(t) grafik …).
Har bir testda ikkita daftar yechimi bo'ladi:
  1) qisqa daftar yechimi — Berilgan / SI / Topish kerak / Formula / Yechish / Javob (hisoblar kod bilan tekshiriladi);
  2) batafsil daftar yechimi — o'sha daftarda, lekin rasmlar chizilib, formulalar maydalab tushuntirilgan:
     umuman tushunmaydigan o'quvchi ham o'qib tushunishi uchun.

Eng oson yo'l — loyiha papkasidagi test_tuz_fizika.cmd ni ikki marta bosish: menyu ochiladi.
Yoki terminalda (loyiha papkasida):
    docker compose exec backend python test_tuz_fizika.py                       # menyu
    docker compose exec backend python test_tuz_fizika.py --topics 1-5          # 1–5-mavzularga test (yetishmaganini)
    docker compose exec backend python test_tuz_fizika.py --topics 1-5 --reset  # shu mavzular testlarini o'chirib, boshidan
    docker compose exec backend python test_tuz_fizika.py --solutions 3,4       # qisqa daftar yechimini qayta yozish
    docker compose exec backend python test_tuz_fizika.py --explainers 3,4      # batafsil (rasmli) yechimni to'ldirish
    docker compose exec backend python test_tuz_fizika.py --status              # holat
    docker compose exec backend python test_tuz_fizika.py --fill                # boshlangan mavzularda kam test/yechimni to'ldirish

Script to'xtab qolsa, qayta ishga tushiring: yaratilgan testlar saqlanib qoladi, faqat yetishmagani tuziladi.
"""

from app import ai_physics
from tutor_cli import Config, cli

# Exercise families per topic, in the spirit of the IDC physics book. Each AI batch is pointed at a couple of these
# in turn, so a topic's tests cover the whole topic instead of one kind.
TOPIC_GUIDE: dict[int, list[str]] = {
    1: ["yo'l va ko'chishni farqlash (aylana bo'ylab, ortga qaytib harakat)", "trayektoriya bo'yicha ko'chishni topish (katakchali chizma, sharq-shimol yo'nalishlar)",
        "tekis harakatda tezlik, yo'l, vaqt", "birliklarni o'tkazish (km/soat ↔ m/s)", "moddiy nuqta va sanoq jismi tushunchasi"],
    2: ["yo'lning qismlarida har xil tezlik — o'rtacha tezlik", "vaqtning qismlarida har xil tezlik", "borib-kelishdagi o'rtacha tezlik",
        "o'rtacha tezlik berilganda noma'lum qism tezligini topish", "o'rtacha yo'l tezligi va o'rtacha ko'chish tezligi"],
    3: ["harakatlanayotgan transportdagi odamning yerga nisbatan tezligi", "ikki jismning bir-biriga nisbatan tezligi (bir yo'nalishda, qarama-qarshi)",
        "sanoq sistemasini tanlash, tinchlik va harakat nisbiyligi", "uchrashish va quvib yetish vaqti", "poyezd yonidan o'tish vaqti (uzunlik hisobga olinadi)"],
    4: ["daryoda oqim bo'yicha va oqimga qarshi suzish", "perpendikulyar tezliklarni qo'shish (qayiq daryoni kesib o'tadi, Pifagor)",
        "shamol va samolyot/velosipedchi tezligi", "harakatlanayotgan platformadagi odam", "eskalator masalalari"],
    5: ["x = x₀ + vt tenglamasidan tezlik va boshlang'ich koordinatani topish", "ikki jism tenglamasidan uchrashish joyi va vaqti",
        "x(t) grafigidan tezlikni topish", "koordinata va yo'lni farqlash", "tekis harakat grafiklarini taqqoslash"],
    6: ["tezlanish ta'rifi a = (v − v₀)/t", "tezlik tenglamasi v = v₀ + at", "v(t) grafigidan tezlanishni topish",
        "tormozlanish, to'xtash vaqti", "tezlanish yo'nalishi va ishorasi"],
    7: ["s = v₀t + at²/2 formulasi", "s = (v² − v₀²)/(2a) formulasi", "tormozlanish yo'li", "n-sekunddagi yo'l, birinchi va keyingi sekundlar nisbati",
        "v(t) grafigi ostidagi yuza — yo'l"],
    8: ["erkin tushish vaqti va balandligi h = gt²/2", "yerga urilish tezligi v = √(2gh)", "oxirgi sekunddagi yo'l",
        "ikki jismning tushishi (bir xil balandlik, har xil vaqt)", "boshlang'ich tezlik bilan pastga otilgan jism"],
    9: ["eng katta ko'tarilish balandligi H = v₀²/(2g)", "ko'tarilish va qaytib tushish vaqti", "berilgan balandlikdagi tezlik",
        "otilgandan t sekunddan keyingi tezlik va balandlik", "ikki jismni ketma-ket otish"],
    10: ["davr va chastota (T = t/N, ν = 1/T)", "chiziqli tezlik v = 2πR/T", "burchak tezlik ω = 2π/T, v = ωR",
         "markazga intilma tezlanish a = v²/R", "soat millari, g'ildirak, Yer aylanishi masalalari"],
    11: ["tasma (remen) uzatma — chiziqli tezliklar teng", "tishli g'ildiraklar — aylanishlar soni nisbati",
         "bir o'qdagi g'ildiraklar — burchak tezliklar teng", "tezlanuvchan aylanma harakat", "velosiped yulduzchalari masalasi"],
    12: ["gorizontal otilgan jismning uchish vaqti t = √(2h/g)", "uchish uzoqligi L = v₀t", "yerga urilish tezligi va burchagi",
         "trayektoriyaning ma'lum nuqtasidagi tezlik", "balandlik va uzoqlik nisbati"],
    13: ["qiya otilgan jismning uchish vaqti", "eng katta balandlik", "uchish uzoqligi, 45° da eng katta", "eng yuqori nuqtadagi tezlik",
         "ikki burchakda bir xil uzoqlik (α va 90° − α)"],
    14: ["zichlik formulasi ρ = m/V", "aralashma va qotishma zichligi", "ichi kovak jism", "birliklar (g/sm³ ↔ kg/m³, l ↔ m³)",
         "bir xil massali yoki hajmli jismlarni taqqoslash"],
    15: ["Nyutonning ikkinchi qonuni F = ma", "teng ta'sir etuvchi kuch (bir to'g'ri chiziqda, perpendikulyar)", "uchinchi qonun: ta'sir va aks ta'sir",
         "inersiya hodisalari", "ikki jism ip bilan bog'langan sistemasi"],
    16: ["Guk qonuni F = kx", "prujinalarni ketma-ket va parallel ulash", "cho'zilish grafigidan bikrlikni topish",
         "prujinali dinamometr", "prujinaga osilgan yuk muvozanati"],
    17: ["butun olam tortishish qonuni F = Gm₁m₂/r²", "masofa o'zgarganda kuch necha marta o'zgaradi", "erkin tushish tezlanishining balandlikka bog'liqligi",
         "boshqa sayyoralarda g", "birinchi kosmik tezlik"],
    18: ["og'irlik kuchi va vazn farqi", "liftdagi vazn (tezlanish yuqoriga/pastga)", "vaznsizlik holati",
         "qavariq va botiq ko'prikdagi vazn", "egrilik radiusi berilgan yo'ldagi avtomobil"],
    19: ["sirpanish ishqalanish kuchi F = μN", "jismni tekis tortish uchun kuch", "ishqalanish ta'sirida to'xtash yo'li",
         "tinchlikdagi ishqalanish kuchi", "burilishda ishqalanish va eng katta tezlik"],
    20: ["qiya tekislikdagi kuchlar (mg sinα, mg cosα)", "qiya tekislikda tinch turish sharti", "qiya tekislik bo'ylab sirpanish tezlanishi",
         "qiya tekislik bo'ylab yuqoriga tortish kuchi", "ishqalanish koeffitsiyentini burchakdan topish"],
    21: ["Arximed kuchi F = ρgV", "suyuqlikdagi jismning og'irligi (dinamometr ko'rsatishi)", "jism zichligini suyuqlikda o'lchash",
         "har xil suyuqlikdagi Arximed kuchi", "to'liq va qisman botgan jism"],
    22: ["suzish sharti, botgan qism ulushi", "sol va kema yuk ko'tarishi", "havo shari ko'tarish kuchi",
         "muz bo'lagi va suv sathi", "ikki suyuqlik chegarasidagi jism"],
    23: ["gorizontal sirtda tortish kuchi va ishqalanish", "blok orqali bog'langan ikki jism", "ip tarangligi",
         "vertikal tezlanish bilan ko'tarish", "burchak ostida tortilgan jism"],
    24: ["jism impulsi p = mv", "kuch impulsi FΔt = Δp", "devorga urilib qaytgan jism impulsining o'zgarishi",
         "p(t) yoki F(t) grafigi", "impuls va kinetik energiya bog'lanishi"],
    25: ["noelastik to'qnashuv — umumiy tezlik", "o'q otganda qurolning orqaga tepishi", "qayiqdan sakrash",
         "bo'laklarga ajralish", "elastik to'qnashuv sodda holi"],
    26: ["mexanik ish A = Fs cosα", "og'irlik kuchining ishi", "ishqalanish kuchining ishi", "F(s) grafigi ostidagi yuza — ish",
         "musbat, manfiy va nol ish"],
    27: ["kinetik energiya Eₖ = mv²/2", "tezlik o'zgarganda energiya necha marta o'zgaradi", "kinetik energiya haqidagi teorema",
         "tormozlanish ishi", "impuls orqali kinetik energiya"],
    28: ["yer ustidagi jism potensial energiyasi Eₚ = mgh", "prujina potensial energiyasi kx²/2", "sanoq sathini tanlash",
         "balandlik o'zgarganda energiya o'zgarishi", "arg'imchoq, toqqa chiqish masalalari"],
    29: ["mexanik energiyaning saqlanishi", "tushayotgan jism tezligi energiya orqali", "prujinali to'pponcha",
         "mayatnik eng pastki nuqtadagi tezligi", "qiya sirtdan sirpanib tushish (ishqalanishsiz)"],
    30: ["havo qarshiligi ishi energiyalar farqidan", "ishqalanish tufayli yo'qotilgan energiya", "o'qning taxtani teshib o'tishi",
         "qarshilik kuchini to'xtash yo'lidan topish", "energiya yo'qotish foizi"],
    31: ["quvvat N = A/t", "N = Fv formulasi", "foydali ish koeffitsiyenti", "nasos, kran, lift quvvati", "avtomobil tezligi va quvvati"],
    32: ["richag muvozanati F₁l₁ = F₂l₂", "kuch momenti", "bir necha kuch ta'siridagi richag", "tarozi masalalari (noma'lum massa)",
         "richag qaysi tomonga aylanadi"],
    33: ["qo'zg'almas blok", "qo'zg'aluvchan blok — kuchdan yutish", "bloklar sistemasi (polispast)", "blokdan yutuq va yo'ldan yutqazish",
         "blok orqali yuk ko'tarish ishi"],
    34: ["ikki jism massa markazi", "sterjen va unga osilgan yuklar massa markazi", "massa markazi koordinatasini topish",
         "turg'unlik va muvozanat turlari", "bir jinsli shakllarning massa markazi"],
    35: ["bosim p = F/S", "suyuqlik bosimi p = ρgh", "atmosfera bosimi, barometr", "har xil chuqurlikdagi bosim farqi", "gidravlik press"],
    36: ["tutash idishlarda bir jinsli suyuqlik sathi", "tutash idishlarda har xil suyuqliklar balandligi nisbati", "U-simon nay",
         "suv minorasi, choynak", "gidravlik press va tutash idishlar"],
    37: ["uzluksizlik tenglamasi S₁v₁ = S₂v₂", "Bernulli tenglamasi", "nay torayganda tezlik va bosim", "teshikdan oqib chiqish tezligi √(2gh)",
         "samolyot qanotidagi ko'tarish kuchi sifat jihatdan"],
    38: ["modda miqdori ν = m/M = N/Nₐ", "molekulalar soni", "molyar massa", "molekula massasi", "diffuziya va Broun harakati"],
    39: ["MKN asosiy tenglamasi p = nkT", "p = (1/3)m₀nv²", "o'rtacha kinetik energiya E = (3/2)kT", "o'rtacha kvadratik tezlik",
         "harorat o'zgarganda tezlik necha marta o'zgaradi"],
    40: ["Mendeleyev–Klapeyron tenglamasi pV = νRT", "Klapeyron tenglamasi p₁V₁/T₁ = p₂V₂/T₂", "gaz zichligi va bosim",
         "ballondagi gaz massasi", "gaz chiqib ketganda bosim"],
    41: ["izotermik jarayon (Boyl–Mariott)", "izobarik jarayon (Gey-Lyussak)", "izoxorik jarayon (Sharl)", "p–V, V–T, p–T grafiklari",
         "jarayonni grafikdan aniqlash"],
    42: ["bir atomli gaz ichki energiyasi U = (3/2)νRT", "ichki energiya o'zgarishi", "ichki energiyani o'zgartirish usullari",
         "ichki energiya va harorat", "ikki gaz aralashmasi"],
    43: ["izobarik jarayonda gaz ishi A = pΔV", "p–V grafigi ostidagi yuza", "aylanma jarayon ishi", "gaz ustida bajarilgan ish",
         "A = νRΔT"],
    44: ["Q = ΔU + A", "izobarik jarayonda issiqlik miqdori", "izoxorik va izotermik jarayonlarda birinchi qonun", "adiabatik jarayon",
         "issiqlik berilganda ish va ichki energiya ulushi"],
    45: ["issiqlik mashinasi FIK η = (Q₁ − Q₂)/Q₁", "Karno sikli FIK η = (T₁ − T₂)/T₁", "isitkich va sovitkich harorati",
         "foydali ish va sovitkichga berilgan issiqlik", "sovitkich mashinalari"],
    46: ["sirt taranglik kuchi F = σl", "kapillyar nayda ko'tarilish h = 2σ/(ρgr)", "sirt energiyasi E = σS", "sovun pardasi (ikki sirt)",
         "ho'llash va ho'llamaslik"],
    47: ["issiqlik miqdori Q = cmΔt", "yoqilg'i yonish issiqligi Q = qm", "issiqlik balansi tenglamasi", "issiqlik sig'imi C = cm",
         "isitgich FIK"],
    48: ["erish issiqligi Q = λm", "bug'lanish issiqligi Q = rm (Lm)", "muzni isitib, eritib, qaynatish", "erish va qaynash grafiklari",
         "aralashmaning oxirgi harorati"],
    49: ["nisbiy namlik φ = p/pₜ·100%", "absolyut namlik va to'yingan bug' zichligi", "shudring nuqtasi", "psixrometr",
         "harorat o'zgarganda namlik"],
    50: ["tebranish davri va chastotasi", "matematik mayatnik T = 2π√(l/g)", "prujinali mayatnik T = 2π√(m/k)",
         "mayatnik uzunligi yoki massa o'zgarganda davr", "tebranish amplitudasi va bosib o'tilgan yo'l"],
    51: ["garmonik tebranish tenglamasi x = A cos(ωt + φ)", "tenglamadan amplituda, davr, chastotani topish", "eng katta tezlik va tezlanish",
         "x(t) grafigi", "tebranishdagi energiya almashinuvi"],
    52: ["to'lqin uzunligi λ = vT = v/ν", "tovush tezligi, aks-sado", "ko'ndalang va bo'ylama to'lqinlar", "to'lqin tenglamasi",
         "chastota va to'lqin uzunligi o'zgarishi"],
}


CONFIG = Config(
    label="Fizika",
    book_title="Fizika 1-qism",
    ai=ai_physics.PHYSICS,
    guide=TOPIC_GUIDE,
    style_note="Kitob uslubida: hayotiy vaziyat, sonlari har xil; har bir savol mustaqil va to'liq bo'lsin.",
)

if __name__ == "__main__":
    cli(CONFIG)
