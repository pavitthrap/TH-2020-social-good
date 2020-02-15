#!/usr/bin/python
# -*- coding: utf-8 -*-
import azure.cognitiveservices.speech as speechsdk
import time
import requests
from pprint import pprint
import re

counter = 0

subscription_key = "cc5ab8a32df6484981ec582e6669bd36"
assert subscription_key

text_analytics_base_url = "https://eastus2.api.cognitive.microsoft.com/text/analytics/v2.0"


speech_key = "6fd6a1d3a05742f8bfaf9ffdccfffbb6"
service_region = "westus"
key_phrase_api_url = text_analytics_base_url + "/keyPhrases"
senti_phrase_api_url = text_analytics_base_url + "/sentiment"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

# Set up the speech recognizer
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

done = False

def stop_cb(evt):
    #"""callback that stops continuous recognition upon receiving an event `evt`"""
    print('CLOSING on {}'.format(evt))
    speech_recognizer.stop_continuous_recognition()
    done = True

# Connect callbacks to the events fired by the speech recognizer
rec = ""

def analyze_speech(rec):
    global counter
    documents = {'documents' : [
      {'id': '1', 'language': 'en', 'text': rec},
    ]}

    headers   = {'Ocp-Apim-Subscription-Key': subscription_key}
    response  = requests.post(key_phrase_api_url, headers=headers, json=documents)
    key_phrases = response.json()

    for document in key_phrases["documents"]:
        text    = next(iter(filter(lambda d: d["id"] == document["id"], documents["documents"])))["text"]
        phrases = ",".join(document["keyPhrases"])
        print("\n")
        print("-----------Key Phrases Extracted: ", phrases)

    analyze_it(rec, phrases)

    response  = requests.post(senti_phrase_api_url, headers=headers, json=documents)
    sentiment = response.json().get("documents")[0].get("score")

    print("-----------Sentiment Analysis ", sentiment)
    print("\n")

    # if abs(.5 - sentiment) >= .38:
    #     counter +=1

    total_analysis()


def total_analysis():
    global counter
    print(counter)
    if counter >= 6:
        print("-----------HIGH RISK ALERT - NOTIFYING BANK")
        #HIGH RISK, NOTIFY BANK - DISPLAY HOW HIGH
    elif counter >= 4:
        print("-----------MEDIUM RISK ALERT - NOTIFYING BANK")
        #MEDIUM RISK
    elif counter >= 2:
        print("-----------LOW RISK ALERT - NOTIFYING BANK")
        #
    else:
        print("-----------VERY LOW RISK")
    print("\n")




def analyze_it(sentence, phrases):
    global counter
    triggerWords = ['gift', 'cards', 'gift cards', 'IRS', 'warranty', 'Medicare', 'insurance', 'social',
                    'social security', 'bank', 'routing', 'number', 'tax', 'dollars', 'owe',
                    'business listing', 'fee', 'interest', 'interest rate', 'loans', 'overdue', 'debt'
                    'verification', 'offer', 'limited time', 'important', 'urgent', 'credit', 'credit card',
                    'cover up', 'viagra', 'anti-aging', 'metabolism', 'bitcoin', 'illegal', 'donation',
                    'free vacation', 'free', 'loan', "you've won", 'low risk', 'free bonus', 'bonus',
                    'payment', 'lottery', 'trust', 'investment', 'subscription', 'can you hear me?',
                    'federal reserve', 'retirement', 'ROTH IRA', 'senior', '401k', 'tech support',
                    'Mark Zuckerberg', 'safe', 'virus', 'password', 'safety', 'lucky', 'won', 'winner',
                    'charity', 'pin number', 'pin', 'million', 'fraudulent activities']

    for word in triggerWords:
        if word.lower() in phrases.lower() or word.lower() in sentence.lower():
            counter+=1

    m = re.findall('([0-9]{2}[0-9]+)', sentence)
    counter += len(m)







speech_recognizer.recognizing.connect(lambda evt: print(evt.result.text))
speech_recognizer.recognized.connect(lambda evt: analyze_speech(rec.join(evt.result.text)))
speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
# stop continuous recognition on either session stopped or canceled events
speech_recognizer.session_stopped.connect(stop_cb)
speech_recognizer.canceled.connect(stop_cb)


# Start continuous speech recognition
speech_recognizer.start_continuous_recognition()
while not done:
    time.sleep(.5)




################################
