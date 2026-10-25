"""test_tuz.py — "Matematika 1-, 2-, 3-qism" kitoblari mavzulariga AI bilan test va daftar uslubidagi yechim tuzadi.

Har mavzu uchun: 40 ta oson, 40 ta o'rta, 10 ta qiyin va 20 ta rasmli (chizmali) — jami 110 ta test.
Har bir testning bosqichma-bosqich yechimi bo'ladi: formula faqat masala formulaga tayansa yoziladi, oddiy
hisob-kitobda esa hisobning o'zi (ustun ko'paytirish va h.k.) ko'rsatiladi. Yechimdagi barcha hisoblar kod bilan
qayta tekshiriladi; javob esa AI tomonidan ikkinchi marta, javobsiz yechib tekshiriladi.

Eng oson yo'l — loyiha papkasidagi test_tuz.cmd ni ikki marta bosish: menyu ochiladi.
Yoki terminalda (loyiha papkasida):
    docker compose exec backend python test_tuz.py                     # menyu
    docker compose exec backend python test_tuz.py --topics 5-10       # 5–10-mavzularga test tuzish (yetishmaganini)
    docker compose exec backend python test_tuz.py --topics 5-10 --reset   # shu mavzular testlarini o'chirib, boshidan
    docker compose exec backend python test_tuz.py --solutions 4,6,7   # shu mavzular testlariga yechimni qayta yozish
    docker compose exec backend python test_tuz.py --solutions 4,6,7 --missing-only   # faqat yechimi yo'qlariga
    docker compose exec backend python test_tuz.py --status            # qaysi mavzuda nechta test va yechim bor
    docker compose exec backend python test_tuz.py --book 2 --topics 1-3   # Matematika 2-qism (3 = 3-qism; standart: 1-qism)

AI ulanishi .env dagi AI_URL / AI_KEY / AI_MODEL / AI_FORMAT dan olinadi. Script to'xtab qolsa, qayta ishga
tushiring: yaratilgan testlar saqlanib qoladi, faqat yetishmagani tuziladi.
"""

import argparse
import asyncio
import re
import secrets
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, func, select

from app import ai
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.mathtext import normalize, normalize_solution
from app.models import Book, Question, TestAttempt, Topic

# what each topic needs: (key, difficulty sent to the AI, figure?, how many, batch size)
PLAN = [
    ("easy", "easy", False, 40, 8),
    ("medium", "medium", False, 40, 8),
    ("hard", "hard", False, 10, 5),
    ("figure", "mixed", True, 20, 4),
]
MAX_ROUNDS = 4  # extra attempts per bucket when the AI returns fewer usable tests than asked
MAX_FAILS = 2  # consecutive failed AI calls after which a bucket is skipped (each failure costs tokens)
EXPLAIN_BATCH = 6  # questions per "write the solutions" request

