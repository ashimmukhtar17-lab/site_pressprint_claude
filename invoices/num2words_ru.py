# Русские числительные для суммы в тенге (мужской/средний род для "тенге" не склоняется)

UNITS_M = ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
UNITS_F = ["", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
TEENS = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать",
         "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"]
TENS = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят",
        "восемьдесят", "девяносто"]
HUNDREDS = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот",
            "восемьсот", "девятьсот"]

SCALE = [
    ("", "", "", 1),                      # ед.
    ("тысяча", "тысячи", "тысяч", 2),      # жен. род
    ("миллион", "миллиона", "миллионов", 1),
    ("миллиард", "миллиарда", "миллиардов", 1),
]


def _plural_form(n, forms):
    n = n % 100
    if 11 <= n <= 19:
        return forms[2]
    n1 = n % 10
    if n1 == 1:
        return forms[0]
    if 2 <= n1 <= 4:
        return forms[1]
    return forms[2]


def _three_digits(n, feminine=False):
    words = []
    h = n // 100
    if h:
        words.append(HUNDREDS[h])
    n = n % 100
    if 10 <= n <= 19:
        words.append(TEENS[n - 10])
    else:
        t = n // 10
        u = n % 10
        if t:
            words.append(TENS[t])
        if u:
            words.append((UNITS_F if feminine else UNITS_M)[u])
    return words


def num2words_ru(n: int) -> str:
    if n == 0:
        return "ноль"
    chunks = []
    tmp = n
    parts = []
    while tmp > 0:
        parts.append(tmp % 1000)
        tmp //= 1000
    for idx in range(len(parts) - 1, -1, -1):
        val = parts[idx]
        if val == 0:
            continue
        feminine = idx == 1  # тысячи - женский род
        words = _three_digits(val, feminine=feminine)
        if idx > 0:
            one, few, many, _ = SCALE[idx]
            words.append(_plural_form(val, (one, few, many)))
        chunks.extend(words)
    return " ".join(chunks)


def sum_in_words_tenge(amount) -> str:
    tenge = int(amount)
    tiyn = round((amount - tenge) * 100)
    words = num2words_ru(tenge)
    return f"{words} тенге {tiyn:02d} тиын"


if __name__ == "__main__":
    print(sum_in_words_tenge(400000))
    print(sum_in_words_tenge(722000))
    print(sum_in_words_tenge(1))
    print(sum_in_words_tenge(21))
