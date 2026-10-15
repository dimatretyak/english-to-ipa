"""Build data/dict.json from CMUdict.

Usage: python3 scripts/build.py <cmudict.dict> <common-words.txt>

Output: {"w": {word: "ipa" or "ipa|ipa2"}, "h": [[homophone group], ...]}
Homophone groups only use words that are both in common-words.txt (one per
line) and lowercase in /usr/share/dict/words (Webster's 2nd, public domain),
plus contractions like "they're". That keeps names, possessives and rare
spellings from CMUdict out. common-words.txt is wordfreq's English top 30,000
(CC BY-SA 4.0):

    python3 -m venv /tmp/wf && /tmp/wf/bin/pip install wordfreq
    /tmp/wf/bin/python -c "import wordfreq; print('\\n'.join(wordfreq.top_n_list('en', 30000)))" > /tmp/top30k.txt
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

VOWELS = {
    "AA": "ɑ", "AE": "æ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ", "EH": "ɛ",
    "EY": "eɪ", "IH": "ɪ", "IY": "i", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
}
CONSONANTS = {
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ", "HH": "h",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ", "P": "p",
    "R": "r", "S": "s", "SH": "ʃ", "T": "t", "TH": "θ", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}
# Legal English onsets, used to put the stress mark before the syllable start.
ONSETS = {tuple(o.split()) for o in """
P R|P L|B R|B L|T R|D R|K R|K L|G R|G L|F R|F L|TH R|SH R|S P|S T|S K|S M|S N|S L|S W|S F
T W|D W|K W|G W|TH W|P Y|B Y|F Y|M Y|K Y|V Y|HH Y|N Y|L Y|S P R|S P L|S T R|S K R|S K W|S K Y|S P Y
""".replace("\n", "|").split("|") if o.strip()}


def to_ipa(phones):
    """ARPAbet phones (with stress digits) -> IPA with ˈ/ˌ before the stressed syllable."""
    out = []  # list of (ipa, is_vowel, stress, arpabet)
    for p in phones:
        base, stress = re.match(r"([A-Z]+)(\d?)$", p).groups()
        if base == "AH":
            ipa = "ʌ" if stress in "12" and stress else "ə"
        elif base == "ER":
            ipa = "ɝ" if stress in "12" and stress else "ɚ"
        elif base in VOWELS:
            ipa = VOWELS[base]
        else:
            out.append((CONSONANTS[base], False, "", base))
            continue
        out.append((ipa, True, stress, base))

    marks = {}  # index -> mark to insert before it
    prev_vowel = -1
    for i, (_, is_vowel, stress, _) in enumerate(out):
        if not is_vowel:
            continue
        if stress in ("1", "2"):
            cons = [o[3] for o in out[prev_vowel + 1:i]]
            start = i
            for n in range(len(cons), 0, -1):  # longest legal onset
                tail = tuple(cons[-n:])
                if n == 1 and tail[0] != "NG" or tail in ONSETS:
                    start = i - n
                    break
            if prev_vowel == -1:
                start = 0  # word-initial clusters always belong to the first syllable
            marks[start] = "ˈ" if stress == "1" else "ˌ"
        prev_vowel = i
    # One-syllable words get no stress mark, like most dictionaries.
    if sum(1 for o in out if o[1]) == 1:
        marks = {}
    return "".join(marks.get(i, "") + o[0] for i, o in enumerate(out))


def main():
    src = Path(sys.argv[1])
    web2 = {w for w in Path("/usr/share/dict/words").read_text().split() if w.islower()}
    contraction = re.compile(r"^(?:[a-z]+'(?:re|ll|ve|d|t|m)|(?:it|he|she|that|there|what|who|where|here|let)'s)$")
    # Single letters ("s", "k") make noise; "i" (eye, aye) is worth keeping.
    common = {
        w for w in Path(sys.argv[2]).read_text().split()
        if (len(w) > 1 or w == "i") and (w in web2 or contraction.match(w))
    }

    prons = defaultdict(list)
    for line in src.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        word, *phones = line.split()
        word = re.sub(r"\(\d+\)$", "", word)
        ipa = to_ipa(phones)
        if ipa not in prons[word]:
            prons[word].append(ipa)

    groups = defaultdict(set)
    for word, ipas in prons.items():
        if word in common:
            for ipa in ipas:
                # Weak forms with only ə/ɚ ("are" as /ɚ/) would match "or", "er".
                if re.search("[iɪeɛæɑɔoʊuʌɝa]", ipa):
                    groups[ipa].add(word)
    homophones = sorted(sorted(g) for g in groups.values() if len(g) > 1)

    out = {"w": {w: "|".join(v) for w, v in prons.items()}, "h": homophones}
    dest = Path(__file__).resolve().parent.parent / "data" / "dict.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"{len(prons)} words, {len(homophones)} homophone groups -> {dest}")


def demo():
    assert to_ipa("HH AH0 L OW1".split()) == "həˈloʊ"
    assert to_ipa("Y UW2 N AH0 V ER1 S AH0 T IY0".split()) == "ˌjunəˈvɝsəti"
    assert to_ipa("T AH0 M EY1 T OW2".split()) == "təˈmeɪˌtoʊ"
    assert to_ipa("DH EH1 R".split()) == "ðɛr"
    assert to_ipa("IH0 K S T R IY1 M".split()) == "ɪkˈstrim"  # S T R onset
    assert to_ipa("AE1 K T ER0".split()) == "ˈæktɚ"
    assert to_ipa("S T R EH1 NG K TH".split()) == "strɛŋkθ"


if __name__ == "__main__":
    demo()
    main()
