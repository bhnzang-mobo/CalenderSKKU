from __future__ import print_function
import datetime
import os.path
from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from bs4 import BeautifulSoup
import pandas as pd
import json
import urllib
import re



token_path = '.json/token.json'
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def creatSKKUEvents() :
    cal_json = urllib.request.urlopen("https://cs.skku.edu/rest/calendar").read()
    cal=json.loads(cal_json.decode('utf-8'))
    result = pd.DataFrame(cal['result'])
    return result

def makeSKKUEvent(result):
    events = []
    recent_start = 0
    recent_end = 0
    start_leap =False
    end_leap = False
    for entry in result.iterrows():
        event={}
        summary = entry[1]["contents"]

        startyear = entry[1]["createdAt"].split('-')[0]
        endyear = startyear
        startdate = entry[1]["startdate"].split('(')[0]
        startdate_month = startdate.split('.')[0]
        startdate_day = startdate.split('.')[1]
        enddate = entry[1]["enddate"].split('(')[0]
        enddate_month = enddate.split('.')[0]
        enddate_day = enddate.split('.')[1]
        #해가 넘어가는 경우를 다룹니다
        if (start_leap and int(startdate_month)<=4):
            startyear = str(int(startyear) + 1)
        else:
            if (recent_start < int(startdate_month)):
                recent_start = int(startdate_month)
            elif (recent_start > int(startdate_month) and int(startdate_month)== 1 ):
                start_leap=True
                startyear = str(int(startyear) + 1)
        if(end_leap and int(enddate_month)<=4):
            endyear = str(int(endyear) + 1)
        else :
            if (recent_end < int(enddate_month)):
                recent_end = int(enddate_month)
            elif (recent_end > int(enddate_month) and int(enddate_month) == 1):
                end_leap=True
                endyear = str(int(endyear) + 1)

        event['summary'] = summary
        event['start'] = {'date': startyear + '-' + startdate_month + '-' + startdate_day}
        event['end'] = {'date': endyear + '-' + enddate_month + '-' + enddate_day}
        events.append(event)
    print(events)
    return events

def skku_eventInsert(service,event,calId="primary"):
    print('Trying: %s' % event)
    res = service.events().insert(calendarId=calId, body=event).execute()
    print('Success! : %s' % event)

def skku_calInsert(service,summary = "calendarSummary"): #캘린더를 생성하고 캘린더 아이디를 반환합니다.
    calendar = {
        'summary': summary,
        'timeZone': 'Asia/Seoul'
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    print("캘린더 생성 성공 : ",created_calendar['id'])
    return created_calendar['id']

def skku_calDelete(service,cal_id):
    flag = True
    A = cal_id

    if(A!="" and A !="0"):
    #Delete 시행
        print("삭제를 수행합니다.")
        try :
            service.calendars().delete(calendarId=A).execute()
        except errors.HttpError as e:
            print(e.error_details[0]['reason']," : 삭제할 대상이 없습니다.")
            return -1
        return 0
    else :
        print("삭제명령을 취소합니다.")
        return 1

def skku_calList(service): #캘린더 목록을 반환합니다. 요약과 아이디를 출력.
    page_token = None
    ret=[]
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            ret.append(calendar_list_entry)
            print(calendar_list_entry['summary'], ":", calendar_list_entry['id'])
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    return ret

def skku_recent(service,numOfResult=10):
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='bv9mbut6k7j1evvovn37bhr5nk@group.calendar.google.com',
                                          timeMin=now,
                                          maxResults=numOfResult,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event)

def skku_init():
    global service
    creds = None

    if os.path.exists(token_path):#배포시 플라스크로 세션에 토큰 존재 여부로 변경
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:  # 토큰이 존재하나 유효하지 않는다면
        if creds and creds.expired and creds.refresh_token:  # 토큰의 만료가 원인이라면
            print("토큰이 만료됐습니다.")
            creds.refresh(Request())
        else:  # 토큰이 존재하지 않는다면-> 발급
            print("토큰을 재발급 합니다.")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=5500)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    # 서비스 시작
    service = build('calendar', 'v3', credentials=creds)


def testRun(service):
    skku_recent(service)
    """event = { #이벤트 예시
      'summary': 'Google I/O 2015',
      'location': '800 Howard St., San Francisco, CA 94103',
      'description': 'A chance to hear more about Google\'s developer products.',
      'start': {
        'dateTime': '2015-05-28T09:00:00-07:00',
        'timeZone': 'America/Los_Angeles',
      },
      'end': {
        'dateTime': '2015-05-28T17:00:00-07:00',
        'timeZone': 'America/Los_Angeles',
      },
      'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=2'
      ],
      'attendees': [
        {'email': 'lpage@example.com'},
        {'email': 'sbrin@example.com'},
      ],
      'reminders': {
        'useDefault': False,
        'overrides': [
          {'method': 'email', 'minutes': 24 * 60},
          {'method': 'popup', 'minutes': 10},
        ],
      },
    }"""
    # 캘린더 리스트 가져오기

    """ 캘린더 삽입"""
    skku_calInsert(service,"test")
    skku_calList(service)
    skku_calDelete(service)
