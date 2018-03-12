#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask+TweepyによるTwitter連携アプリのサンプル．
連携アプリ認証を行いタイムラインを表示する．
"""
import os
import logging
import tweepy
from flask import Flask, session, redirect, render_template, request

# Consumer Key
CONSUMER_KEY = os.environ['CONSUMER_KEY']
# Consumer Secret
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
# Callback URL (認証後リダイレクトされるURL)
# CALLBACK_URL = 'https://flask-tweepy.herokuapp.com/'  # Heroku上
CALLBACK_URL = 'http://localhost:5000/' # ローカル環境

logging.warn('app start!')

# Flask の起動
app = Flask(__name__)
# flask の session を使うにはkeyを設定する必要がある．
app.secret_key = os.environ['SECRET_KEY']

@app.route('/')
def index():
    """ root ページの表示 """
    # 認証できているなら auth 、できていないなら False
    auth = authentication()
    # 連携アプリ認証済みなら user の timeline を取得
    timeline = user_timeline(auth)

    test = "やっていき"

    # templates/index.html を使ってレンダリング．
    return render_template('index.html', auth=auth, timeline=timeline, tweet=test)


@app.route('/twitter_auth', methods=['GET'])
def twitter_auth():
    """ 連携アプリ認証用URLにリダイレクト """
    # tweepy でアプリのOAuth認証を行う
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, CALLBACK_URL)

    try:
        # 連携アプリ認証用の URL を取得
        redirect_url = auth.get_authorization_url()
        # 認証後に必要な request_token を session に保存
        session['request_token'] = auth.request_token
    except tweepy.TweepError, e:
        logging.error(str(e))

    # リダイレクト
    return redirect(redirect_url)

# 認証できているなら auth を返し、できていないなら False を返す
def authentication():
    # request_token と oauth_verifier のチェック
    token = session.pop('request_token', None)
    verifier = request.args.get('oauth_verifier')
    if token is None or verifier is None:
        return False  # 未認証ならFalseを返す

    # tweepy でアプリのOAuth認証を行う
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, CALLBACK_URL)

    # Access token, Access token secret を取得．
    auth.request_token = token
    try:
        auth.get_access_token(verifier)
    except tweepy.TweepError, e:
        logging.error(str(e))
        return {}
    
    return auth
    
def user_timeline(auth):
    if(auth != False):
        # tweepy で Twitter API にアクセス
        api = tweepy.API(auth)

        # user の timeline 内のツイートのリストを最大100件取得して返す
        return api.user_timeline(count=100)
    else:
        return {}