# Exercise families per topic number, in the spirit of the book (same idea, different numbers). Each AI batch is
# pointed at a couple of these in turn, so a topic's tests cover the whole topic instead of one kind.
TOPIC_GUIDE: dict[int, list[str]] = {
    1: [
        "ko'p xonali sonlarni qo'shish va ayirish (ustun usuli)",
        "ko'paytirish va bo'lish, qulay usulda hisoblash (125·8, 25·4, taqsimot qonuni)",
        "amallar tartibi va qavsli ifodalar qiymatini topish",
        "xona birliklari, raqam va son farqi, eng katta/eng kichik n xonali sonlar",
        "ketma-ket sonlar yig'indisi (1+2+…+n, juft/toq sonlar yig'indisi)",
        "berilgan shartdagi sonlar sonini sanash (ikki xonali, raqamlari yig'indisi …)",
        "noma'lum komponentni topish (x + a = b, a·x = b, qoldiqsiz bo'lish)",
        "matnli masalalar: narx, miqdor, harakat, ish",
        "faktorial va ko'paytmaning oxirgi nollari",
    ],
    2: [
        "2, 3, 4, 5, 8, 9, 10, 11, 25 ga bo'linish belgilari",
        "noma'lum raqamni topish (4a52 son 9 ga bo'linadi …)",
        "tub va murakkab sonlarni ajratish, berilgan oraliqdagi tub sonlar soni",
        "egizak tub sonlar, tub sonlar yig'indisi/ko'paytmasi",
        "bir nechta songa bir vaqtda bo'linish (6, 12, 15, 18, 36, 45, 72)",
        "1 dan n gacha k ga bo'linadigan/bo'linmaydigan sonlar soni",
        "raqamlardan tuzilgan sonlarning bo'linishi",
    ],
    3: [
        "sonni tub ko'paytuvchilarga ajratish (kanonik yoyilma)",
        "ikki va uch sonning EKUBi",
        "ikki va uch sonning EKUKi",
        "EKUB · EKUK = a · b xossasi bilan masalalar",
        "matnli masalalar: bir vaqtda jo'nash, eng katta teng guruhlar, plitkalar",
        "EKUB va EKUK berilganda sonlarni topish",
        "o'zaro tub sonlar",
    ],
    4: [
        "sonning natural bo'luvchilari soni (36, 100, 144, 360 …)",
        "natural bo'luvchilar yig'indisi",
        "ikki-uch sonning umumiy natural bo'luvchilari soni",
        "ko'paytma yoki faktoriallar nisbatining bo'luvchilari soni (12·30, 8!/6!)",
        "2³·3ᵐ ning bo'luvchilari soni berilgan, m ni topish",
        "n! ko'paytma p ning qanday eng katta darajasiga bo'linadi (Lejandr formulasi)",
        "ko'paytma nechta nol bilan tugaydi (1·2·…·n, 21·22·…·50)",
        "1 dan n gacha bir nechta songa bo'linadiganlar soni (inklyuziya-ekskluziya)",
        "ko'paytmasi berilgan natural sonlar juftliklari soni, bo'luvchilari soni toq bo'lgan sonlar",
    ],
    5: [
        "qoldiqli bo'lish: bo'linuvchi, bo'luvchi, to'liqsiz bo'linma, qoldiq orasidagi bog'lanish",
        "bir songa bo'linganda qoldiq berilgan, boshqa songa bo'lgandagi qoldiq",
        "yig'indi, ayirma, ko'paytma qoldig'i",
        "daraja qoldig'i (2¹⁰⁰ ni 7 ga bo'lgandagi qoldiq)",
        "darajaning oxirgi raqami (7²⁰²⁵, 3ⁿ+2ⁿ)",
        "ko'paytma yoki yig'indining oxirgi raqami",
        "qoldiq shartiga mos eng kichik/eng katta sonni topish",
    ],
    6: [
        "ko'p qavatli kasrli ifodaning qiymati (suratida va maxrajida kasrlar, o'nli kasr bilan aralash)",
        "aralash sonli qavsli ifodalar: (aralash sonlar yig'indisi) : (aralash sonlar yig'indisi)",
        "kasrning surati/maxraji foizga yoki songa o'zgarganda hosil bo'lgan kasr",
        "kasrli yig'indilar qatori: maxraji qo'shni sonlar ko'paytmasi (teleskopik), suratida kvadratlar",
        "kasrlarni taqqoslash, qisqartirish, umumiy maxrajga keltirish",
        "sonning kasr qismini va kasr qismiga ko'ra sonni topish",
        "matnli masalalar: ishning qismi, hovuz, qismlar",
    ],
    7: [
        "o'nli kasrlar ustida to'rt amal",
        "oddiy kasrni o'nli kasrga va aksincha aylantirish",
        "davriy o'nli kasrni oddiy kasrga aylantirish (0,(6), 1,2(3))",
        "o'nli kasrlarni yaxlitlash va taqqoslash",
        "butun va kasr qism: [x] va {x}",
        "o'nli kasrli murakkab ifodalar qiymati",
        "verguldan keyingi raqamlar soni, n-raqamni topish",
    ],
    8: [
        "ratsional sonlar: musbat va manfiy sonlar ustida amallar",
        "son moduli, qarama-qarshi sonlar",
        "son o'qida ratsional sonlar va ularni taqqoslash",
        "manfiy sonli ifodalar qiymati (−2·(−9+1)−4·(6−10))",
        "ishora qoidasi bilan ko'paytma va bo'linmaning ishorasi",
        "ratsional sonlar orasidagi sonlar soni",
    ],
    9: [
        "nisbat va uni soddalashtirish, proporsiyaning noma'lum hadi",
        "to'g'ri va teskari proporsional miqdorlar (ishchilar-kunlar, sigirlar-ozuqa)",
        "sonni berilgan nisbatda bo'lish",
        "sonning foizini va foiziga ko'ra sonni topish",
        "ketma-ket foizli o'zgarish (15% keyin 20% oshdi)",
        "foyda, chegirma, narx o'zgarishi masalalari",
        "masshtab va xarita masalalari, aralashma va qotishma konsentratsiyasi",
    ],
    10: [
        "to'g'ri to'rtburchak va kvadrat perimetri va yuzi",
        "uchburchak turlari, burchaklari yig'indisi, perimetri",
        "aylana uzunligi va doira yuzi",
        "kub va to'g'ri burchakli parallelepiped: qirralar yig'indisi, sirt yuzi, hajm",
        "katakchali qog'ozdagi shakl yuzi",
        "murakkab shakl perimetri va yuzi (shakllardan tuzilgan)",
        "vaqt, masofa, uzunlik o'lchov birliklarini almashtirish geometriyada",
    ],
    11: [
        "natural ko'rsatkichli daraja qiymati, darajalarni ko'paytirish va bo'lish",
        "darajani darajaga ko'tarish, ko'paytma va bo'linmaning darajasi",
        "nol va manfiy ko'rsatkichli daraja",
        "darajali ifodalarni soddalashtirish (2⁵·4³/8⁴)",
        "darajalarni taqqoslash (2³⁰⁰ va 3²⁰⁰)",
    ],
    12: [
        "murakkab darajali ifodalarni soddalashtirish",
        "umumiy ko'paytuvchini qavsdan chiqarib hisoblash (3²⁰+3²¹)/3¹⁹",
        "daraja ko'rsatkichidagi noma'lumni topish (2ˣ = 32·4)",
        "sonning standart shakli",
        "darajali ifodaning oxirgi raqami va bo'linishi",
    ],
    13: [
        "uzunlik, massa, yuza, hajm, vaqt o'lchov birliklarini almashtirish",
        "birhadni standart shaklga keltirish, birhad koeffitsiyenti va darajasi",
        "o'xshash hadlarni ixchamlash",
        "birhadlarni ko'paytirish va darajaga ko'tarish",
        "algebraik ifodaning qiymatini hisoblash",
        "matnni algebraik ifoda bilan yozish",
    ],
    14: [
        "ko'phadlarni qo'shish va ayirish, standart shakl",
        "birhadni ko'phadga va ko'phadni ko'phadga ko'paytirish",
        "ko'phadning darajasi va koeffitsiyentlari, koeffitsiyentlar yig'indisi (x = 1)",
        "ko'phadni birhadga bo'lish",
        "ko'phad qiymatini hisoblash, ayniyatdan noma'lum koeffitsiyent",
    ],
    15: [
        "(a ± b)² formulasi bilan ochish",
        "a² − b² formulasi va (a−b)(a+b) ko'paytma",
        "yig'indining kvadratini ajratish, to'la kvadrat",
        "qulay hisoblash (99², 101·99, 48·52)",
        "a + b va ab berilganda a² + b² ni topish",
        "x + 1/x berilganda x² + 1/x² ni topish",
    ],
    16: [
        "yig'indi va ayirmaning kubi (a ± b)³ ni ochish",
        "kublar yig'indisi va ayirmasi a³ ± b³",
        "* o'rniga kerakli ifodani yozish",
        "ko'phadni yig'indi yoki ayirma kubiga keltirish",
        "x + y va xy berilganda x³ + y³, x⁴ + y⁴ ni topish",
        "x + k/x berilganda x² + k²/x², x³ + k³/x³ ni topish",
        "(x−1)(x+1)(x²+1)… kabi zanjir ko'paytmalar",
    ],
    17: [
        "umumiy ko'paytuvchini qavsdan chiqarish",
        "guruhlash usuli bilan ko'paytuvchilarga ajratish",
        "qisqa ko'paytirish formulalari yordamida ajratish",
        "ko'paytuvchilarga ajratib ifoda qiymatini hisoblash",
    ],
    18: [
        "kvadrat uchhadni ko'paytuvchilarga ajratish",
        "to'la kvadrat ajratish usuli",
        "murakkab ifodalarni bir necha usulni birlashtirib ajratish",
        "ko'paytuvchilarga ajratib tenglama yechish (x³ − 4x = 0)",
        "bo'linish masalalari: n³ − n ning 6 ga bo'linishi",
    ],
    19: [
        "algebraik kasrni qisqartirish",
        "kasrning aniqlanish sohasi (maxraj nolga teng bo'lmasligi)",
        "algebraik kasrlarni umumiy maxrajga keltirish",
        "algebraik kasrlarni qo'shish va ayirish",
    ],
    20: [
        "algebraik kasrlarni ko'paytirish va bo'lish",
        "murakkab (ko'p qavatli) algebraik kasrlarni soddalashtirish",
        "ifodani soddalashtirib qiymatini hisoblash",
        "kasr ifodaning butun qiymatlari",
    ],
    21: [
        "ax + b = c ko'rinishdagi chiziqli tenglamalar",
        "qavsli va kasrli chiziqli tenglamalar",
        "modulli eng sodda tenglamalar |x − a| = b",
        "parametrli tenglama: yechimi yo'q / cheksiz ko'p bo'lishi",
        "tenglamaning ildizi berilgan, parametrni topish",
    ],
    22: [
        "o'rniga qo'yish usuli bilan sistema yechish",
        "qo'shish usuli bilan sistema yechish",
        "sistema yechimidan ifoda qiymatini topish (x + y, xy)",
        "parametrli sistemaning yechimlar soni",
        "uch noma'lumli sodda sistemalar",
    ],
    23: [
        "sonlarga oid masalalar (ikki son yig'indisi va ayirmasi)",
        "yosh masalalari",
        "harakat masalalari (qarama-qarshi, quvib yetish, oqim)",
        "ish va unumdorlik masalalari",
        "narx va miqdor, tangalar, aralashmalar masalalari",
        "ikki xonali son raqamlariga oid masalalar",
    ],
    24: [
        "chiziqli tengsizlikni yechish va yechimlar oralig'i",
        "tengsizlikning eng kichik/eng katta butun yechimi, butun yechimlar soni",
        "tengsizliklar sistemasi",
        "qo'sh tengsizliklar a < bx + c < d",
        "modulli eng sodda tengsizliklar",
        "parametrli tengsizliklar",
    ],
    25: [
        "y = kx + b grafigi, k va b ma'nosi",
        "grafikning o'qlar bilan kesishish nuqtalari",
        "ikki to'g'ri chiziqning kesishish nuqtasi, parallellik sharti",
        "nuqtalardan o'tuvchi to'g'ri chiziq tenglamasi",
        "funksiyaning o'sishi va kamayishi, nuqta grafikka tegishliligi",
        "grafik va o'qlar bilan chegaralangan uchburchak yuzi",
    ],
    26: [
        "arifmetik kvadrat ildiz qiymati, aniq kvadratlar",
        "ildizlarni ko'paytirish va bo'lish xossalari",
        "ko'paytuvchini ildiz ostidan chiqarish va kiritish",
        "ildizlarni taqqoslash, ildiz qaysi butun sonlar orasida",
        "√(a²) = |a| xossasi",
    ],
    27: [
        "o'xshash ildizli ifodalarni ixchamlash",
        "maxrajdagi irratsionallikdan qutulish",
        "qisqa ko'paytirish formulalari bilan ildizli ifodalar",
        "ichma-ich ildizlar √(a ± 2√b)",
        "ildizli ifodaning qiymatini hisoblash",
    ],
    28: [
        "to'liq kvadrat tenglamani diskriminant orqali yechish",
        "to'liqsiz kvadrat tenglamalar",
        "ildizlar soni va diskriminant ishorasi, parametrli shartlar",
        "kvadrat tenglamaga keltiriladigan tenglamalar (bikvadrat, almashtirish)",
        "matnli masalalar kvadrat tenglama orqali",
    ],
    29: [
        "Viyet teoremasi: ildizlar yig'indisi va ko'paytmasi",
        "ildizlarga bog'liq ifodalar: x₁² + x₂², 1/x₁ + 1/x₂, x₁³ + x₂³",
        "ildizlari berilgan tenglamani tuzish",
        "ildizlar orasidagi bog'lanishdan parametrni topish",
        "teskari Viyet teoremasi bilan og'zaki yechish",
    ],
}

