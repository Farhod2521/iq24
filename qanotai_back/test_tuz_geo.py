"""test_tuz_geo.py — "Geometriya" (planimetriya) mavzulariga AI bilan test va ikki xil daftar yechimi tuzadi.

Har mavzu uchun: 25 ta oson, 15 ta o'rta, 10 ta qiyin — jami 50 ta test, IDC kitobi uslubida: qisqa shart, ma'lumotning
bir qismi aniq chizmada (masshtabda, to'g'ri burchak va teng kesma belgilari bilan). Har bir testda ikkita daftar
yechimi bo'ladi:
  1) qisqa yechim — Berilgan / Topish kerak / Formula (ramkada) / hisob / Javob; hisoblar (√ va π bilan) kod bilan tekshiriladi;
  2) batafsil yechim — o'sha daftarda, chizma qayta chizilib, yordamchi chiziqlar va ishlatilgan uchburchak bo'yalib,
     formulalar maydalab tushuntirilgan.

Eng oson yo'l — loyiha papkasidagi test_tuz_geo.cmd ni ikki marta bosish: menyu ochiladi.
Yoki terminalda (loyiha papkasida):
    docker compose exec backend python test_tuz_geo.py                  # menyu
    docker compose exec backend python test_tuz_geo.py --topics 1-5     # 1–5-mavzularga test (yetishmaganini)
    docker compose exec backend python test_tuz_geo.py --fill           # boshlangan mavzularda kam test/yechimni to'ldirish
    docker compose exec backend python test_tuz_geo.py --status         # holat
"""

from app import ai_geometry
from tutor_cli import Config, cli

