#!/usr/bin/env python3
"""Build Russian 3000-word vocabulary from RNC frequency list."""
import csv
import json
import re
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "vocab-data.js"
CSV_URL = "https://raw.githubusercontent.com/LingData2019/LingData/master/data/freq_rnc_ranked.csv"
CSV_LOCAL = Path(__file__).parent / "freq_rnc_ranked.csv"
TOTAL = 3000
LEVELS = 60
WORDS_PER_LEVEL = TOTAL // LEVELS

POS_CAT = {
    "conj": "core", "part": "core", "pr": "core", "spro": "core", "apro": "core",
    "adv": "core", "advpro": "core", "num": "core", "intj": "core",
    "v": "action", "vi": "action", "vt": "action",
    "s": "world", "a": "emotions", "anom": "world", "sgeo": "world",
}

TOPIC_KEYWORDS = {
    "study": ("школ", "универс", "учеб", "экзам", "наук", "книг", "читать", "писать", "язык", "слов"),
    "people": ("человек", "люд", "семь", "друг", "ребен", "муж", "жен", "брат", "сестр", "род"),
    "nature": ("вод", "мор", "лес", "гор", "неб", "солн", "земл", "живот", "растен", "погод"),
    "academic": ("государ", "обществ", "эконом", "полит", "истор", "культур", "прав", "закон"),
    "school": ("класс", "урок", "учител", "ученик", "студент", "диплом"),
    "emotions": ("люб", "страх", "рад", "груст", "счаст", "зл", "чувств", "надеж"),
}

POS_UZ = {
    "conj": "bog'lovchi", "part": "yordamchi so'z", "pr": "predlog",
    "spro": "olmoshi", "apro": "ko'rsatkich olmoshi", "adv": "ravish",
    "advpro": "ravish olmoshi", "v": "fe'l", "s": "ot", "a": "sifat", "num": "son",
}

