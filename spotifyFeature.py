import pandas as pd
import numpy as np
import os
import requests
import time
import sys

import json

sys.setrecursionlimit(20000)

class spotifyTool:
    def __init__(self):
        self.ids=[]
        self.failList=[]
        self.failCount=0
        self.length  = 0

        self.time_short_sleep=0.01
        self.time_long_sleep=1
        self.outTxtPath = os.getcwd() + '\\resource\\ocr_result_txt'
        self.csv=pd.DataFrame(columns=['sid', 'name', 'artist'])
        self.spotify_token={}


    def read_song_List(self):
        # 텍스트 파일 저장 경로
        for root, dirs, files in os.walk(os.path.realpath(os.getcwd()) + '\\resource\\orc_ori_image'):
            for fname in files:
                fullName = os.path.join(root, fname)
                print(fullName)
                with open(fullName, 'r', newline='', encoding="utf-8") as f:
                    print(fname)
                    self.csv = pd.read_excel(fullName)
                    self.csv.columns = ['sid', 'name', 'artist']
        self.length  = len(self.csv)

    def get_access_token(self):
        client_id = '01493f9309da40a5879993e2d662148f'
        client_secret = '4a2dd73f6ceb458ab0aa67ae97548456'
        grant_type = 'client_credentials'

        # Request based on Client Credentials Flow from https://developer.spotify.com/web-api/authorization-guide/
        # Request body parameter: grant_type Value: Required. Set it to client_credentials
        body_params = {'grant_type': grant_type}

        url = 'https://accounts.spotify.com/api/token'

        response = requests.post(url, data=body_params, auth=(client_id, client_secret))
        if response.status_code != 200:
            print('error')
        self.spotify_token = response.json()['access_token']
        return self.spotify_token

    def get_song_ids_from_list(self):
        for i in range(self.length):
            id=self.get_spotify_id(self.csv['name'][i],self.csv['artist'][i])
            state=''
            if id==-1:
                time.sleep(self.time_long_sleep)
                spotify_token=self.get_access_token()
                i=i-1
            elif id==0:
                state='Fail\t'+str(id)
                self.failList.append([i,self.csv['name'][i],self.csv['artist'][i]])
                self.ids.append([i, self.csv['name'][i], self.csv['artist'][i], id,state])
                self.failCount=self.failCount+1
            elif id==-2:
                state='\t\t* * * Fail\t'+str(id)
                self.failList.append([i,self.csv['name'][i],self.csv['artist'][i]])
                self.ids.append([i, self.csv['name'][i], self.csv['artist'][i], id,state])
                self.failCount=self.failCount+1
            else:
                state='Success\t'
                self.ids.append([i,self.csv['name'][i],self.csv['artist'][i],id,state])
            print('\tindex:',i,'th', state,';', 'progress','%02f%%' % ((i+1)/(self.length)*100),
                  'ratio of success:','%02f%%' % ((i+1-self.failCount)/(i+1)*100 )
                  ,self.csv['name'][i],self.csv['artist'][i])
            # with open(self.outTxtPath + '\log.txt', 'a', newline='', encoding="utf-8") as f:
            #     data='\tindex:'+str(i)+'th'+ state+';'+ 'progress'+'%02f%%' % ((i+1)/(self.length)*100)+'ratio of success:'+'%02f%%' % ((i+1-self.failCount)/(i+1)*100 )+self.csv['name'][i]+self.csv['artist'][i]
            #     f.write(data)
            time.sleep(self.time_short_sleep)

    def get_spotify_id(self,song_name, artist):
        """Search For the Song"""
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json","Authorization": "Bearer {}".format(self.spotify_token)
            }
        )
        if response.status_code == 200:
            response_json = response.json()
            songs = response_json["tracks"]["items"]
            if songs==[]:
                return 0
            else:
                song_id= songs[0]["uri"]
        elif response.status_code == 401:
            print(f"\tResponse gave status code {response.status_code}")
            return -1
        else:
            print(f"\t\t!!! Response gave status code {response.status_code}")
            print(song_name+'___'+artist)
            return -2

        return song_id

    def get_features(self):
        df_all = pd.DataFrame(columns=(
        'acousticness', 'analysis_url', 'danceability', 'duration_ms', 'energy',
           'id', 'instrumentalness', 'key', 'liveness', 'loudness', 'mode',
           'speechiness', 'tempo', 'time_signature', 'track_href', 'type', 'uri',
           'valence'))
        headers = {'Authorization': 'Bearer ' + self.get_access_token()}
        for id in self.ids:
            time.sleep(self.time_short_sleep)
            df_feat=self.get_feature(id.strip("spotify:track:"))
            # X = df_features[
            #     ['acousticness', 'danceability', 'energy', 'instrumentalness', 'key', 'liveness', 'loudness', 'speechiness',
            #      'tempo', 'time_signature', 'valence']]
            df_all.append(df_feat)
        return df_all

    def get_feature(self,id):
        # df_feat=pd.DataFrame(columns=(
        # 'acousticness', 'analysis_url', 'danceability', 'duration_ms', 'energy',
        #    'id', 'instrumentalness', 'key', 'liveness', 'loudness', 'mode',
        #    'speechiness', 'tempo', 'time_signature', 'track_href', 'type', 'uri',
        #    'valence'))
        headers = {'Authorization': 'Bearer ' + self.get_access_token()}
        time.sleep(self.time_short_sleep)
        id = id.strip("spotify:track:")
        response = requests.get(f"https://api.spotify.com/v1/audio-features/{id}", headers=headers)
        if response.status_code == 200:
            features = response.json()
            df_feat = pd.DataFrame([features])
            return df_feat
        elif response.status_code == 401:
            print(f"Response gave status code {response.status_code}")
            self.get_access_token()
            return -1
        else:
            print(f"!!! Response gave status code {response.status_code}")
            return -2
        # return df_feat


