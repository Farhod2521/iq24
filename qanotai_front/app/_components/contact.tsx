"use client";

import Image from "next/image";
import { useState, type FormEvent } from "react";
import { Check, Heart } from "./icons";
import { Container, Eyebrow, formatPhone } from "./ui";

const field =
  "w-full rounded-2xl bg-brand-50/60 px-5 py-4 text-base text-ink ring-1 ring-brand-100 outline-none transition placeholder:text-muted/70 focus:bg-white focus:ring-2 focus:ring-brand-500";

export function Contact() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (name.trim().length < 3) return setError("Ism va familiyangizni kiriting.");
    if (phone.replace(/\D/g, "").length !== 9) return setError("Telefon raqamni to'liq kiriting.");
    if (message.trim().length < 5) return setError("Xabaringizni yozing.");
    setError("");
    // TODO: send { name, phone: "+998" + digits, message } to the backend once the endpoint exists
    setSent(true);
  }

  function reset() {
    setName("");
    setPhone("");
    setMessage("");
    setSent(false);
  }

  return (
    <section id="boglanish" className="py-12 lg:py-20">
      <Container className="grid items-center gap-10 lg:grid-cols-[1fr_1.15fr]">
        <div>
          <Eyebrow>Bog&apos;lanish</Eyebrow>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">Biz bilan bog&apos;laning</h2>
          <p className="mt-2 text-muted sm:text-lg">
            Savolingiz yoki taklifingiz bormi? Ma&apos;lumotlaringizni qoldiring — tez orada siz bilan bog&apos;lanamiz.
          </p>

          <div className="relative mt-8 flex items-end gap-2">
            <Image src="/images/owl-hero.png" alt="" width={703} height={900} className="w-40 sm:w-48" />
            <div className="relative mb-24 rounded-2xl rounded-bl-sm bg-white px-4 py-3 text-sm font-semibold text-brand-700 shadow-card ring-1 ring-brand-100">
              Yozib qoldiring,
              <br />
              albatta javob beramiz! <Heart className="inline size-4 text-brand-500" />
            </div>
          </div>
        </div>

        <div className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-brand-100/70 sm:p-8">
          {sent ? (
            <div className="flex flex-col items-center py-10 text-center">
              <span className="grid size-16 place-items-center rounded-full bg-emerald-500 text-white">
                <Check className="size-8" strokeWidth={3} />
              </span>
              <h3 className="mt-5 text-2xl font-extrabold text-ink">Xabaringiz yuborildi!</h3>
              <p className="mt-2 text-muted">Tez orada siz bilan bog&apos;lanamiz.</p>
              <button
                type="button"
                onClick={reset}
                className="mt-6 rounded-full px-5 py-2.5 text-sm font-semibold text-brand-600 ring-1 ring-brand-200 transition-colors hover:bg-brand-50"
              >
                Yana xabar yuborish
              </button>
            </div>
          ) : (
            <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
              <label className="flex flex-col gap-2">
                <span className="text-sm font-semibold text-ink">Ism familiya</span>
                <input
                  type="text"
                  name="name"
                  autoComplete="name"
                  placeholder="Masalan: Aziz Karimov"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={field}
                />
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-sm font-semibold text-ink">Telefon raqami</span>
                <div className="flex items-center rounded-2xl bg-brand-50/60 ring-1 ring-brand-100 transition focus-within:bg-white focus-within:ring-2 focus-within:ring-brand-500">
                  <span className="pl-5 text-base font-semibold text-ink">+998</span>
                  <input
                    type="tel"
                    name="phone"
                    autoComplete="tel-national"
                    inputMode="numeric"
                    placeholder="90 123 45 67"
                    value={phone}
                    onChange={(e) => setPhone(formatPhone(e.target.value))}
                    className="w-full bg-transparent py-4 pl-2 pr-5 text-base text-ink outline-none placeholder:text-muted/70"
                  />
                </div>
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-sm font-semibold text-ink">Xabar</span>
                <textarea
                  name="message"
                  rows={5}
                  placeholder="Savol yoki taklifingizni yozing..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className={`${field} resize-none`}
                />
              </label>

              {error && <p className="text-sm font-medium text-red-600">{error}</p>}

              <button
                type="submit"
                className="mt-1 rounded-full bg-brand-600 px-8 py-4 text-lg font-bold text-white shadow-xl shadow-brand-600/30 transition-colors hover:bg-brand-700"
              >
                Yuborish
              </button>
            </form>
          )}
        </div>
      </Container>
    </section>
  );
}
