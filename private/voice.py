# !/usr/bin/env python3
# -*- codig: utf-8 -*-
import jsonify
import requests
import json
import whisper
import connection.dbConnectTemplate as dbtemp


# def stt(source):
def voice_analysis(itvNo, qNo, filename):

    model = whisper.load_model("base")
    result = model.transcribe(itvNo + "/" + filename)
    # print(result)
    start_point = result['segments'][0]['start']        # 답변 시작 시간
    end_point = result['segments'][-1]['end']         # 답변 종료 시간
    print(f"시작 시간 : {start_point}, 종료 시간 : {end_point}")
    print(result["text"])

    content = result["text"]       # STT 문자열

    client_id = "exhnc4vqhw"
    client_secret = "C82anCAZex9PK4XktQLYlUBYwmTodghxMTBwHHCb"
    url="https://naveropenapi.apigw.ntruss.com/sentiment-analysis/v1/analyze"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
        "Content-Type": "application/json"
    }

    data = {
      "content": content
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    results = json.loads(response.text)

    voice_list = list()
    rescode = response.status_code
    if (rescode == 200):
        for result in results['sentences']:
            sentence = result['content']

            offset, length = None, None
            for h in result['highlights']:
                offset = h['offset']
                length = h['length']
            highlight = result['content'][offset:offset + length]
            sentiment = result['sentiment']
            negative = result['confidence']['negative']
            positive = result['confidence']['positive']
            neutral = result['confidence']['neutral']

            print(f"  답변 문장: {sentence}")
            print(f"  강조된 분석 구문: {highlight}")
            print("분석 결과:")
            print(f"  문장 경향성: {sentiment}")
            print(f"  수치:")
            print(f"    부정: {negative}")
            print(f"    긍정: {positive}")
            print(f"    중립: {neutral}")
            print()
            each_sentence = ['', '', sentence, positive, negative]
            # TB_VOICE_SENTENCE 각 행 저장 list
            voice_list.append(each_sentence)
    else:
        print("Error : " + response.text)
    voice_content = ['', itvNo, qNo, content]     # 리스트

    print(voice_list)

    dbtemp.oracle_init()
    conn = dbtemp.connect()

    # "insert into TB_VOICE (VOICE_CONTENT) values (:1)"
    query1 = "insert into TB_VOICE values (:1, :2, :3, :4)"     # (VOICE_NO, ITV_NO, Q_NO, VOICE_CONTENT)
    query2 = "insert into TB_VOICE_SENTENCE values (:1, :2, :3, :4, :5)" #(VS_NO, VOICE_NO, SENTENCE, VSEN_POSITIVE, VSEN_NEGATIVE)
    query3 = "select max(voice_no) from TB_VOICE"
    query4 = "select max(vs_no) from TB_VOICE_SENTENCE"
    cursor = conn.cursor()

    try:
        # VOICE_NO 부여
        cursor.execute(query3)
        voice_no = cursor.fetchone()[0]
        if voice_no is None:
            voice_no = 1
        voice_content[0] = voice_no

        # VOICE 데이터 튜플 변환 및 쿼리 INSERT
        voice = tuple(voice_content)
        cursor.execute(query1, voice)

        # 첫 VS_NO 부여
        cursor.execute(query4)
        vs_no = cursor.fetchone()[0]
        if vs_no is None:
            vs_no = 0

        # TB_VOICE_SENTENCE
        for s in voice_list:
            #VS_NO 부여
            vs_no = vs_no + 1
            s[0] = vs_no
            s[1] = voice_no
            print("vs_no 및 voice_no 주입", s)

            # VOICE_SETENCE 데이터 튜플 변환 및 쿼리 INSERT
            row = tuple(s)
            print("row", row)
            cursor.execute(query2, row)
            conn.commit()
        print("커밋 성공")
    except:
        conn.rollback()
        print("커밋 실패")
    finally:
        cursor.close()
        dbtemp.close(conn)