if __name__ == "__main__":
    sptf=spotifyTool()
    sptf.read_song_List()

    sptf.get_access_token()
    # headers = {'Authorization': 'Bearer ' + sptf.get_access_token()}

    sptf.get_song_ids_from_list()

    # sptf.failCount = len(sptf.failList)

#   ids를 전부 다 받았고 아래는 검색 실패한 목록이다.
#   목록은 보완해서 수정하기 위해서 엑셀로 저장
    df_fail = pd.DataFrame(sptf.failList)
    df_fail.columns = ['name', 'artist']

    df_fail.to_excel(os.path.join(sptf.outTxtPath, 'fail.xlsx')
                     ,header=False
                     ,startcol=0
                     ,startrow=0
                     ,index=False
                     )
    df_fail2=df_fail
    df_fail2.columns = ['name', 'artist']
    del df_fail2['name']
    df_fail2.drop_duplicates()
    df_fail2.to_excel(os.path.join(sptf.outTxtPath, 'fail2_drop.xlsx')
                     ,header=False
                     ,startcol=0
                     ,startrow=0
                     ,index=False
                     )
    df_ids=pd.DataFrame(sptf.ids)
    df_ids.to_excel(os.path.join(sptf.outTxtPath, 'ids.xlsx')
                     ,header=False
                     ,startcol=0
                     ,startrow=0
                     ,index=False
                     )

    # idss = get_spotify_id("Good day", "iu")
    # df_all=pd.DataFrame(columns=('acousticness', 'danceability', 'energy', 'instrumentalness', 'key', 'liveness', 'loudness', 'speechiness',
    #          'tempo', 'time_signature', 'valence'))
    #

    df_all=sptf.get_features()

    df_all.to_excel(os.path.join(sptf.outTxtPath, 'features.xlsx')
                     ,header=False
                     ,startcol=0
                     ,startrow=0
                     ,index=False
                     )

    #
    # ids_test= ",".join(sptf.ids)
    # r = requests.get(f"https://api.spotify.com/v1/audio-features/?sptf.ids={ids_test}",
    #                  headers={
    #                      "Content-Type": "application/json",
    #                      "Authorization": "Bearer {}".format(sptf.spotify_token)
    #                  }
    #                  )
    #
    # features = r.json()
    # df_features = pd.DataFrame(features['audio_features'])
    # X = df_features[
    #     ['acousticness', 'danceability', 'energy', 'instrumentalness', 'key', 'liveness', 'loudness', 'speechiness',
    #      'tempo', 'time_signature', 'valence']]

    # sptf.csv2 = sptf.csv.drop_duplicates()
    # X.to_excel(os.path.join(sptf.outTxtPath, 'features.xlsx')
    #              ,header=False
    #              ,startcol=0
    #              ,startrow=0
    #              ,index=False
    #              )