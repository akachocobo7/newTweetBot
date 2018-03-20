#!/usr/bin/env python
# -*- coding: utf-8 -*-

from janome.tokenizer import Tokenizer
import json, config
from requests_oauthlib import OAuth1Session
import unicodedata
import string
import re
import random
from collections import defaultdict

def tweet_practice():
    CK = config.CONSUMER_KEY
    CS = config.CONSUMER_SECRET
    AT = config.ACCESS_TOKEN
    ATS = config.ACCESS_TOKEN_SECRET
    twitter = OAuth1Session(CK, CS, AT, ATS)

    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"

    params = {'count' : 300}
    req = twitter.get(url, params = params)

    count = 0
    texts = ""
    if req.status_code == 200:
        timeline = json.loads(req.text)
        for tweet in timeline:
            tweet = tweet['text']

            tweet = re.sub('#.*', "", tweet)    # ハッシュタグは削除
            tweet = re.sub('http.*', "", tweet) # urlは削除
            tweet = re.sub('@.*\\s', "", tweet)  # @hoge は削除
            if "RT" in tweet:   #RTは無視
                pass
            else:
                count += 1
                # print(tweet)
                if(unicode(tweet[-1:]) != u'。'):
                    tweet += u'。'
                # print(tweet)
                texts += tweet
    else:
        print(("ERROR: %d" % req.status_code))

    print((str(count) + "tweets"))
    return texts

