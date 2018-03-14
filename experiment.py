# -*- coding: utf-8 -*-

import json, config, re
from requests_oauthlib import OAuth1Session

CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET
twitter = OAuth1Session(CK, CS, AT, ATS)

url = "https://api.twitter.com/1.1/statuses/user_timeline.json"

params ={'count' : 110}
req = twitter.get(url, params = params)

count = 0
if req.status_code == 200:
    timeline = json.loads(req.text)
    for tweet in timeline:
        tweet = tweet['text']

        tweet = re.sub('#.*', "", tweet)    # ハッシュタグは削除
        tweet = re.sub('http.*', "", tweet) # urlは削除
        tweet = re.sub('@.*\s', "", tweet)  # @hoge は削除
        if "RT" in tweet:   #RTは無視
            pass
        else:
            count += 1
            print(tweet)
else:
    print("ERROR: %d" % req.status_code)

print(str(count) + "tweets")