# Manual Uzbek translations for top function words (better quality than auto-translate)
MANUAL_UZ = {
    "и": "va", "в": "da / ichida", "не": "emas / yo'q", "на": "ustida / -ga",
    "я": "men", "быть": "bo'lmoq", "он": "u (erkak)", "с": "bilan / dan",
    "что": "nima / ki", "а": "lekin / va", "по": "bo'ylab / -ga qarab",
    "это": "bu", "она": "u (ayol)", "этот": "bu (ko'rsatkich)", "к": "ga / -ga",
    "но": "lekin", "они": "ular", "мы": "biz", "как": "qanday / kabi",
    "из": "dan / -dan", "у": "da (kimdadir)", "который": "qaysi / -gan",
    "то": "u / shu", "за": "orqasida / uchun", "свой": "o'z (nisbiy)",
    "весь": "butun / hamma", "год": "yil", "от": "dan", "так": "shunday / shu tarzda",
    "о": "haqida", "для": "uchun", "ты": "sen", "же": "esa (yordamchi)",
    "все": "hamma / barcha", "тот": "u (uzoq)", "мочь": "qila olish / -a olmoq",
    "вы": "siz / sizlar", "человек": "odam", "такой": "bunday", "его": "uning",
    "сказать": "aytmoq", "только": "faqat", "или": "yoki", "еще": "yana / hali",
    "бы": "bo'lar edi (shart)", "себя": "o'zini", "один": "bir / yolg'iz",
    "уже": "allaqachon", "до": "gacha / oldin", "время": "vaqt", "если": "agar",
    "сам": "o'zi", "когда": "qachon", "другой": "boshqa", "вот": "mana / ana",
    "говорить": "gapirmoq", "день": "kun", "где": "qayerda", "можно": "mumkin",
    "нет": "yo'q", "да": "ha", "очень": "juda", "хорошо": "yaxshi",
    "здесь": "bu yerda", "там": "u yerda", "сейчас": "hozir", "потом": "keyin",
    "большой": "katta", "маленький": "kichik", "новый": "yangi", "старый": "eski",
    "русский": "rus", "язык": "til", "слово": "so'z", "дом": "uy", "работа": "ish",
    "жизнь": "hayot", "страна": "mamlakat", "город": "shahar", "вода": "suv",
    "еда": "ovqat", "деньги": "pul", "школа": "maktab", "книга": "kitob",
    "мама": "ona", "папа": "ota", "друг": "do'st", "любить": "sevmoq",
    "знать": "bilmoq", "думать": "o'ylamoq", "видеть": "ko'rmoq", "слышать": "eshitmoq",
    "идти": "bormoq", "делать": "qilmoq", "хотеть": "xohlamoq", "иметь": "ega bo'lmoq",
    "давать": "bermoq", "брать": "olmoq", "понимать": "tushunmoq", "учить": "o'rgatmoq / o'rganmoq",
    "читать": "o'qimoq", "писать": "yozmoq", "говорить": "gapirmoq", "спрашивать": "so'ramoq",
    "отвечать": "javob bermoq", "жить": "yashamoq", "стоять": "turmoq", "сидеть": "o'tirmoq",
    "стол": "stol", "окно": "deraza", "дверь": "eshik", "улица": "ko'cha",
    "машина": "mashina", "телефон": "telefon", "интернет": "internet",
    "утро": "ertalab", "вечер": "kechqurun", "ночь": "tun", "неделя": "hafta",
    "месяц": "oy", "сегодня": "bugun", "завтра": "ertaga", "вчера": "kecha",
    "вопрос": "savol", "ответ": "javob", "проблема": "muammo", "решение": "yechim",
    "начинать": "boshlamoq", "кончать": "tugatmoq", "помогать": "yordam bermoq",
    "искать": "izlamoq", "находить": "topmoq", "терять": "yo'qotmoq",
    "покупать": "sotib olmoq", "продавать": "sotmoq", "цена": "narx",
    "магазин": "do'kon", "ресторан": "restoran", "кофе": "kofe", "чай": "choy",
    "хлеб": "non", "молоко": "sut", "мясо": "go'sht", "рыба": "baliq",
    "красный": "qizil", "синий": "ko'k", "белый": "oq", "черный": "qora",
    "зеленый": "yashil", "желтый": "sariq", "горячий": "issiq", "холодный": "sovuq",
    "быстрый": "tez", "медленный": "sekin", "легкий": "engil", "тяжелый": "og'ir",
    "красивый": "chiroyli", "интересный": "qiziqarli", "важный": "muhim",
    "простой": "oddiy", "сложный": "murakkab", "правильный": "to'g'ri",
    "молодой": "yosh", "старый": "qari / eski", "богатый": "boy", "бедный": "kambag'al",
    "счастливый": "baxtli", "грустный": "xafa", "больной": "kasal", "здоровый": "sog'lom",
    "рука": "qo'l", "нога": "oyoq", "голова": "bosh", "глаз": "ko'z",
    "ухо": "quloq", "рот": "og'iz", "сердце": "yurak", "мозг": "miya",
    "солнце": "quyosh", "луна": "oy (sayyora)", "звезда": "yulduz", "небо": "osmon",
    "море": "dengiz", "река": "daryo", "гора": "tog'", "лес": "o'rmon",
    "собака": "it", "кошка": "mushuk", "птица": "qush", "цветок": "gul",
    "война": "urush", "мир": "tinchlik / dunyo", "правительство": "hukumat",
    "президент": "prezident", "закон": "qonun", "суд": "sud",
    "компьютер": "kompyuter", "программа": "dastur", "фильм": "film",
    "музыка": "musiqa", "игра": "o'yin", "спорт": "sport", "футбол": "futbol",
    "путешествие": "sayohat", "отдых": "dam olish", "отпуск": "ta'til",
    "больница": "shifoxona", "врач": "shifokor", "лекарство": "dori",
    "университет": "universitet", "студент": "talaba", "учитель": "o'qituvchi",
    "урок": "dars", "экзамен": "imtihon", "диплом": "diplom",
    "номер": "raqam", "адрес": "manzil", "письмо": "xat", "сообщение": "xabar",
    "новость": "yangilik", "газета": "gazeta", "журнал": "jurnal",
    "компания": "kompaniya", "офис": "ofis", "директор": "direktor",
    "клиент": "mijoz", "заказ": "buyurtma", "услуга": "xizmat",
    "качество": "sifat (quality)", "количество": "miqdor", "размер": "o'lcham",
    "уровень": "daraja", "результат": "natija", "цель": "maqsad",
    "план": "reja", "идея": "g'oya", "мнение": "fikr", "пример": "misol",
    "причина": "sabab", "следствие": "oqibat", "условие": "shart",
    "возможность": "imkoniyat", "необходимость": "zarurat", "обязанность": "majburiyat",
    "свобода": "erkinlik", "ответственность": "mas'uliyat", "уважение": "hurmat",
    "доверие": "ishonch", "обещание": "va'da", "ошибка": "xato",
    "успех": "muvaffaqiyat", "неудача": "muvaffaqiyatsizlik", "опыт": "tajriba",
    "знание": "bilim", "наука": "fan", "технология": "texnologiya",
    "информация": "ma'lumot", "данные": "ma'lumotlar", "система": "tizim",
    "процесс": "jarayon", "метод": "usul", "способ": "usul / yo'l",
    "ситуация": "vaziyat", "случай": "holat", "событие": "voqea",
    "история": "tarix", "культура": "madaniyat", "традиция": "an'ana",
    "праздник": "bayram", "подарок": "sovg'a", "сюрприз": "syurpriz",
    "погода": "ob-havo", "дождь": "yomg'ir", "снег": "qor", "ветер": "shamol",
    "температура": "harorat", "сезон": "fasl", "весна": "bahor", "лето": "yoz",
    "осень": "kuz", "зима": "qish",
}