# Same idea for "Matematika 2-qism" (algebra for school-leavers).
TOPIC_GUIDE_2: dict[int, list[str]] = {
    1: [
        "kasr-ratsional tenglamani yechish, aniqlanish sohasini hisobga olish (chet ildizlarni tashlash)",
        "umumiy maxrajga keltirib kvadrat tenglamaga keltiriladigan ratsional tenglamalar",
        "almashtirish usuli bilan yechiladigan ratsional tenglamalar (t = x + 1/x va h.k.)",
        "ildizlar yig'indisi, ko'paytmasi yoki soni so'raladigan tenglamalar",
        "ratsional tenglama bilan yechiladigan matnli masalalar (tezlik, ish unumi)",
    ],
    2: [
        "ikkinchi darajali tenglamalar sistemasini o'rniga qo'yish usuli bilan yechish",
        "simmetrik sistemalar (x + y va xy orqali)",
        "bir jinsli sistemalar va ko'paytuvchilarga ajratish orqali yechish",
        "sistema yechimlari soni, x·y yoki x + y qiymati so'raladigan masalalar",
        "sistemaga keltiriladigan matnli masalalar",
    ],
    3: [
        "ko'phadni ko'phadga bo'lish, bo'linma va qoldiq",
        "Bezu teoremasi: qoldiqni topish, noma'lum koeffitsiyentni topish",
        "ko'phadning butun va ratsional ildizlari, Gorner sxemasi",
        "ko'phadni ko'paytuvchilarga ajratish, yuqori darajali tenglamalar",
        "ko'phad koeffitsiyentlari yig'indisi, P(1), P(−1) qiymatlari",
    ],
    4: [
        "chiziqli va kvadrat tengsizliklarni yechish, butun yechimlar soni",
        "intervallar usuli bilan ko'paytma ko'rinishidagi tengsizliklar",
        "tengsizliklar sistemasi, eng katta/eng kichik butun yechim",
        "aniqlanish sohasini topish (ildiz ostidagi ifoda, maxraj)",
        "kvadrat uchhadning ishorasi, har doim musbat bo'lish sharti",
    ],
    5: [
        "kasr-ratsional tengsizliklar intervallar usulida",
        "karrali ildizli tengsizliklar ((x−a)², (x−a)³ ko'paytuvchilar)",
        "tengsizlik yechimlari ichidagi butun sonlar yig'indisi yoki soni",
        "ratsional tengsizliklar sistemasi",
        "almashtirish orqali yechiladigan ratsional tengsizliklar",
    ],
    6: [
        "parabola uchi, simmetriya o'qi, eng katta/eng kichik qiymat",
        "grafik bo'yicha a, b, c ishoralari va qiymatlarini aniqlash",
        "kvadrat funksiyaning o'sish va kamayish oraliqlari, qiymatlar to'plami",
        "parabolaning o'qlar va to'g'ri chiziq bilan kesishish nuqtalari",
        "kesmada funksiyaning eng katta va eng kichik qiymati, optimallash masalalari",
    ],
    7: [
        "parametrning qanday qiymatida tenglama ildizga ega emas / bitta / ikkita ildizga ega",
        "kvadrat tenglama ildizlarining joylashuvi (ikkalasi musbat, biri 1 dan katta va h.k.)",
        "parametrli chiziqli tenglama va tengsizliklar",
        "tengsizlik barcha x lar uchun bajariladigan parametr qiymatlari",
        "parametrli sistemaning yechimlari soni",
    ],
    8: [
        "modul ta'rifi va xossalari, modulli ifoda qiymati",
        "|f(x)| = a va |f(x)| = g(x) ko'rinishidagi tenglamalar",
        "bir nechta modulli tenglamalar oraliqlar usulida",
        "modul ostidan chiqarish orqali ifodani soddalashtirish",
        "modulli tenglama ildizlari yig'indisi yoki soni, parametrli modulli tenglamalar",
    ],
    9: [
        "|f(x)| < a va |f(x)| > a ko'rinishidagi tengsizliklar",
        "|f(x)| < g(x), |f(x)| > |g(x)| tengsizliklar",
        "bir nechta modulli tengsizliklar oraliqlar usulida",
        "modulli tengsizlikning butun yechimlari soni yoki yig'indisi",
        "modulli tengsizliklar sistemasi",
    ],
    10: [
        "ratsional ko'rsatkichli darajani hisoblash (a^(m/n))",
        "daraja xossalari bilan ifodalarni soddalashtirish",
        "ildizni daraja ko'rinishida yozish va aksincha",
        "darajali ifodalarni taqqoslash",
        "ratsional ko'rsatkichli darajali ifodaning qiymati (o'zgaruvchi berilganda)",
    ],
    11: [
        "√f(x) = g(x) ko'rinishidagi tenglamalar, chet ildizlarni tekshirish",
        "ikki ildizli tenglamalar (kvadratga ko'tarish ikki marta)",
        "almashtirish usuli bilan irratsional tenglamalar",
        "aniqlanish sohasi orqali yechiladigan irratsional tenglamalar",
        "irratsional tenglama ildizlari soni yoki yig'indisi",
    ],
    12: [
        "√f(x) < g(x) ko'rinishidagi tengsizliklar",
        "√f(x) > g(x) ko'rinishidagi tengsizliklar",
        "√f(x) ≥ √g(x) tengsizliklar va aniqlanish sohasi",
        "irratsional tengsizlikning butun yechimlari",
        "ko'paytma va bo'linma ko'rinishidagi irratsional tengsizliklar",
    ],
    13: [
        "arifmetik progressiyaning n-hadi formulasi",
        "ayirma va birinchi hadni ikki had orqali topish",
        "arifmetik progressiya xossasi (o'rta had), uchta son progressiya tashkil qilishi",
        "progressiyada berilgan son nechanchi had ekanini topish",
        "musbat/manfiy hadlar soni, matnli masalalar",
    ],
    14: [
        "dastlabki n ta had yig'indisi formulasi",
        "yig'indi berilganda hadlar sonini yoki ayirmani topish",
        "ma'lum shartdagi sonlar yig'indisi (100 dan kichik 3 ga karrali sonlar va h.k.)",
        "S_n formulasidan n-hadni topish (a_n = S_n − S_{n−1})",
        "eng katta yig'indi, matnli masalalar",
    ],
    15: [
        "geometrik progressiyaning n-hadi va maxraji",
        "dastlabki n ta had yig'indisi",
        "cheksiz kamayuvchi geometrik progressiya yig'indisi, davriy kasrni oddiy kasrga aylantirish",
        "geometrik progressiya xossasi (o'rta proporsional)",
        "arifmetik va geometrik progressiya aralash masalalari",
    ],
    16: [
        "harakatga doir masalalar (qarama-qarshi, bir tomonga, oqim bo'yicha)",
        "ishga doir masalalar (birgalikda bajarish, quvurlar)",
        "foizga doir masalalar (narx o'zgarishi, bank foizi)",
        "aralashma va qotishma masalalari",
        "sonlarga doir masalalar (raqamlar, ikki xonali son)",
    ],
    17: [
        "tenglamalar sistemasi bilan yechiladigan harakat masalalari",
        "unumdorlik va vaqt masalalari kvadrat tenglama orqali",
        "ketma-ket foiz o'zgarishlari, murakkab foiz",
        "konsentratsiya o'zgarishi, bir necha marta aralashtirish",
        "yosh, narx va miqdorga doir murakkab matnli masalalar",
    ],
    18: [
        "funksiyaning aniqlanish sohasini topish",
        "funksiya qiymatini hisoblash, f(f(x)), f(a) = b dan a ni topish",
        "funksiyaning qiymatlar to'plami",
        "juft va toq funksiyalar",
        "grafik bo'yicha funksiya xossalarini o'qish",
    ],
    19: [
        "funksiyaning monotonligi, o'sish va kamayish oraliqlari",
        "teskari funksiyani topish",
        "murakkab funksiya f(g(x))",
        "davriy funksiyalar va davr",
        "funksiya grafigini almashtirish (siljitish, cho'zish, simmetriya)",
    ],
    20: [
        "funksiyaning nollari va ishora saqlash oraliqlari",
        "funksiyaning eng katta va eng kichik qiymati",
        "f(x) ning funksional tenglamadan topilishi (f(x) + 2f(1−x) = …)",
        "grafiklar kesishish nuqtalari soni",
        "kasr-chiziqli funksiya va giperbola",
    ],
    21: [
        "a^f(x) = a^g(x) ko'rinishidagi tenglamalar (bir asosga keltirish)",
        "almashtirish usuli bilan yechiladigan tenglamalar (t = a^x)",
        "umumiy ko'paytuvchini qavsdan chiqarish (2^(x+1) + 2^x = …)",
        "bir jinsli ko'rsatkichli tenglamalar (4^x, 6^x, 9^x)",
        "ko'rsatkichli tenglamalar sistemasi, ildizlar yig'indisi",
    ],
    22: [
        "a^f(x) > a^g(x) tengsizliklar, asos 1 dan katta va kichik holatlar",
        "almashtirish bilan yechiladigan ko'rsatkichli tengsizliklar",
        "ko'rsatkichli tengsizlikning butun yechimlari soni",
        "ko'rsatkichli tengsizliklar sistemasi",
        "aniqlanish sohasi bilan birga keladigan ko'rsatkichli tengsizliklar",
    ],
    23: [
        "logarifm ta'rifi bo'yicha hisoblash",
        "logarifm xossalari: ko'paytma, bo'linma, daraja logarifmi",
        "yangi asosga o'tish formulasi",
        "asosiy logarifmik ayniyat a^(log_a b) = b",
        "log_a b berilganda boshqa logarifmni ifodalash",
    ],
    24: [
        "logarifmik ifodalarni soddalashtirish",
        "logarifmlarni taqqoslash, qiymat qaysi butun sonlar orasida",
        "logarifmlar qatnashgan murakkab ifodalar qiymati",
        "logarifmik ifodaning aniqlanish sohasi",
        "o'zgaruvchilar orasidagi logarifmik bog'lanishdan ifoda qiymati",
    ],
}

