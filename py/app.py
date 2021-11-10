"""from flask import Flask, render_template, request, session
from authlib.integrations.flask_client import OAuth
from main import *

app = Flask(__name__)
app.secret_key = "40312662"
service=""

# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="664305802864-7uf2n3lk2bl17m91arcd3pmcrc1eh96q.apps.googleusercontent.com",
    client_secret="uOMCphLQAJreAhC9FZCoEMAq",
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)



@app.route("/")
def hello(num=None):
    skku_init()
    skku_recent()
    return render_template("layout.html")

@app.route("/delete", methods = ["POST","GET"])
def cal_del(num=None):
    #skkU_calInsert("성균관대 학사일정_모보현")
    cal_list = skku_calList()
    return render_template("delete.html",cal_list=cal_list)

@app.route("/makeEvents", methods = ["POST","GET"])
def skkuEventInsert(num=None):
    res = 2
    cal_id=skku_calInsert("성균관대 2021 학사일정")
    result = creatSKKUEvents()
    events = makeSKKUEvent(result)
    for ent in events:
        skku_eventInsert(ent,cal_id)
    return render_template("result.html",res=res)


@app.route("/result", methods = ["POST","GET"])
def cal_res(num=None):

    cal_id = request.form.get("cal_id")
    res = skku_calDelete(cal_id)
    return render_template("result.html",res=res)

@app.route("/calenderList", methods=['POST','GET'])
def skku(num=2):
    cal_list = skku_calList()
    return render_template("index.html",cal_list=cal_list)

if __name__ == '__main__':
    skku_init()
    app.run(host='0.0.0.0', port=5500)
"""

# -*- coding: utf-8 -*-

import os
import flask
from flask import send_from_directory
import requests
from main import *

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "credentials.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'
service = None
app = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See https://flask.palletsprojects.com/quickstart/#sessions.
app.secret_key = 'lqelj2l@ldlp%d-!ksjli'

"""@app.route('/<path:path>')
def path(path=None):
    return send_from_directory('',path=path)
"""
def getService():
    global service


@app.route("/showEvents", methods = ["POST","GET"])
def skkuEventInsert(num=None):
    global service
    res = 2

    result = creatSKKUEvents()
    events = None
    if 'events' in flask.session:
        events = flask.session['events']
    else:
        events = makeSKKUEvent(result)
    eventIdx = flask.request.form.getlist("idx")
    if(eventIdx):
        for i in reversed(eventIdx):
            del events[int(i)]

    flask.session['url']='/showEvents'
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')
    flask.session['events']=events
    flask.session['url'] = '/'
    return flask.render_template("listEvents.html",events=list(enumerate(events)))


@app.route("/insertEvents", methods = ["POST","GET"])
def insertEvent():
    global service
    if not service:
        credentials = google.oauth2.credentials.Credentials(
            **flask.session['credentials'])
        service = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)
    cal_id = skku_calInsert(service, "성균관대 2021 학사일정")

    events = flask.session['events']
    for ent in events:
        skku_eventInsert(service,ent,cal_id)
    del flask.session['events']
    flask.flash("등록이 모두 완료되었습니다.")
    return flask.redirect("/")

@app.route('/')
def index():
    flask.session['url']='/'
    return flask.render_template("home.html",session = flask.session)


@app.route('/index')
def test_api_request():
    global service
    flask.session['url']='/index'
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    #initialize Service
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    ret = skku_calList(service)
    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect("/")


@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)
    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    # initialize Service
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    print(flask.session)
    return flask.redirect(flask.session['url'])

@app.route('/reset')
def reset():
    print("삭제 시도")
    if 'events' in flask.session:
        print("삭제")
        del flask.session['events']
    return flask.redirect('/showEvents')

@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    if 'events' in flask.session:
        del flask.session['events']
    if 'url' in flask.session:
        return flask.redirect(flask.session['url'])
    return flask.redirect('/')


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run('localhost', 8080, debug=True)