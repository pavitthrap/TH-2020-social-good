import os 

from flask import Flask, g, render_template, request, url_for
import json 
import threading
#from . import db

def after_this_request(f):
	print("after called")
	if not hasattr(g, 'after_request_callbacks'):
		g.after_request_callbacks = []
	g.after_request_callbacks.append(f)
	return f

###############################
# import azure.cognitiveservices.speech as speechsdk
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

# speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

# # Set up the speech recognizer
# speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

done = False


#################

demo = False
curr_text = ""
analysis_result = ""
sentiment_result = 0.9
keyword_result = 7


def update_curr_text(text):
	global curr_text
	print(text)
	curr_text = text
	#print("updating curr text", curr_text)

########################
# Connect callbacks to the events fired by the speech recognizer
rec = ""

def analyze_speech(rec):
    global counter, curr_text, sentiment_result
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
    sentiment_result = sentiment

    print("-----------Sentiment Analysis ", sentiment)
    print("\n")

    if abs(.5 - sentiment) >= .38:
        counter +=1

    total_analysis()


def total_analysis():
    global counter, analysis_result, keyword_result
    print(counter)
    if counter >= 6:
        analysis_result = "HIGH RISK - NOTIFYING BANK"
        print("-----------HIGH RISK ALERT - NOTIFYING BANK")
        #HIGH RISK, NOTIFY BANK - DISPLAY HOW HIGH
    elif counter >= 4:
        analysis_result = "MEDIUM RISK - NOTIFYING BANK"
        print("-----------MEDIUM RISK ALERT - NOTIFYING BANK")
        #MEDIUM RISK
    elif counter >= 2:
        analysis_result = "LOW RISK - NOTIFYING BANK"
        print("-----------LOW RISK ALERT - NOTIFYING BANK")
        #
    else:
        analysis_result = "VERY LOW RISK"
        print("-----------VERY LOW RISK")
    keyword_result = counter
    print("\n", analysis_result, "setting analysis", keyword_result)




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


##########################
# speech_recognizer.recognizing.connect(lambda evt: update_curr_text(evt.result.text))
# speech_recognizer.recognized.connect(lambda evt: analyze_speech(rec.join(evt.result.text)))
# speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
# speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
# speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
# stop continuous recognition on either session stopped or canceled events

#################################################

def sustain_speech():
    print("sustain called")
    speech_recognizer.start_continuous_recognition()
    for i in range(35):
        time.sleep(.5)
    #print("CURR TEXT IS", curr_text)
    speech_recognizer.stop_continuous_recognition()

def stop_cb(evt):
    #"""callback that stops continuous recognition upon receiving an event `evt`"""
    print('CLOSING on {}'.format(evt))
    speech_recognizer.stop_continuous_recognition()
    done = True

 ################################################

# speech_recognizer.session_stopped.connect(stop_cb)
# speech_recognizer.canceled.connect(stop_cb)









def create_app(test_config=None):
	# create and configure the app 
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY='dev', 
		DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
	)

	if test_config is None:
		#load the instance config, if it exists, when not testing 
		app.config.from_pyfile('config.py', silent=True)
	else:
		#load the test config if passed in 
		app.config.from_mapping(test_config)


	#ensure the instance folder exists
	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

    # a simple page that says hello 
	@app.route('/hello')
	def hello():
		return 'Hello, World!'

	#@app.before_request	
	@app.route('/', methods=('GET', 'POST'))
	def index(screen_text="Unknown Caller", sentiment=0.9, keywords=7):
	    # row = get_db().execute(
	    #         'SELECT * FROM status WHERE id = (SELECT MAX(id) FROM status);'
	    #     ).fetchone()
	    
	    """Show all the posts, most recent first."""
	    #print("show index")
	    global demo, curr_text, analysis_result, keyword_result, sentiment_result
	    state = getattr(g, 'state', None)
	    screen_text = ""
	    if state is None:
	        g.state = 1
	    if request.method == 'POST':
	        print(request.form)
	        
	        request_JSON = request.data
	        #print(request_JSON)
	        #request_JSON = json.dumps(request_JSON)
	        request_JSON = request_JSON.decode('utf-8')
	        #print(request_JSON)
	        if 'phonedemo' in request.form:
	        	g.state = 1
	        elif 'appdemo' in request.form:
	        	g.state = 4
	        elif 'enterapp.x' in request.form:
	        	g.state = 5
	        elif 'bankacct' in request.form:
	        	g.state = 7
	        elif 'mainscreen' in request.form:
	        	g.state = 8
	        elif 'analysis' in request.form:
	        	g.state = 3
	        	screen_text = analysis_result
	        	sentiment = round(sentiment_result, 3)
	        	keywords = keyword_result
	        	print("analysis result is", analysis_result, sentiment_result, keyword_result)
	        elif 'homepage' in request.form:
	        	g.state = 3
	        	screen_text = analysis_result
	        	print("analysis result is", analysis_result)
	        elif 'name=startdemo' == request_JSON or 'demo1.x' in request.form:
	        	demo=True
	        	counter = 0
	        elif 'name=getupdate' == request_JSON: 
	        	screen_text = curr_text
	        elif 'seecall' in request.form: 
	        	g.state = 6
	        	print("curr text is", curr_text)
	        	screen_text = curr_text
	        # print("going to return")
	        return render_template('blog/index.html', screen_text=screen_text, sentiment=sentiment, keywords=keywords)

	    # db = get_db()
	    # posts = db.execute(
	    #     'SELECT p.id, title, body, created, author_id, username'
	    #     ' FROM post p JOIN user u ON p.author_id = u.id'
	    #     ' ORDER BY created DESC'
	    # ).fetchall()
	    return render_template('blog/index.html')

	from flaskr import db
	db.init_app(app)

	from flaskr import auth
	app.register_blueprint(auth.bp)

	from flaskr import blog
	app.register_blueprint(blog.bp)
	app.add_url_rule('/', endpoint='index')

	@app.before_first_request
	def activate_job():
	    def run_demo():
	        global demo
	        while not demo:
	        	time.sleep(1)
	        	#print("value of demo", demo)
	        	pass
	        #print("demo is gn start")
	        sustain_speech()

	    thread = threading.Thread(target=run_demo)
	    thread.start()

	return app