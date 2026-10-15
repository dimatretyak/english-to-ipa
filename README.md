# English to IPA Converter

**[Open the converter →](https://dimatretyak.github.io/english-to-ipa/)**

Type English text and get its IPA phonetic transcription with stress marks
(General American). Also shows every pronunciation of a word, whether it takes
*a* or *an*, and common homophones. Static page: the dictionary is downloaded
once and everything runs in the browser.

Made by the author of [Word of the Day](https://wordofdayapp.com/?utm_source=github&utm_medium=referral&utm_campaign=english_to_ipa&utm_content=readme),
a free word of the day with meaning, examples and flashcard practice.

## How it works

`scripts/build.py` turns the [CMU Pronouncing Dictionary](https://github.com/cmusphinx/cmudict)
(ARPAbet) into `data/dict.json` (IPA). Stress marks go before the syllable
onset (longest legal English onset); `r` is written as in learner dictionaries,
not `ɹ`. Homophone groups are limited to common words (wordfreq top 30,000 that
are lowercase in `/usr/share/dict/words`).

Rebuild:

```sh
python3 -m venv /tmp/wf && /tmp/wf/bin/pip install wordfreq
/tmp/wf/bin/python -c "import wordfreq; print('\n'.join(wordfreq.top_n_list('en', 30000)))" > /tmp/top30k.txt
curl -sLo /tmp/cmudict.dict https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict
python3 scripts/build.py /tmp/cmudict.dict /tmp/top30k.txt
```

## License

Code: MIT. Pronunciations: CMU Pronouncing Dictionary, © Carnegie Mellon
University, BSD-style license (`data/LICENSE-CMUDICT`). The homophone groups in
`data/dict.json` are derived with [wordfreq](https://github.com/rspeer/wordfreq)
data, CC BY-SA 4.0.
