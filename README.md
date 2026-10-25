# QANOT.AI

| Papka | Nima |
|---|---|
| `qanotai_front/` | Next.js sayt va kabinet (`/dashboard`) |
| `qanotai_back/` | FastAPI API (`app/main.py`) va Telegram bot (`app/bot.py`) |
| `docker-compose.yml` | PostgreSQL + backend + bot + frontend |

## Ishga tushirish

```bash
cp .env.example .env   # birinchi marta: tokenlar va parollarni to'ldiring
docker compose up -d --build
```

- Sayt: http://localhost:3080
- API hujjatlari: http://localhost:8080/docs

To'xtatish: `docker compose down` (baza `pgdata` volume'da saqlanib qoladi).

## Kirish usullari

**Telegram.** Sayt bir martalik token yaratadi va botni `t.me/<bot>?start=<token>` bilan ochadi. Bot inline
«✅ Tasdiqlash / ❌ Bekor qilish» tugmalarini yuboradi. Sayt holatni har 2 soniyada tekshiradi va tasdiqlangach
kabinetga o'tkazadi. Birinchi marta kirganda bot telefon raqamini so'raydi (ixtiyoriy).

**Google.** `.env` da `GOOGLE_CLIENT_ID` va `GOOGLE_CLIENT_SECRET` bo'lishi kerak:
[Google Cloud Console](https://console.cloud.google.com/apis/credentials) → *Create credentials* → *OAuth client ID* →
*Web application*. *Authorized redirect URI*: `http://localhost:3080/api/auth/google/callback`
(serverda — `PUBLIC_URL` + `/api/auth/google/callback`).

## Superadmin panel

http://localhost:3080/superadmin — dashboard, foydalanuvchilar, fanlar va kitoblar (muqova yuklash bilan).

Kim superadmin ekanini `.env` belgilaydi (vergul bilan bir nechta):

```bash
SUPERADMIN_TELEGRAM_IDS=123456789
SUPERADMIN_EMAILS=admin@example.com
```

O'zgartirgandan keyin: `docker compose up -d backend`. Yuklangan muqovalar `media` volume'da saqlanadi.
Birinchi ishga tushishda 6 ta asosiy fan va har biriga bitta kitob avtomatik qo'shiladi.

## AI test generator

Superadmin → Kitoblar → mavzu → «✨ AI bilan yaratish». Istalgan provayder ishlaydi — `.env` da:

```bash
AI_URL=https://...    # provayder API manzili (OpenAI uslubida odatda .../v1 bilan tugaydi)
AI_KEY=...            # shu provayderning kaliti
AI_MODEL=...          # model nomi
AI_FORMAT=openai      # openai (ko'pchilik provayderlar) yoki anthropic (Claude uslubi)
```

O'zgartirgandan keyin: `docker compose up -d backend`.

## Lokal ishlab chiqish (Dockersiz frontend)

```bash
docker compose up -d db backend bot
cd qanotai_front && npm run dev     # /api/* → http://localhost:8080 ga proksi qilinadi
```

## Serverga chiqarishda

- `.env` da `PUBLIC_URL=https://sizning-domen.uz`, `COOKIE_SECURE=true` va yangi `JWT_SECRET` qo'ying.
- Jadvallar backend ishga tushganda avtomatik yaratiladi (`create_all`); sxema o'zgara boshlasa Alembic qo'shish kerak.