def download_csv():
    if CSV_LOCAL.exists() and CSV_LOCAL.stat().st_size > 100000:
        return
    print("Downloading RNC frequency list...")
    urllib.request.urlretrieve(CSV_URL, CSV_LOCAL)


def classify_cat(lemma: str, pos: str) -> str:
    base = POS_CAT.get(pos, "world")
    if pos in ("s", "a", "v"):
        low = lemma.lower()
        for cat, keys in TOPIC_KEYWORDS.items():
            if any(k in low for k in keys):
                return cat
    return base


def make_example(lemma: str, pos: str) -> tuple[str, str]:
    pos_label = POS_UZ.get(pos, "so'z")
    if pos == "v":
        return (f"Я хочу {lemma}.", f"'{lemma}' — fe'l. Jumla: men ... xohlayman.")
    if pos == "s":
        return (f"Это слово — {lemma}.", f"'{lemma}' — ot. Kundalik rus tilida tez-tez ishlatiladi.")
    if pos == "a":
        return (f"Это очень {lemma}.", f"'{lemma}' — sifat. Narsa yoki odamni tavsiflaydi.")
    if pos == "pr":
        return (f"Книга лежит {lemma} столе.", f"'{lemma}' — predlog. Joy yoki vaqtni bog'laydi.")
    if pos == "conj":
        return (f"Я учу русский, {lemma} это интересно.", f"'{lemma}' — bog'lovchi so'z. Gaplarni bog'laydi.")
    if pos == "spro":
        return (f"{lemma.capitalize()} здесь.", f"'{lemma}' — olmoshi. O'rniga ot qo'yiladi.")
    if pos == "apro":
        return (f"{lemma.capitalize()} дом большой.", f"'{lemma}' — ko'rsatkich olmoshi.")
    if pos in ("adv", "advpro"):
        return (f"Он говорит {lemma}.", f"'{lemma}' — ravish. Fe'l yoki sifatni tushuntiradi.")
    if pos == "part":
        return (f"Я {lemma} знаю ответ.", f"'{lemma}' — yordamchi so'z. Ma'noni o'zgartiradi.")
    return (
        f"Слово «{lemma}» часто встречается в русском языке.",
        f"«{lemma}» — {pos_label}. Eng ko'p ishlatiladigan 3000 so'zdan biri."
    )


def translate_batch(words: list[str]) -> dict[str, str]:
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "deep-translator", "-q"])
        from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source="ru", target="uz")
    result = {}
    batch_size = 50
    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]
        need = [w for w in batch if w not in MANUAL_UZ]
        if not need:
            continue
        text = "\n".join(need)
        try:
            translated = translator.translate(text)
            lines = translated.split("\n") if translated else []
            for j, w in enumerate(need):
                if j < len(lines) and lines[j].strip():
                    result[w] = lines[j].strip()
        except Exception as e:
            print(f"  Batch {i//batch_size + 1} error: {e}")
            time.sleep(2)
            try:
                for w in need:
                    result[w] = translator.translate(w)
                    time.sleep(0.15)
            except Exception:
                pass
        time.sleep(0.5)
        print(f"  Translated {min(i + batch_size, len(words))}/{len(words)}")
    return result


def load_words():
    download_csv()
    rows = []
    with open(CSV_LOCAL, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or i == 0:
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            rank = int(parts[0])
            freq = float(parts[-4])
            pos = parts[-5]
            lemma = " ".join(parts[1:-5])
            if not lemma or re.match(r"^[\d\W]+$", lemma):
                continue
            rows.append({"lemma": lemma, "pos": pos, "freq": freq})
            if len(rows) >= TOTAL:
                break
    return rows


def build():
    print("Loading frequency data...")
    rows = load_words()
    print(f"Loaded {len(rows)} lemmas")

    lemmas = [r["lemma"] for r in rows]
    missing = [l for l in lemmas if l not in MANUAL_UZ]
    print(f"Translating {len(missing)} words to Uzbek...")
    auto_uz = translate_batch(missing)

    data = []
    for i, row in enumerate(rows):
        rank = i + 1
        level = (rank - 1) // WORDS_PER_LEVEL + 1
        lemma = row["lemma"]
        pos = row["pos"]
        cat = classify_cat(lemma, pos)
        uz = MANUAL_UZ.get(lemma) or auto_uz.get(lemma) or lemma
        ex, ex_uz = make_example(lemma, pos)
        data.append({
            "w": lemma,
            "uz": uz,
            "cat": cat,
            "pos": pos,
            "ex": ex,
            "exUz": ex_uz,
            "source": "RNC Frequency",
            "id": rank,
            "rank": rank,
            "level": level,
        })

    js = "window.VOCABULARY_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    OUT.write_text(js, encoding="utf-8")
    print(f"Written {len(data)} words to {OUT}")
    print(f"Levels: 1-{LEVELS}, {WORDS_PER_LEVEL} words/level")


if __name__ == "__main__":
    build()