# Same idea for "Matematika 3-qism" (logarithms, trigonometry, calculus, combinatorics).
TOPIC_GUIDE_3: dict[int, list[str]] = {
    1: [
        "logarifmik funksiyaning aniqlanish sohasi",
        "logarifmik funksiyaning monotonligi, logarifmlarni taqqoslash",
        "logarifmik funksiya grafigi va uning xossalari",
        "logarifmik funksiyaning qiymatlar to'plami, eng katta/eng kichik qiymat",
        "ko'rsatkichli va logarifmik funksiyalar o'zaro teskari ekani",
    ],
    2: [
        "log_a f(x) = b ko'rinishidagi sodda tenglamalar",
        "log_a f(x) = log_a g(x), aniqlanish sohasini tekshirish",
        "logarifm xossalari bilan soddalashtiriladigan tenglamalar",
        "almashtirish usuli (t = log_a x) bilan kvadrat tenglamaga keltirish",
        "asosida o'zgaruvchi qatnashgan va logarifmlash bilan yechiladigan tenglamalar",
    ],
    3: [
        "log_a f(x) > b sodda tengsizliklar, asos 1 dan katta va kichik holatlar",
        "log_a f(x) > log_a g(x), aniqlanish sohasi bilan",
        "almashtirish bilan yechiladigan logarifmik tengsizliklar",
        "logarifmik tengsizlikning butun yechimlari soni yoki yig'indisi",
        "logarifmik tengsizliklar sistemasi",
    ],
    4: [
        "gradus va radian o'lchovi, birinchisidan ikkinchisiga o'tish",
        "birlik aylana, burchak qaysi chorakda yotishi",
        "yoy uzunligi va sektor yuzi",
        "sin, cos, tg, ctg ta'riflari (to'g'ri burchakli uchburchakda va aylanada)",
        "trigonometrik funksiyalar ishorasi choraklar bo'yicha",
    ],
    5: [
        "asosiy burchaklarda (30°, 45°, 60°, 90°…) trigonometrik qiymatlar",
        "trigonometrik ifodalarning son qiymatini hisoblash",
        "davriylik yordamida katta burchaklarni keltirish",
        "manfiy burchaklar, juft-toqlik xossasi",
        "trigonometrik qiymatlarni taqqoslash",
    ],
    6: [
        "sin²α + cos²α = 1 orqali bir funksiyadan boshqasini topish",
        "tgα berilganda sinα, cosα va kasr ifodalarni hisoblash",
        "ayniyatlar bilan ifodalarni soddalashtirish",
        "sinα + cosα berilganda sinα·cosα, sin³α + cos³α ni topish",
        "trigonometrik ayniyatlarni isbotlashga keltiriladigan hisoblashlar",
    ],
    7: [
        "keltirish formulalari bilan ifodalarni soddalashtirish",
        "keltirish formulalari bilan hisoblash (sin 150°, cos 210° …)",
        "sinuslar teoremasi: tomon yoki burchakni topish, tashqi chizilgan aylana radiusi",
        "kosinuslar teoremasi: uchinchi tomon, burchak kosinusi",
        "uchburchak turini aniqlash, uchburchak yuzi (½ab·sinC)",
    ],
    8: [
        "sin(α ± β), cos(α ± β) formulalari bilan hisoblash (sin 75°, cos 15°)",
        "tg(α ± β) formulasi",
        "qo'shish formulalarini teskari qo'llab ifodani yig'ish",
        "sinα, cosβ berilganda sin(α+β) ni topish (chorakni hisobga olib)",
        "qo'shish formulalari bilan soddalashtirish",
    ],
    9: [
        "sin2α, cos2α, tg2α formulalari bilan hisoblash",
        "ikkilangan burchak formulalari bilan soddalashtirish",
        "darajani pasaytirish formulalari",
        "sinα berilganda sin2α, cos2α ni topish",
        "uchlangan burchak va ko'paytmalar (cos20°·cos40°·cos80°)",
    ],
    10: [
        "sinα ± sinβ, cosα ± cosβ ni ko'paytmaga aylantirish",
        "ko'paytmani yig'indiga aylantirish",
        "yig'indi-ko'paytma formulalari bilan hisoblash",
        "ifodalarni soddalashtirish va qiymatini topish",
        "yig'indi formulalari bilan tenglamalarga tayyorlov masalalari",
    ],
    11: [
        "yarim burchak sinusi va kosinusi, ishorani tanlash",
        "yarim burchak tangensi formulalari",
        "tg(α/2) orqali sinα, cosα ni ifodalash",
        "yarim burchak formulalari bilan hisoblash (sin 15°, tg 22,5°)",
        "soddalashtirish va qiymat topish",
    ],
    12: [
        "arcsin, arccos, arctg, arcctg qiymatlarini hisoblash",
        "teskari trigonometrik funksiyalar aniqlanish sohasi va qiymatlar to'plami",
        "sin(arccos a), tg(arcsin a) kabi ifodalar",
        "arcsin a + arccos a = π/2 va shunga o'xshash ayniyatlar",
        "teskari trigonometrik funksiyalar qatnashgan sodda tenglamalar",
    ],
    13: [
        "trigonometrik funksiyalarning eng kichik musbat davri",
        "aniqlanish sohasi va qiymatlar to'plami",
        "juft-toqligi",
        "eng katta va eng kichik qiymat (a·sinx + b·cosx)",
        "monotonlik oraliqlari, grafiklarni taqqoslash",
    ],
    14: [
        "sodda trigonometrik tenglamalar (sinx = a, cosx = a, tgx = a)",
        "kvadrat tenglamaga keltiriladigan tenglamalar",
        "ko'paytuvchilarga ajratib yechiladigan tenglamalar",
        "berilgan oraliqdagi ildizlar soni yoki yig'indisi",
        "eng kichik musbat ildiz",
    ],
    15: [
        "bir jinsli trigonometrik tenglamalar",
        "a·sinx + b·cosx = c (yordamchi burchak usuli)",
        "yig'indi-ko'paytma va darajani pasaytirish formulalari bilan yechish",
        "trigonometrik tenglamalar sistemasi",
        "ildizlarni oraliqda tanlash, parametrli tenglamalar",
    ],
    16: [
        "sodda trigonometrik tengsizliklar (sinx > a, cosx ≤ a)",
        "tgx va ctgx qatnashgan tengsizliklar",
        "almashtirish bilan yechiladigan trigonometrik tengsizliklar",
        "oraliqdagi butun yechimlar",
        "trigonometrik tengsizliklar birlik aylanada",
    ],
    17: [
        "hosila ta'rifi, o'rtacha va oniy o'zgarish tezligi",
        "darajali funksiya, ko'phad hosilasi",
        "yig'indi, ko'paytma va bo'linma hosilasi",
        "trigonometrik, ko'rsatkichli va logarifmik funksiyalar hosilasi",
        "nuqtadagi hosila qiymatini hisoblash",
    ],
    18: [
        "murakkab funksiya hosilasi (zanjir qoidasi)",
        "ildiz va daraja ostidagi murakkab funksiyalar",
        "murakkab trigonometrik va logarifmik funksiyalar hosilasi",
        "f'(x) = 0 tenglamasini yechish",
        "ikkinchi tartibli hosila",
    ],
    19: [
        "funksiyaning o'sish va kamayish oraliqlari",
        "kritik nuqtalar, maksimum va minimum nuqtalari",
        "ekstremum qiymatlari",
        "kesmada funksiyaning eng katta va eng kichik qiymati",
        "optimallash masalalari (eng katta yuz, eng kichik perimetr)",
    ],
    20: [
        "urinma burchak koeffitsiyenti, urinma tenglamasi",
        "berilgan to'g'ri chiziqqa parallel urinma",
        "urinmaning o'qlar bilan hosil qilgan uchburchak yuzi",
        "harakat qonuni: tezlik va tezlanish",
        "grafik bo'yicha hosila ishorasini aniqlash",
    ],
    21: [
        "boshlang'ich funksiyalar jadvali",
        "aniqmas integral xossalari, ko'phad integrali",
        "berilgan nuqtadan o'tuvchi boshlang'ich funksiya",
        "trigonometrik va ko'rsatkichli funksiyalar integrali",
        "f(x) = F'(x) bog'lanishi bo'yicha masalalar",
    ],
    22: [
        "chiziqli almashtirish bilan integrallash (∫f(kx+b)dx)",
        "trigonometrik ifodalarni darajani pasaytirib integrallash",
        "kasr va ildizli funksiyalar integrali",
        "o'zgaruvchini almashtirish usuli",
        "bo'laklab integrallash (sodda hollar)",
    ],
    23: [
        "Nyuton–Leybnits formulasi bilan aniq integralni hisoblash",
        "egri chiziqli trapetsiya yuzi",
        "ikki chiziq bilan chegaralangan shakl yuzi",
        "aniq integral xossalari, parametrni topish",
        "integral yordamida harakat masalalari (yo'l)",
    ],
    24: [
        "qo'shish va ko'paytirish qoidasi",
        "o'rin almashtirishlar (n!)",
        "o'rinlashtirishlar A_n^k",
        "gruppalashlar C_n^k",
        "raqamlardan son tuzish, takrorlanuvchi tanlovlar",
    ],
    25: [
        "C_n^k xossalari, Paskal uchburchagi",
        "Nyuton binomi: n-had va koeffitsiyent",
        "binom koeffitsiyentlari yig'indisi",
        "x qatnashmagan had, eng katta koeffitsiyent",
        "kombinatorik tenglamalar (C_n^2 = 15 va h.k.)",
    ],
    26: [
        "to'plamlar ustida amallar, Eyler–Venn diagrammasi",
        "kesishma va birlashma elementlari soni (inklyuziya–ekskluziya)",
        "klassik ehtimollik (tanga, kubik, sharlar)",
        "qarama-qarshi hodisa, qo'shish va ko'paytirish teoremalari",
        "kombinatorika yordamida ehtimollikni hisoblash",
    ],
}

