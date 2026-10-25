"""test_tuz_stereometriya.py — "Stereometriya" mavzulariga AI bilan test va ikki xil daftar yechimi tuzadi.

Har mavzu uchun: 25 ta oson, 15 ta o'rta, 10 ta qiyin — jami 50 ta test, IDC kitobi uslubida: jism chizmasi bilan
(ko'rinmas qirralar avtomatik shtrixli, kesimlar bo'yalgan, kub, prizma, piramida, silindr, konus, shar).
Har bir testda ikkita daftar yechimi bo'ladi:
  1) qisqa yechim — Berilgan / Topish kerak / Formula (ramkada) / hisob / Javob; hisoblar (√ va π bilan) kod bilan tekshiriladi;
  2) batafsil yechim — o'sha daftarda, jism qayta chizilib, kerakli kesim/balandlik ajratilib, ichidagi tekis
     uchburchak alohida chizilgan va formulalar maydalab tushuntirilgan.

Eng oson yo'l — loyiha papkasidagi test_tuz_stereometriya.cmd ni ikki marta bosish: menyu ochiladi.
Yoki terminalda (loyiha papkasida):
    docker compose exec backend python test_tuz_stereometriya.py                  # menyu
    docker compose exec backend python test_tuz_stereometriya.py --topics 1-5     # 1–5-mavzularga test
    docker compose exec backend python test_tuz_stereometriya.py --fill           # kam test/yechimni to'ldirish
    docker compose exec backend python test_tuz_stereometriya.py --status         # holat
"""

from app import ai_geometry
from tutor_cli import Config, cli

# Exercise families per topic, in the spirit of the book (same idea, different numbers).
TOPIC_GUIDE: dict[int, list[str]] = {
    1: ["fazoda to'g'ri chiziqlarning o'zaro joylashuvi (kesishuvchi, parallel, ayqash)", "to'g'ri chiziq va tekislik orasidagi burchak",
        "uch perpendikulyar haqidagi teorema", "nuqtadan tekislikkacha masofa, og'ma va uning proyeksiyasi", "ikki yoqli burchak"],
    2: ["kub qirrasi, yon sirti, to'la sirti va hajmi", "kub diagonali a√3 va yoq diagonali a√2", "kubdan kichik kub qirqilgan yoki ustiga qo'yilgan jism hajmi va sirti",
        "kub qirralari o'rtalari orqali kesim", "qirra o'zgarganda hajm va sirt necha marta o'zgaradi"],
    3: ["to'g'ri burchakli parallelepiped diagonali d² = a² + b² + c²", "to'la sirt va hajm", "yoqlar yuzlari berilganda hajm",
        "diagonal va asos tekisligi orasidagi burchak", "diagonal kesim yuzi"],
    4: ["asosi parallelogramm bo'lgan to'g'ri parallelepiped hajmi", "asos burchagi va tomonlari orqali diagonallar", "yon sirt va to'la sirt",
        "diagonal kesim yuzi", "kichik diagonal va asos orasidagi burchak"],
    5: ["muntazam uchburchakli prizma hajmi va sirti", "muntazam to'rtburchakli va oltiburchakli prizma", "prizma hajmi asos yuzi va balandlik orqali",
        "yon yoq diagonali va burchagi", "og'ma prizma hajmi (perpendikulyar kesim)"],
    6: ["muntazam piramida apofemasi va balandligi", "piramida yon sirti ½·P·apofema", "yon qirra va asos orasidagi burchak",
        "yon yoq va asos orasidagi ikki yoqli burchak", "piramida balandligi asosiga tushadigan nuqta (tashqi chizilgan aylana markazi)"],
    7: ["piramida hajmi ⅓·S·h", "muntazam to'rtburchakli va uchburchakli piramida hajmi", "kesik piramida hajmi va sirti",
        "asosga parallel kesim va hajmlar nisbati k³", "tetraedr hajmi"],
    8: ["silindr yon sirti 2πrh va to'la sirti", "silindr hajmi πr²h", "o'q kesimi yuzi va diagonali",
        "o'qqa parallel kesim", "yoyilmasi kvadrat bo'lgan silindr"],
    9: ["konus yasovchisi, radius va balandlik (l² = r² + h²)", "konus yon sirti πrl va to'la sirti", "konus hajmi ⅓πr²h",
        "o'q kesimi va uchidagi burchak", "konus yoyilmasi — sektor burchagi"],
    10: ["shar hajmi ⁴⁄₃πR³ va sirti 4πR²", "sharning tekislik bilan kesimi, kesim radiusi", "shar segmenti va qatlami (sodda hollar)",
         "radius o'zgarganda hajm va sirt nisbati", "bir necha sharni eritib yangi shar quyish"],
    11: ["kubga ichki chizilgan shar (R = a/2) va tashqi chizilgan shar (R = a√3/2)", "to'g'ri burchakli parallelepipedga tashqi chizilgan shar",
         "prizmaga ichki va tashqi chizilgan silindr", "muntazam prizmaga tashqi chizilgan shar", "jismlar hajmlari nisbati"],
    12: ["silindrga ichki va tashqi chizilgan shar", "konusga ichki chizilgan shar radiusi", "konusga tashqi chizilgan shar radiusi",
         "silindr va konus kombinatsiyasi", "hajmlar va sirtlar nisbati"],
    13: ["muntazam piramidaga ichki chizilgan shar radiusi", "muntazam piramidaga tashqi chizilgan shar radiusi", "tetraedrga ichki va tashqi shar",
         "piramida va konus kombinatsiyasi", "radiuslar nisbati"],
    14: ["sirti berilganda eng katta hajmli jism", "ma'lum o'lchamdagi jismga sig'adigan eng katta jism",
         "kesim yuzining eng katta qiymati", "eng qisqa yo'l jism sirti bo'ylab (yoyilma orqali)", "hosilasiz baholanadigan ekstremal masalalar"],
}

CONFIG = Config(
    label="Stereometriya",
    book_title="Stereometriya",
    ai=ai_geometry.SOLID,
    guide=TOPIC_GUIDE,
    style_note="Kitob uslubida: qisqa shart, jism chizmasi bilan; sonlari har xil; har bir savol mustaqil va to'liq bo'lsin.",
)

if __name__ == "__main__":
    cli(CONFIG)