class sentence_generation(object):
    """文章を生成する"""

    BEGIN = u"__BEGIN_SENTENCE__"
    END = u"__END_SENTENCE__"

    def __init__(self, text):
        # テキストをいい感じにする
        if isinstance(text, str):
            text = text.decode("utf-8")
        # 半角記号を削除
        half_symbol = re.compile("[!-/:-@[-`{-~]")
        text = half_symbol.sub("", text)

        self.text = text

        self.t = Tokenizer(wakati=True)

        # 生成する文章の数を指定
        self.sentence_num = 5
        # 生成する文章の文字数の大ざっぱな上限
        self.stop_length = 110
    
    def make_triplet_freqs(self):
        """
        形態素解析と3つ組の出現回数を数える。
        keyが3つ組で値がその出現回数 の辞書を返す。
        """
        # 長い文章をセンテンス毎に分割
        sentences = self.division(self.text)

        # 3つ組の出現回数
        triplet_freqs = defaultdict(int)

        # センテンス毎に3つ組にする
        for sentence in sentences:
            # 形態素解析
            morphemes = self.morphological_analysis(sentence)
            # 3つ組をつくる
            triplets = self.make_triplet(morphemes)
            # 出現回数を加算
            for (triplet, n) in triplets.items():
                triplet_freqs[triplet] += n

        return triplet_freqs
    
    def division(self, text):
        """
        「。」や改行などで区切られた長い文章を一文ずつに分ける。
        一文ずつの配列を返す。
        """
        # 改行文字以外の分割文字（正規表現表記）
        delimiter = re.compile(u"。|．|\\.")

        # 全ての分割文字を改行文字に置換（splitしたときに「。」などの情報を無くさないため）
        text = delimiter.sub(u"\1\n", text)

        # 改行文字で分割
        sentences = text.splitlines()

        # 前後の空白文字を削除
        sentences = [sentence.strip() for sentence in sentences]

        return sentences
    
    def morphological_analysis(self, sentence):
        """
        一文を形態素解析する。
        形態素で分割された配列を返す。
        """
        morphemes = []
        # sentence = sentence.encode("utf-8")
        node = self.t.tokenize(sentence)
        for word in node:
            # 空白を削除
            morpheme = word.strip()
            morphemes.append(morpheme)

        return morphemes
    
    def make_triplet(self, morphemes):
        """
        形態素解析で分割された配列を、形態素毎に3つ組にしてその出現回数を数える。
        keyが3つ組で値がその出現回数 の辞書を返す。
        """

        # 3つ組をつくれない場合は終える
        if len(morphemes) < 3:
            return {}

        # 出現回数の辞書
        triplet_freqs = defaultdict(int)

        # 繰り返し
        for i in xrange(len(morphemes)-2):
            triplet = tuple(morphemes[i:i+3])
            triplet_freqs[triplet] += 1

        # beginを追加
        triplet = (sentence_generation.BEGIN, morphemes[0], morphemes[1])
        triplet_freqs[triplet] = 1

        # endを追加
        triplet = (morphemes[-2], morphemes[-1], sentence_generation.END)
        triplet_freqs[triplet] = 1

        return triplet_freqs
    
    """
    def show(self, triplet_freqs):
        '''
        3つ組毎の出現回数を出力する。
        '''
        for triplet in triplet_freqs:
            print "|".join(triplet), "\t", triplet_freqs[triplet]
    """

    
    def generate(self):
        """
        文章を生成し、その文章を返す。
        """

        # 最終的にできる文章
        generated_text = u""

        triplet_freqs = self.make_triplet_freqs()

        # 指定の数だけ作成する
        for _ in xrange(self.sentence_num):
            text = self.generate_sentence(triplet_freqs)
            # 文字数上限を超えないなら追加
            if(len(generated_text) + len(text) <= self.stop_length):
                generated_text += text

        return generated_text

    def generate_sentence(self, triplet_freqs):
        """
        ランダムに一文を生成し、その文章を返す。
        """
        # 生成文章のリスト
        morphemes = []

        # はじまりを取得
        first_triplet = self.get_first_triplet(triplet_freqs)
        morphemes.append(first_triplet[1])
        morphemes.append(first_triplet[2])

        # 文章を紡いでいく
        while morphemes[-1] != sentence_generation.END:
            prefix1 = morphemes[-2]
            prefix2 = morphemes[-1]
            triplet = self.get_triplet(triplet_freqs, prefix1, prefix2)
            morphemes.append(triplet[2])

        # 連結
        result = "".join(morphemes[:-1])

        return result

    def get_chain(self, triplet_freqs, prefixes):
        """
        チェーンの情報をtriplet_freqsから取得する。
        チェーンの情報の配列を返す。
        """

        # 結果
        result = []

        for triplet in triplet_freqs:
            dic = {}
            dic['prefix1'] = triplet[0]
            dic['prefix2'] = triplet[1]
            dic['suffix'] = triplet[2]
            dic['freq'] = triplet_freqs[triplet]
            result.append(dic)

        return result

    def get_first_triplet(self, triplet_freqs):
        """
        文章のはじまりの3つ組をランダムに取得する。
        文章のはじまりの3つ組のタプルを返す。
        """
        # BEGINをprefix1としてチェーンを取得
        prefixes = (sentence_generation.BEGIN,)

        # チェーン情報を取得
        chains = self.get_chain(triplet_freqs, prefixes)

        # 取得したチェーンから、確率で1つ選ぶ
        triplet = self.get_probable_triplet(chains)

        return (triplet["prefix1"], triplet["prefix2"], triplet["suffix"])

    def get_triplet(self, triplet_freqs, prefix1, prefix2):
        """
        prefix1とprefix2からsuffixをランダムに取得する。
        3つ組のタプルを返す。
        """
        # BEGINをprefix1としてチェーンを取得
        prefixes = (prefix1, prefix2)

        # チェーン情報を取得
        chains = self.get_chain(triplet_freqs, prefixes)

        # 取得したチェーンから、確率で1つ選ぶ
        triplet = self.get_probable_triplet(chains)

        return (triplet["prefix1"], triplet["prefix2"], triplet["suffix"])

    def get_probable_triplet(self, chains):
        """
        チェーンの配列の中から確率で1つ選ぶ。
        確率で選んだ3つ組を返す。
        """
        # 確率配列
        probability = []

        # 確率に合うように、インデックスを入れる
        for (index, chain) in enumerate(chains):
            for _ in xrange(chain["freq"]):
                probability.append(index)

        # ランダムに1つを選ぶ
        chain_index = random.choice(probability)

        return chains[chain_index]


    def generate_text(self):
        """
        文章を生成する。
        生成した文章を返す。
        """
        # triplet_freqs = self.make_triplet_freqs()
        # self.show(triplet_freqs)

        if(self.text != ""):
            text = self.generate()
            print (text.encode('utf_8'))
            return text
        else:
            return {}
    

if __name__ == '__main__':
    text = tweet_practice()
    '''
    f = open('test.txt')
    text = f.read()
    f.close()
    '''
    a = re.compile("[!-/:-@[-`{-~]")
    text = re.sub(a, "", text)
    generate = sentence_generation(text)
    generate.generate_text()