# book number (--book) → its title in the database and its topic guide
BOOKS: dict[int, tuple[str, dict[int, list[str]]]] = {
    1: ("Matematika 1-qism", TOPIC_GUIDE),
    2: ("Matematika 2-qism", TOPIC_GUIDE_2),
    3: ("Matematika 3-qism", TOPIC_GUIDE_3),
}
current_book = 1  # chosen with --book or in the menu

FIGURE_HINT = (
    "Rasmli testlar uchun mavzuga tabiiy mos chizma tanlang: geometriyada shakl (tomonlar, burchaklar, katakchalar), "
    "funksiya va tenglamalarda grafik, tengsizlik va sonlarda son o'qi, foiz, nisbat va matnli masalalarda jadval "
    "yoki ustunli diagramma. Kerakli ma'lumot faqat chizmada bo'lsin."
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()


def say(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def parse_topics(spec: str) -> list[int]:
    """'5-10' → 5..10, '1,3,7' → [1,3,7], '1-3,8' → [1,2,3,8]."""
    out: set[int] = set()
    for part in re.split(r"[,\s]+", spec.strip()):
        if not part:
            continue
        m = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", part)
        if m:
            a, b = sorted((int(m.group(1)), int(m.group(2))))
            out.update(range(a, b + 1))
        elif part.isdigit():
            out.add(int(part))
        else:
            raise ValueError(f"tushunarsiz: {part!r} (masalan: 5-10 yoki 1,3,7)")
    return sorted(out)


def save_figure(svg: str) -> str:
    folder = Path(get_settings().media_dir) / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(8)}.svg"
    (folder / name).write_text(svg, encoding="utf-8")
    return f"/api/media/figures/{name}"


def remove_figure(url: str | None) -> None:
    if url and "/figures/" in url:
        (Path(get_settings().media_dir) / "figures" / url.rsplit("/", 1)[1]).unlink(missing_ok=True)


def bucket(q: Question) -> str:
    return "figure" if q.image_url and "/figures/" in q.image_url else q.difficulty


async def topic_questions(topic_id: int) -> list[Question]:
    async with SessionLocal() as s:
        return list((await s.execute(select(Question).where(Question.topic_id == topic_id).order_by(Question.position))).scalars())


async def counts_for(topic_id: int) -> dict[str, int]:
    c = {"easy": 0, "medium": 0, "hard": 0, "figure": 0, "solved": 0}
    for q in await topic_questions(topic_id):
        b = bucket(q)
        if b in c:
            c[b] += 1
        c["solved"] += q.solution is not None
    return c


async def store(topic_id: int, questions: list[ai.GeneratedQuestion]) -> int:
    async with SessionLocal() as s:
        last = (await s.execute(select(func.coalesce(func.max(Question.position), 0)).where(Question.topic_id == topic_id))).scalar_one()
        for i, q in enumerate(questions, start=1):
            s.add(
                Question(
                    topic_id=topic_id,
                    position=last + i,
                    difficulty=q.difficulty,
                    text=q.text,
                    options=q.options,
                    correct=q.correct,
                    explanation=q.explanation or None,
                    image_url=save_figure(q.figure_svg) if q.figure_svg else None,
                    solution=q.solution,
                )
            )
        await s.commit()
    return len(questions)


class Stats:
    def __init__(self) -> None:
        self.saved = self.rejected = self.calls = self.errors = self.solutions = self.no_solution = 0
        self.tokens_in = self.tokens_out = 0


def fatal(e: Exception) -> bool:
    text = str(e)
    return any(w in text for w in ("sozlanmagan", "kaliti", "balans", "ruxsat"))


# ─── generating tests ────────────────────────────────────────────────────────


async def fill_topic(topic: Topic, book: Book, subject: str, verify: bool, stats: Stats, sem: asyncio.Semaphore) -> None:
    families = BOOKS[current_book][1].get(topic.number or 0, [])
    label = f"{topic.number}-mavzu"
    batch_no = 0
    for key, difficulty, figure, target, size in PLAN:
        fails = 0
        for _ in range(MAX_ROUNDS + target // size):
            if fails >= MAX_FAILS:
                say(f"  {label} {key}: {fails} marta ketma-ket xato — token behuda ketmasligi uchun keyingi bo'limga o'tildi")
                break
            have = (await counts_for(topic.id))[key]
            need = target - have
            if need <= 0:
                break
            n = min(size, need)
            focus = [families[(batch_no + k) % len(families)] for k in range(2)] if families else []
            batch_no += 1
            notes = ""
            if focus:
                notes = "Bu to'plamda asosan quyidagi turdagi misollar bo'lsin: " + "; ".join(focus) + ". "
            notes += "Kitob uslubida: bir xil g'oya, sonlari har xil; har bir savol mustaqil va to'liq bo'lsin."
            notes += " Kasrlar kitobdagidek ustma-ust: savol, variant va yechimda faqat $\\frac{a}{b}$ LaTeX, hech qachon a/b emas."
            if figure:
                notes += " " + FIGURE_HINT
            seen = [q.text for q in await topic_questions(topic.id)]
            async with sem:
                try:
                    stats.calls += 1
                    drafts, usage = await ai.generate_questions(
                        subject=subject,
                        book=book.title,
                        topic=topic.title,
                        topic_number=topic.number,
                        difficulty=difficulty,
                        count=0 if figure else n,
                        figure_count=n if figure else 0,
                        existing=[t[:140] for t in seen[-60:]],
                        notes=notes,
                    )
                    stats.tokens_in += usage["input_tokens"]
                    stats.tokens_out += usage["output_tokens"]
                    drafts = [d for d in drafts if bool(d.figure_svg) == figure]
                    known = {norm(t) for t in seen}
                    unique = []
                    for d in drafts:
                        k = norm(d.text)
                        if k not in known:
                            known.add(k)
                            unique.append(d)
                    drafts = unique[:n]
                    if verify and drafts:
                        stats.calls += 1
                        try:
                            ok = await ai.verify(drafts)
                        except Exception:  # don't throw away a paid generation over one bad verifier reply
                            stats.calls += 1
                            ok = await ai.verify(drafts)
                        kept = [d for d, good in zip(drafts, ok) if good]
                        stats.rejected += len(drafts) - len(kept)
                        drafts = kept
                except ai.GenerationError as e:
                    stats.errors += 1
                    say(f"  {label} {key}: xato — {e}")
                    if fatal(e):
                        raise
                    fails += 1
                    await asyncio.sleep(5)
                    continue
                except Exception as e:  # network hiccup, bad JSON from the verifier, …
                    stats.errors += 1
                    say(f"  {label} {key}: kutilmagan xato — {e!r}")
                    fails += 1
                    await asyncio.sleep(5)
                    continue
            fails = 0
            saved = await store(topic.id, drafts)
            stats.saved += saved
            with_sol = sum(d.solution is not None for d in drafts)
            stats.solutions += with_sol
            say(f"  {label} {key}: +{saved} (jami {have + saved}/{target}, yechimi bilan {with_sol})")
    # tests whose solution failed the checks get one more chance through the solution writer
    await explain_topic(topic, missing_only=True, stats=stats, sem=sem, quiet=True)
    c = await counts_for(topic.id)
    total = c["easy"] + c["medium"] + c["hard"] + c["figure"]
    say(
        f"✓ {label} «{topic.title}»: oson {c['easy']}, o'rta {c['medium']}, qiyin {c['hard']}, rasmli {c['figure']} "
        f"· yechimli {c['solved']}/{total}"
    )


# ─── (re)writing worked solutions ────────────────────────────────────────────


async def explain_topic(topic: Topic, missing_only: bool, stats: Stats, sem: asyncio.Semaphore, quiet: bool = False) -> None:
    label = f"{topic.number}-mavzu"
    questions = [q for q in await topic_questions(topic.id) if not (missing_only and q.solution)]
    if not questions:
        if not quiet:
            say(f"✓ {label}: yechim yozadigan test yo'q")
        return
    if not quiet:
        say(f"  {label}: {len(questions)} ta testga yechim yoziladi")
    done = failed = 0
    for i in range(0, len(questions), EXPLAIN_BATCH):
        chunk = questions[i : i + EXPLAIN_BATCH]
        payload = [{"text": q.text, "options": q.options, "correct": q.correct} for q in chunk]
        async with sem:
            try:
                stats.calls += 1
                solutions = await ai.explain(payload, f"{topic.number}. {topic.title}")
            except ai.GenerationError as e:
                stats.errors += 1
                say(f"  {label} yechim: xato — {e}")
                if fatal(e):
                    raise
                continue
            except Exception as e:
                stats.errors += 1
                say(f"  {label} yechim: kutilmagan xato — {e!r}")
                await asyncio.sleep(5)
                continue
        async with SessionLocal() as s:
            for q, sol in zip(chunk, solutions):
                if sol is None:
                    failed += 1
                    continue
                row = await s.get(Question, q.id)
                if row is not None:
                    row.solution = sol
                    done += 1
            await s.commit()
    stats.solutions += done
    stats.no_solution += failed
    if not quiet or done or failed:
        say(f"✓ {label}: {done} ta yechim yozildi" + (f", {failed} tasi tekshiruvdan o'tmadi" if failed else ""))


# ─── entry points ────────────────────────────────────────────────────────────


async def load(topic_numbers: list[int] | None) -> tuple[Book, str, list[Topic]]:
    title = BOOKS[current_book][0]
    async with SessionLocal() as s:
        book = (await s.execute(select(Book).where(Book.title.ilike(f"%{title}%")).order_by(Book.id))).scalars().first()
        if book is None:
            raise SystemExit(f"«{title}» kitobi bazada topilmadi.")
        subject = book.subject.name
        topics = list(
            (await s.execute(select(Topic).where(Topic.book_id == book.id, Topic.kind == "lesson").order_by(Topic.position))).scalars()
        )
    if topic_numbers:
        missing = sorted(set(topic_numbers) - {t.number for t in topics})
        if missing:
            print(f"Ogohlantirish: kitobda bunday mavzu yo'q: {missing}")
        topics = [t for t in topics if t.number in topic_numbers]
    return book, subject, topics


async def reset_topics(topics: list[Topic]) -> None:
    ids = [t.id for t in topics]
    async with SessionLocal() as s:
        for q in (await s.execute(select(Question).where(Question.topic_id.in_(ids)))).scalars():
            remove_figure(q.image_url)
        n_q = (await s.execute(delete(Question).where(Question.topic_id.in_(ids)))).rowcount
        n_a = (await s.execute(delete(TestAttempt).where(TestAttempt.topic_id.in_(ids)))).rowcount
        await s.commit()
    say(f"Tozalandi: {n_q} ta test va {n_a} ta natija ({len(topics)} ta mavzu).")


async def show_status(topics: list[Topic]) -> None:
    per_topic = sum(t for _, _, _, t, _ in PLAN)
    print(f"{'':>4} {'Mavzu':<58} {'oson':>5} {'o‘rta':>5} {'qiyin':>5} {'rasm':>5} {'jami':>6} {'yechim':>7}")
    for t in topics:
        c = await counts_for(t.id)
        total = c["easy"] + c["medium"] + c["hard"] + c["figure"]
        print(f"{t.number:>3}. {t.title[:58]:<58} {c['easy']:>5} {c['medium']:>5} {c['hard']:>5} {c['figure']:>5} {total:>4}/{per_topic} {c['solved']:>7}")


async def run_generate(topic_numbers: list[int], reset: bool, verify: bool, parallel: int) -> None:
    book, subject, topics = await load(topic_numbers)
    if not topics:
        print("Mavzu tanlanmadi.")
        return
    say(f"Test tuzish: {book.title}, {', '.join(str(t.number) for t in topics)}-mavzular · har biriga {sum(p[3] for p in PLAN)} ta · AI: {ai.ai_status()['model']}")
    if reset:
        await reset_topics(topics)
    stats = Stats()
    sem = asyncio.Semaphore(max(1, parallel))
    started = time.monotonic()
    try:
        await asyncio.gather(*(fill_topic(t, book, subject, verify, stats, sem) for t in topics))
    except ai.GenerationError as e:
        say(f"To'xtatildi: {e}")
    report(stats, started)


async def run_solutions(topic_numbers: list[int], missing_only: bool, parallel: int) -> None:
    book, _, topics = await load(topic_numbers)
    if not topics:
        print("Mavzu tanlanmadi.")
        return
    say(f"{book.title}: yechimlarni {'to‘ldirish' if missing_only else 'qayta yozish'}: {', '.join(str(t.number) for t in topics)}-mavzular")
    stats = Stats()
    sem = asyncio.Semaphore(max(1, parallel))
    started = time.monotonic()
    try:
        await asyncio.gather(*(explain_topic(t, missing_only, stats, sem) for t in topics))
    except ai.GenerationError as e:
        say(f"To'xtatildi: {e}")
    report(stats, started)


def report(stats: Stats, started: float) -> None:
    minutes = (time.monotonic() - started) / 60
    say(
        f"Tayyor: {stats.saved} ta yangi test, {stats.solutions} ta yechim, {stats.rejected} ta test tekshiruvdan o'tmadi, "
        f"{stats.no_solution} ta yechim rad etildi, {stats.errors} ta xato, {stats.calls} ta AI so'rovi, "
        f"{minutes:.1f} daqiqa."
    )


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def ask_topics(prompt: str) -> list[int]:
    while True:
        spec = ask(prompt)
        if not spec:
            return []
        try:
            return parse_topics(spec)
        except ValueError as e:
            print(f"  {e}")


def choose_book() -> None:
    global current_book
    print("Qaysi kitob?")
    for n, (title, _) in BOOKS.items():
        print(f"  {n}. {title}")
    while True:
        choice = ask(f"Kitob raqami [Enter = {current_book}]: ")
        if not choice:
            return
        if choice.isdigit() and int(choice) in BOOKS:
            current_book = int(choice)
            return
        print(f"  {', '.join(map(str, BOOKS))} dan birini kiriting.")


async def menu(parallel: int, book_given: bool) -> None:
    if not book_given:
        choose_book()
    while True:
        print()
        print(f"══════════ QANOT.AI · Test tuzish ({BOOKS[current_book][0]}) ══════════")
        print("  1. Test tuzish            — mavzular oralig'ini kiriting (masalan 5-10)")
        print("  2. Yechimlarni qayta ishlash — mavzularni kiriting (masalan 4,6,7)")
        print("  3. Holatni ko'rish        — qaysi mavzuda nechta test va yechim bor")
        print("  4. Yozuvni tozalash       — 8^2025 kabi yozuvlarni 8²⁰²⁵ ko'rinishiga keltirish")
        print("  5. Kitobni almashtirish")
        print("  0. Chiqish")
        choice = ask("Tanlang: ")
        if choice in ("0", "", "q"):
            return
        if choice == "1":
            topics = ask_topics("Qaysi mavzular? (masalan 5-10 yoki 1,3,7): ")
            if not topics:
                continue
            reset = ask("Shu mavzulardagi bor testlarni o'chirib, boshidan tuzaymi? [h = ha / Enter = yo'q, to'ldirish]: ").lower() in ("h", "ha")
            await run_generate(topics, reset=reset, verify=True, parallel=parallel)
        elif choice == "2":
            topics = ask_topics("Qaysi mavzular? (masalan 4,6,7 yoki 1-5): ")
            if not topics:
                continue
            only = ask("Faqat yechimi yo'q testlarga yozaymi? [Enter = hammasiga qayta / y = faqat yo'qlariga]: ").lower() in ("y", "ha", "h")
            await run_solutions(topics, missing_only=only, parallel=parallel)
        elif choice == "3":
            _, _, topics = await load(None)
            await show_status(topics)
        elif choice == "4":
            await fix_notation()
        elif choice == "5":
            choose_book()
        else:
            print("  1, 2, 3, 4, 5 yoki 0 ni tanlang.")


async def fix_notation() -> None:
    """Rewrite programmer-style powers (8^2025, 2**10) already stored in tests into school notation (8²⁰²⁵)."""
    changed = 0
    async with SessionLocal() as s:
        for q in (await s.execute(select(Question))).scalars():
            text, options = normalize(q.text), [normalize(o) for o in q.options]
            explanation, solution = normalize(q.explanation), normalize_solution(q.solution)
            if (text, options, explanation, solution) != (q.text, q.options, q.explanation, q.solution):
                q.text, q.options, q.explanation, q.solution = text, options, explanation, solution
                changed += 1
        await s.commit()
    say(f"Yozuv tozalandi: {changed} ta testda daraja belgilari (^, **) maktab ko'rinishiga keltirildi.")


async def main() -> int:
    global current_book
    p = argparse.ArgumentParser(description="Matematika kitoblari: AI bilan test va yechim tuzish")
    p.add_argument("--book", type=int, choices=sorted(BOOKS), help="kitob: 1, 2 yoki 3 (Matematika 1-, 2-, 3-qism)")
    p.add_argument("--topics", nargs="*", default=[], help="test tuzish uchun mavzular: 5-10 yoki 1,3,7")
    p.add_argument("--reset", action="store_true", help="--topics dagi mavzular testlarini o'chirib, boshidan tuzish")
    p.add_argument("--solutions", nargs="*", default=[], help="yechimni qayta yozish uchun mavzular: 4,6,7")
    p.add_argument("--missing-only", action="store_true", help="--solutions bilan: faqat yechimi yo'q testlarga")
    p.add_argument("--status", action="store_true", help="mavzular bo'yicha holatni ko'rsatish")
    p.add_argument("--fix-notation", action="store_true", help="bazadagi 8^2025 kabi yozuvlarni 8²⁰²⁵ ga keltirish")
    p.add_argument("--parallel", type=int, default=3, help="bir vaqtda nechta mavzu ustida ishlash (standart 3)")
    p.add_argument("--no-verify", dest="verify", action="store_false", help="test javoblarini ikkinchi marta tekshirmaslik")
    args = p.parse_args()
    if args.book:
        current_book = args.book
    elif args.topics or args.solutions or args.status:
        print(f"Kitob: {BOOKS[current_book][0]} (boshqa kitob uchun --book 2)")

    await init_db()
    if args.status:
        _, _, topics = await load(None)
        await show_status(topics)
        return 0
    if args.fix_notation:
        await fix_notation()
        return 0

    status = ai.ai_status()
    if not status["configured"]:
        print("AI sozlanmagan: .env faylida AI_URL, AI_KEY va AI_MODEL ni kiriting, so'ng `docker compose up -d backend`.")
        return 1

    try:
        if args.topics:
            await run_generate(parse_topics(" ".join(args.topics)), args.reset, args.verify, args.parallel)
        elif args.solutions:
            await run_solutions(parse_topics(" ".join(args.solutions)), args.missing_only, args.parallel)
        else:
            print(f"AI: {status['model']} ({status['host']})")
            await menu(args.parallel, book_given=bool(args.book))
    except ValueError as e:
        print(e)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nTo'xtatildi. Qayta ishga tushirsangiz, qolgan joyidan davom etadi.")
