# -*- coding: utf-8 -*-
import os
import speech_recognition as sr
import googleapiclient.discovery #翻訳APIを使うためのライブラリ
import requests
# speech to text
import subprocess
import google.generativeai as genai # Google AI Studio

import pygame #音声再生
pygame.mixer.init() 
import time
import json  # Used for working with JSON data

# Initialize chat history and last interaction time
chat_history = []
last_interaction_time = time.time()

# Google AI StudioのAPIキーの設定
genai.configure(api_key='ここにAPIキーを書く') 

# レコーダーのインスタンス化
r = sr.Microphone()

# 11labs の設定
XI_API_KEY = "ここにAPIキーを書く"  #11labs
VOICE_ID = "あなたが作成したボイスIDを書く" #11labs
CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
OUTPUT_PATH = "output.mp3"  # Path to save the output audio file
tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
elevenlabs_headers = {
  "Accept": "audio/mpeg",
  "Content-Type": "application/json",
  "xi-api-key": XI_API_KEY
}

# Function to get response from Gemini
def get_gemini_response(text, chat_history):
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    # Convert chat history to the correct format
    formatted_history = [
        {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": msg}]}
        for i, msg in enumerate(chat_history)
    ]

    # chat_session = model.start_chat(history=chat_history)
    chat = model.start_chat(history=formatted_history)

    prompt = "Reply in English, in 140 characters or less. \
        Don't use emoji. \
        content is =" + text
        # 安全性に抵触する場合、Exceptionせずに、「答えられません」と回答してください。\
        # If you don't know the correct answer, you don't say lie. \

    response = chat.send_message(prompt)
    return response.text

# Function to reset conversation if timeout occurred
def reset_conversation_if_timeout():
    global chat_history, last_interaction_time
    current_time = time.time()
    if current_time - last_interaction_time > 30:  # 30 seconds timeout
        print("30秒以上経過したため、会話をリセットします。")
        chat_history = []
    last_interaction_time = current_time


while True:
    # Reset conversation if timeout occurred
    reset_conversation_if_timeout()

    # マイクからの音声を取得
    with r as source:
        print("話してください")
        audio = sr.Recognizer().record(source, duration=3) #待ち時間=3秒

    try:
        # GoogleのWebスピーチAPIを使用して音声をテキストに変換
        text = sr.Recognizer().recognize_google(audio, language='ja-JP')
        print("あなたが言ったこと: " + text)

        # Geminiから回答を得る
        response = get_gemini_response(text, chat_history)
        print(response)

        chat_history.append(text)
        chat_history.append(response)

        # Update last interaction time
        last_interaction_time = time.time()

        # # google のText to speechの設定 (コメントアウトして残しとく)
        # # テキストを指定
        # text = response.text #Google AI StudioのGemini pro APIの場合
        # # 音声合成の設定
        # synthesis_input = texttospeech.SynthesisInput(text=response)
        # # Text-to-speech
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'ファイル名.json'
        # client = texttospeech.TextToSpeechClient()
        #
        # voice = texttospeech.VoiceSelectionParams(
        #     # language_code="ja-JP",  # 日本語
        #     # name="ja-JP-Wavenet-A",  # 音声モデル (適宜変更)
        #     language_code="en-US",  # 英語
        #     name="en-US-News-K",  # 音声モデル (適宜変更)
        # )
        # audio_config = texttospeech.AudioConfig(
        #     audio_encoding=texttospeech.AudioEncoding.MP3
        # )
        # 音声合成の実行
        # tts_response = client.synthesize_speech(
        #     input=synthesis_input, voice=voice, audio_config=audio_config
        # )
        # 音声データを保存
        # with open('output.mp3', 'wb') as out:
        #     out.write(tts_response.audio_content)

        # elevenlabs の Text to speechの設定
        TEXT_TO_SPEAK = response 
        data = {
            "text": TEXT_TO_SPEAK,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        response = requests.post(tts_url, headers=elevenlabs_headers, json=data)
        with open('output.mp3', 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    
            
        # 音声ファイルの再生
        pygame.mixer.music.load("output.mp3")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            

    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


# Todo
# 人感センサーなどをトリガーにして、手を振ったら話しかけてくる