# Exercise families per topic, in the spirit of the book (same idea, different numbers).
TOPIC_GUIDE: dict[int, list[str]] = {
    1: ["qo'shni va vertikal burchaklar", "burchak bissektrisasi, burchaklar ayirmasi va nisbati", "nuqtadan to'g'ri chiziqqacha masofa",
        "kesmalar va ularning o'rtalari orasidagi masofa", "soat millari orasidagi burchak"],
    2: ["parallel to'g'ri chiziqlar va kesuvchi: ichki almashinuvchi, mos burchaklar", "bir tomonli ichki burchaklar yig'indisi",
        "parallel chiziqlar orasidagi siniq chiziq burchagi", "burchaklar nisbati berilgan masalalar", "parallellik alomatlari"],
    3: ["uchburchak burchaklari yig'indisi", "tashqi burchak xossasi", "teng yonli uchburchak burchaklari",
        "bissektrisa va balandlik orasidagi burchak", "burchaklar nisbati berilgan uchburchak"],
    4: ["uchburchak tengsizligi: tomon qaysi oraliqda", "uchinchi tomonning butun qiymatlari soni", "perimetri berilgan teng yonli uchburchak tomonlari",
        "katta tomon qarshisida katta burchak", "uchburchak mavjud bo'lish sharti"],
    5: ["Pifagor teoremasi", "katetning gipotenuzadagi proyeksiyasi, balandlik h² = a₁·b₁", "30° qarshisidagi katet",
        "to'g'ri burchakli uchburchakda sin, cos, tg", "gipotenuzaga tushirilgan mediana"],
    6: ["kosinuslar teoremasi bilan tomonni topish", "kosinuslar teoremasi bilan burchakni topish", "sinuslar teoremasi va tashqi chizilgan aylana radiusi",
        "ikki tomon va ular orasidagi burchak", "uchburchak turini aniqlash (o'tkir, o'tmas)"],
    7: ["S = ½·a·h", "S = ½·a·b·sinC", "Geron formulasi", "teng tomonli uchburchak yuzi a²√3/4", "to'g'ri burchakli uchburchak yuzi"],
    8: ["bissektrisa xossasi: tomonlarni proporsional bo'ladi", "bissektrisa uzunligi", "bissektrisalar kesishgan nuqta",
        "bissektrisa ajratgan uchburchaklar yuzlari nisbati", "tashqi burchak bissektrisasi"],
    9: ["medianalar kesishish nuqtasi 2:1 nisbatda bo'ladi", "mediana uzunligi formulasi", "mediana uchburchakni teng yuzli ikkiga bo'ladi",
        "medianalar hosil qilgan 6 ta uchburchak yuzlari", "to'g'ri burchakli uchburchakda mediana"],
    10: ["o'xshashlik koeffitsiyenti va tomonlar", "o'xshash uchburchaklar yuzlari nisbati k²", "asosga parallel kesma (DE ∥ BC)",
         "to'g'ri burchakli uchburchakda balandlik hosil qilgan o'xshash uchburchaklar", "o'xshash uchburchaklar perimetrlari nisbati"],
    11: ["asosga parallel kesmalar ajratgan bo'laklar yuzi", "ichki nuqtadan tomonlarga perpendikulyarlar (muntazam uchburchak, DE, DF, DG)",
         "umumiy balandlikli uchburchaklar yuzlari nisbati", "uchburchak ichidagi parallel kesmalar va yuzalar", "yuzalar nisbati orqali tomonni topish"],
    12: ["to'rtburchak burchaklari yig'indisi", "to'g'ri to'rtburchak diagonali va yuzi", "kvadrat diagonali va yuzi",
         "diagonallari perpendikulyar to'rtburchak yuzi d₁·d₂/2", "to'rtburchak tomonlari o'rtalari (Varinyon parallelogrammi)"],
    13: ["parallelogramm burchaklari va tomonlari", "parallelogramm yuzi a·h va a·b·sinα", "diagonallar xossasi d₁² + d₂² = 2(a² + b²)",
         "burchak bissektrisasi parallelogrammda teng yonli uchburchak ajratadi", "diagonallar hosil qilgan uchburchaklar yuzi"],
    14: ["romb diagonallari perpendikulyar va teng ikkiga bo'linadi", "romb yuzi d₁·d₂/2", "romb balandligi va burchagi",
         "romb perimetri diagonallar orqali", "rombga ichki chizilgan aylana radiusi"],
    15: ["trapetsiya o'rta chizig'i", "teng yonli trapetsiya burchaklari va balandligi", "to'g'ri burchakli trapetsiya",
         "trapetsiya diagonallari kesishish nuqtasi va o'xshash uchburchaklar", "diagonali perpendikulyar trapetsiya"],
    16: ["trapetsiya yuzi (a + b)/2 · h", "teng yonli trapetsiya yuzi tomonlar orqali", "diagonallari perpendikulyar trapetsiya yuzi",
         "diagonallar ajratgan to'rt uchburchak yuzlari", "o'rta chiziq va balandlik orqali yuza"],
    17: ["qavariq ko'pburchak ichki burchaklari yig'indisi", "muntazam ko'pburchak burchagi va tomonlari soni", "ko'pburchak diagonallari soni",
         "muntazam oltiburchak yuzi va diagonallari", "tashqi burchaklar yig'indisi"],
    18: ["aylana uzunligi va yoy uzunligi", "doira yuzi va sektor yuzi", "segment yuzi", "halqa yuzi", "radius o'zgarganda yuza necha marta o'zgaradi"],
    19: ["markaziy va ichki chizilgan burchak", "diametrga tiralgan burchak 90°", "bir yoyga tiralgan ichki burchaklar",
         "vatarlar orasidagi burchak", "urinma va vatar orasidagi burchak"],
    20: ["kesishuvchi vatarlar bo'laklari ko'paytmasi", "urinma va kesuvchi: AT² = AB·AC", "bir nuqtadan o'tkazilgan urinmalar tengligi",
         "markazdan vatargacha masofa", "ikki aylananing umumiy urinmasi"],
    21: ["ichki chizilgan aylana radiusi r = S/p", "to'g'ri burchakli uchburchakda r = (a + b − c)/2", "urinish nuqtalari ajratgan kesmalar",
         "teng tomonli uchburchakka ichki chizilgan aylana", "radius va perimetr orqali yuza"],
    22: ["tashqi chizilgan aylana radiusi R = abc/(4S)", "to'g'ri burchakli uchburchakda R gipotenuzaning yarmi", "R = a/(2·sinA)",
         "teng tomonli uchburchakka tashqi chizilgan aylana", "markaz uchburchak ichida yoki tashqarisida"],
    23: ["aylanaga ichki chizilgan to'rtburchak: qarama-qarshi burchaklar yig'indisi 180°", "aylanaga tashqi chizilgan to'rtburchak: a + c = b + d",
         "kvadrat va to'g'ri to'rtburchakka tashqi chizilgan aylana", "rombga ichki chizilgan aylana", "Ptolemey teoremasi sodda holi"],
    24: ["teng yonli trapetsiyaga tashqi chizilgan aylana", "trapetsiyaga ichki chizilgan aylana: asoslar yig'indisi yon tomonlar yig'indisiga teng",
         "ichki chizilgan aylanali trapetsiya balandligi 2r", "ichki chizilgan aylanali trapetsiya yuzi", "to'g'ri burchakli trapetsiya va aylana"],
    25: ["muntazam ko'pburchakka ichki va tashqi chizilgan aylanalar radiuslari", "muntazam oltiburchak va aylana", "kvadrat va aylana (ichki, tashqi)",
         "aylanaga ichki chizilgan ko'pburchak yuzi", "muntazam uchburchak, kvadrat va oltiburchak tomonlarining R orqali ifodasi"],
    26: ["ikki nuqta orasidagi masofa", "kesma o'rtasi koordinatalari", "uchburchak yuzi koordinatalar orqali",
         "nuqtaga simmetrik nuqta", "parallelogrammning to'rtinchi uchini topish"],
    27: ["vektor koordinatalari va uzunligi", "vektorlarni qo'shish va songa ko'paytirish", "kollinear vektorlar",
         "vektorlarni bazis bo'yicha yoyish", "uchburchakda mediana vektori"],
    28: ["skalyar ko'paytma koordinatalarda", "vektorlar orasidagi burchak", "perpendikulyarlik sharti",
         "skalyar ko'paytma |a|·|b|·cosα orqali", "vektor uzunligi ifodalardan (|a + b|)"],
    29: ["to'g'ri chiziq tenglamasi ikki nuqta orqali", "burchak koeffitsiyent, parallel va perpendikulyar to'g'ri chiziqlar",
         "aylana tenglamasi, markazi va radiusi", "to'g'ri chiziq va aylananing kesishishi", "nuqtadan to'g'ri chiziqqacha masofa"],
    30: ["bir necha mavzuni birlashtirgan masalalar: uchburchak va aylana", "to'rtburchak va o'xshashlik", "yuzalar va koordinatalar",
         "trigonometriya bilan geometrik masala", "eng katta / eng kichik qiymatga oid geometrik masala"],
}

CONFIG = Config(
    label="Geometriya",
    book_title="Geometriya",
    ai=ai_geometry.PLANE,
    guide=TOPIC_GUIDE,
    style_note="Kitob uslubida: qisqa shart, ma'lumot chizmada; sonlari har xil; har bir savol mustaqil va to'liq bo'lsin.",
)

if __name__ == "__main__":
    cli(CONFIG)
