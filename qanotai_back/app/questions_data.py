"""Starter tests for "Matematika 1-qism", topic 1 — "Natural sonlar va ular ustida amallar".

Each entry: (difficulty, text, options, index of the correct option, explanation).
Answers were checked by computation; wrong options are the usual mistakes (operation order, off-by-one, etc.).
"""

NATURAL_SONLAR: list[tuple[str, str, list[str], int, str]] = [
    (
        "easy",
        "Hisoblang: 2345 + 6789",
        ["9134", "9124", "9034", "8134"],
        0,
        "Xonalar bo'yicha qo'shamiz: 5+9=14 (4 yoziladi, 1 eslab qolinadi), 4+8+1=13, 3+7+1=11, 2+6+1=9. Natija: 9134.",
    ),
    (
        "easy",
        "Eng kichik to'rt xonali natural son bilan eng katta uch xonali natural sonning ayirmasini toping.",
        ["1", "0", "9", "99"],
        0,
        "Eng kichik to'rt xonali son 1000, eng katta uch xonali son 999. 1000 − 999 = 1.",
    ),
    (
        "easy",
        "Qulay usulda hisoblang: 125 · 8 · 37",
        ["37000", "3700", "370000", "29600"],
        0,
        "125 · 8 = 1000 bo'lgani uchun 1000 · 37 = 37000.",
    ),
    (
        "medium",
        "Hisoblang: 999 · 999 + 999",
        ["999000", "998001", "999999", "1000000"],
        0,
        "999 ni qavsdan tashqariga chiqaramiz: 999 · (999 + 1) = 999 · 1000 = 999000.",
    ),
    (
        "medium",
        "1 dan 100 gacha bo'lgan barcha natural sonlar yig'indisini toping.",
        ["5050", "5000", "4950", "5100"],
        0,
        "Juftlab qo'shamiz: 1+100 = 2+99 = … = 101, bunday juftlar 50 ta. 101 · 50 = 5050.",
    ),
    (
        "medium",
        "Ikki xonali natural sonlar nechta?",
        ["90", "99", "89", "100"],
        0,
        "Ikki xonali sonlar 10 dan 99 gacha: 99 − 10 + 1 = 90 ta.",
    ),
    (
        "medium",
        "Ifodaning qiymatini toping: 48 : 4 · 3 + 15",
        ["51", "19", "4", "49"],
        0,
        "Bo'lish va ko'paytirish chapdan o'ngga bajariladi: 48 : 4 = 12, 12 · 3 = 36, 36 + 15 = 51. "
        "(19 javobi 4 · 3 ni avval hisoblash xatosidan chiqadi.)",
    ),
    (
        "hard",
        "1 dan 200 gacha bo'lgan natural sonlar ichida 3 ga ham, 5 ga ham bo'linmaydiganlari nechta?",
        ["107", "93", "113", "120"],
        0,
        "3 ga bo'linadiganlar: 66 ta, 5 ga: 40 ta, 15 ga (ikkalasiga): 13 ta. "
        "3 yoki 5 ga bo'linadiganlar: 66 + 40 − 13 = 93 ta. Bo'linmaydiganlar: 200 − 93 = 107 ta.",
    ),
    (
        "hard",
        "Raqamlari yig'indisi 5 ga teng bo'lgan uch xonali natural sonlar nechta?",
        ["15", "21", "10", "12"],
        0,
        "Son abc, a ≥ 1 va a + b + c = 5. a' = a − 1 desak, a' + b + c = 4 tenglamaning manfiy bo'lmagan "
        "butun yechimlari soni C(6, 2) = 15 ta.",
    ),
    (
        "hard",
        "1 · 2 · 3 · … · 25 ko'paytma nechta nol bilan tugaydi?",
        ["6", "5", "4", "7"],
        0,
        "Har bir nol 2 · 5 juftidan hosil bo'ladi, 5 lar soni hal qiladi: [25/5] + [25/25] = 5 + 1 = 6.",
    ),
]


