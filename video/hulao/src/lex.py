# -*- coding: utf-8 -*-
"""把自定义读音注册到 jieba 分词与 pypinyin 词库（TTS 前端逐词调用 pypinyin）。"""
def register(lex):
    import jieba
    from pypinyin import load_phrases_dict
    d = {}
    for w, py in lex.items():
        jieba.add_word(w, freq=2000000)
        d[w] = [[p] for p in py.split()]
        assert len(d[w]) == len(w), (w, py)
    load_phrases_dict(d)
