"""Patch example sentences in vocab-data.js without re-translating."""
import json
import re
from pathlib import Path

OUT = Path(__file__).parent / "vocab-data.js"

POS_UZ = {
    "conj": "bog'lovchi", "part": "yordamchi so'z", "pr": "predlog",
    "spro": "olmoshi", "apro": "ko'rsatkich olmoshi", "adv": "ravish",
    "advpro": "ravish olmoshi", "v": "fe'l", "s": "ot", "a": "sifat", "num": "son",
}

def make_example(lemma: str, pos: str) -> tuple[str, str]:
    pos_label = POS_UZ.get(pos, "so'z")
    if pos == "v":
        return (
            f"Я хочу {lemma}.",
            f"'{lemma}' — fe'l. Jumla: men ... xohlayman."
        )
    if pos == "s":
        return (
            f"Это слово — {lemma}.",
            f"'{lemma}' — ot. Kundalik rus tilida tez-tez ishlatiladi."
        )
    if pos == "a":
        return (
            f"Это очень {lemma}.",
            f"'{lemma}' — sifat. Narsa yoki odamni tavsiflaydi."
        )
    if pos == "pr":
        return (
            f"Книга лежит {lemma} столе.",
            f"'{lemma}' — predlog. Joy yoki vaqtni bog'laydi."
        )
    if pos == "conj":
        return (
            f"Я учу русский, {lemma} это интересно.",
            f"'{lemma}' — bog'lovchi so'z. Gaplarni bog'laydi."
        )
    if pos == "spro":
        return (
            f"{lemma.capitalize()} здесь.",
            f"'{lemma}' — olmoshi. O'rniga ot qo'yiladi."
        )
    if pos == "apro":
        return (
            f"{lemma.capitalize()} дом большой.",
            f"'{lemma}' — ko'rsatkich olmoshi."
        )
    if pos == "adv" or pos == "advpro":
        return (
            f"Он говорит {lemma}.",
            f"'{lemma}' — ravish. Fe'l yoki sifatni tushuntiradi."
        )
    if pos == "part":
        return (
            f"Я {lemma} знаю ответ.",
            f"'{lemma}' — yordamchi so'z. Ma'noni o'zgartiradi."
        )
    return (
        f"Слово «{lemma}» часто встречается в русском языке.",
        f"«{lemma}» — {pos_label}. Eng ko'p ishlatiladigan 3000 so'zdan biri."
    )


def pos_from_ex_uz(ex_uz: str) -> str:
    if "fe'l" in ex_uz: return "v"
    if "predlog" in ex_uz: return "pr"
    if "bog'lovchi" in ex_uz: return "conj"
    if "olmoshi" in ex_uz and "ko'rsatkich" not in ex_uz: return "spro"
    if "ko'rsatkich" in ex_uz: return "apro"
    if "ravish" in ex_uz: return "adv"
    if "yordamchi" in ex_uz: return "part"
    if "sifat" in ex_uz: return "a"
    if "ot" in ex_uz: return "s"
    return "s"


def main():
    content = OUT.read_text(encoding="utf-8")
    m = re.match(r"window\.VOCABULARY_DATA\s*=\s*(\[.*\])\s*;?\s*$", content, re.DOTALL)
    if not m:
        raise SystemExit("Could not parse vocab-data.js")
    data = json.loads(m.group(1))
    for item in data:
        pos = item.get("pos") or pos_from_ex_uz(item.get("exUz", ""))
        ex, ex_uz = make_example(item["w"], pos)
        item["ex"] = ex
        item["exUz"] = ex_uz
        item["pos"] = pos
    OUT.write_text("window.VOCABULARY_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"Patched {len(data)} entries")


if __name__ == "__main__":
    main()