# Topic 2 — "Boʻlinish belgilari, tub va murakkab sonlar"
BOLINISH_BELGILARI: list[tuple[str, str, list[str], int, str]] = [
    (
        "easy",
        "Quyidagi sonlardan qaysi biri 3 ga bo'linadi?",
        ["2541", "2543", "2546", "2549"],
        0,
        "Son 3 ga bo'linishi uchun raqamlari yig'indisi 3 ga bo'linishi kerak. 2+5+4+1 = 12 — 3 ga bo'linadi; "
        "qolganlarida yig'indi 14, 17, 20.",
    ),
    (
        "easy",
        "Quyidagi sonlardan qaysi biri tub son?",
        ["97", "91", "87", "51"],
        0,
        "91 = 7 · 13, 87 = 3 · 29, 51 = 3 · 17 — murakkab sonlar. 97 esa √97 < 10 gacha bo'lgan 2, 3, 5, 7 "
        "tub sonlarning hech biriga bo'linmaydi, demak tub.",
    ),
    (
        "easy",
        "1 dan 20 gacha bo'lgan natural sonlar ichida nechta tub son bor?",
        ["8", "9", "7", "10"],
        0,
        "Tub sonlar: 2, 3, 5, 7, 11, 13, 17, 19 — jami 8 ta. (1 tub ham, murakkab ham emas.)",
    ),
    (
        "medium",
        "4a52 to'rt xonali son 9 ga bo'linishi uchun a raqami nechaga teng bo'lishi kerak?",
        ["7", "2", "5", "9"],
        0,
        "Raqamlar yig'indisi 4 + a + 5 + 2 = 11 + a, u 9 ga bo'linishi kerak. a raqam bo'lgani uchun "
        "11 + a = 18, ya'ni a = 7.",
    ),
    (
        "medium",
        "24 sonining natural bo'luvchilari nechta?",
        ["8", "6", "7", "10"],
        0,
        "24 = 2³ · 3, bo'luvchilar soni (3 + 1)(1 + 1) = 8: 1, 2, 3, 4, 6, 8, 12, 24.",
    ),
    (
        "medium",
        "Quyidagi sonlardan qaysi biri 4 ga bo'linadi?",
        ["7916", "3726", "5834", "2318"],
        0,
        "Son 4 ga bo'linishi uchun oxirgi ikki raqamidan tuzilgan son 4 ga bo'linishi kerak: "
        "16 bo'linadi, 26, 34, 18 esa bo'linmaydi.",
    ),
    (
        "medium",
        "Eng kichik ikki xonali tub son bilan eng katta ikki xonali tub sonning yig'indisini toping.",
        ["108", "110", "106", "100"],
        0,
        "Eng kichik ikki xonali tub son 11, eng katta ikki xonali tub son 97 (99 = 9 · 11, 98 juft). 11 + 97 = 108.",
    ),
    (
        "hard",
        "7x36y besh xonali son 45 ga bo'linadi. x + y ning eng katta qiymatini toping.",
        ["11", "2", "9", "13"],
        0,
        "45 = 5 · 9. 5 ga bo'linishi uchun y = 0 yoki y = 5. 9 ga bo'linishi uchun 7 + x + 3 + 6 + y = 16 + x + y "
        "9 ga bo'linishi kerak: y = 0 da x = 2, y = 5 da x = 6. Eng katta x + y = 6 + 5 = 11.",
    ),
    (
        "hard",
        "100 dan kichik tub sonlar nechta?",
        ["25", "24", "26", "23"],
        0,
        "Har o'nlikda: 1–10 da 4 ta, 11–20 da 4, 21–30 da 2, 31–40 da 2, 41–50 da 3, 51–60 da 2, 61–70 da 2, "
        "71–80 da 3, 81–90 da 2, 91–99 da 1 (97). Jami 25 ta.",
    ),
    (
        "hard",
        "1 dan 50 gacha bo'lgan natural sonlar ichida nechta murakkab son bor?",
        ["34", "35", "33", "36"],
        0,
        "1 dan 50 gacha 15 ta tub son bor, 1 esa tub ham, murakkab ham emas. Murakkab sonlar: 50 − 15 − 1 = 34. "
        "(35 javobi 1 ni murakkab deb hisoblash xatosidan chiqadi.)",
    ),
]
