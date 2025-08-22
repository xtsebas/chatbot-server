# tools/build_words_from_freq.py
import os
import re

INPUT = "es_full.txt"   # archivo con "palabra frecuencia"
OUTPUT = os.path.join("..", "src", "mcp_server", "words.txt")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

patron_palabra = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$")

count_in = 0
count_out = 0

with open(INPUT, "r", encoding="utf-8") as fin, open(OUTPUT, "w", encoding="utf-8") as fout:
    for line in fin:
        count_in += 1
        line = line.strip()
        if not line:
            continue
        word = line.split(maxsplit=1)[0].lower()
        if not patron_palabra.match(word):
            continue
        # 👉 solo palabras de exactamente 5 letras
        if len(word) != 5:
            continue
        fout.write(word + "\n")
        count_out += 1

print(f"Líneas leídas: {count_in}")
print(f"Palabras escritas (5 letras): {count_out}")
print(f"Guardado en: {OUTPUT}")