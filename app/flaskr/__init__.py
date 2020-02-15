import os

from flask import Flask, g, render_template, request, url_for, redirect, session
import json
import threading
import datetime
import time
#from . import db

from flaskr.db import get_db

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


# def sustain_speech():
#     print("sustain called")
#     speech_recognizer.start_continuous_recognition()
#     for i in range(35):
#         time.sleep(.5)
#     #print("CURR TEXT IS", curr_text)
#     speech_recognizer.stop_continuous_recognition()

# def stop_cb(evt):
#     #"""callback that stops continuous recognition upon receiving an event `evt`"""
#     print('CLOSING on {}'.format(evt))
#     speech_recognizer.stop_continuous_recognition()
#     done = True





def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def create_fake_data():
	db = get_db()
	query_ids = [3,1]
	answer_ids = [3, 5, 2]

	# Check to see if fake data's already been created
	answer = db.execute(
            'SELECT * FROM answer WHERE id = ?', (answer_ids[0],)
        ).fetchone()
	if answer:
		return query_ids
	
	# Create fake data
	username = g.user['username']
	db.execute(
		'UPDATE user SET query_list = ? WHERE username = ?', ("1,3", username)
	)
	db.execute(
	'INSERT INTO query (id, author_id, title, subtitle, pic_filename, category, top_answer, answer_list) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?)',
	(query_ids[0], 2, "Hello2", "Bob", "img.jpg", "hello", "3", "3,5")
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[0], 4, 2, 3, 'hoy', username)
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[1], 2, 4, 3, 'boy', username)
	)
	db.execute(
	'INSERT INTO query (id, author_id, title, subtitle, pic_filename, category, top_answer, answer_list) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?)',
	(query_ids[1], 2, "Cantelope", "Bobbyjoe", "img.jpg", "yoyo", "2", "2,4,5,6,7,9,8,21")
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[2], 16, 3, 1, 'choy', username)
	)
	return query_ids

def get_top_answer(answer_list):
	db = get_db()
	max_answer_id = None
	max_num_votes = -1
	for answer_id in answer_list.split(','):
		answer = db.execute(
            'SELECT * FROM answer WHERE id = ?', (int(answer_id),)
        ).fetchone()
		curr_num_votes = answer['upvotes'] - answer['downvotes']
		if curr_num_votes >= 0 and max_num_votes < curr_num_votes:
			max_answer_id = answer_id
			max_num_votes = curr_num_votes
	# returns None if no answer is found with a nonnegative number of upvotes 
	return max_answer_id
		

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

	# with app.app_context():
	# 	from db import init_db
	# 	print("init db")
	# 	init_db()

	#ensure the instance folder exists
	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

    # a simple page that says hello
	@app.route('/query_create')
	def query_create():
		return render_template('retina/query_create.html')

	@app.route('/query_display')
	def query_display():
		screen_text = ""
		sentiment=0.9
		keywords= "retina"
		full_path = os.path.join(request.host_url, 'static', 'uploads', request.args['filename'])
		return render_template('retina/query_display.html', screen_text=screen_text, display_image = full_path)

	@app.route('/post_answer', methods=('GET', 'POST'))
	def post_answer(query_id=0):
		db = get_db()
		query_ids = create_fake_data()
		query_id = query_ids[0]
		if request.method == 'POST':
			# Put the answer in the db
			answer = request.form['answer']
			db.execute('INSERT INTO answer (upvotes, downvotes, query_id, content) VALUES ( ?, ?, ?, ?)',
						(0, 0, query_id, answer))
			answer= db.execute('SELECT * FROM answer WHERE content = ?',
						(answer,)).fetchone()
			answer_id = answer['id']

			# Update the corresponding query's answer_list and top_answer fields as appropriate
			query = db.execute('SELECT * FROM query WHERE id = ?', (query_id,)).fetchone()
			new_answer_list = query['answer_list'] + ',' + str(answer_id)
			new_query_state = 0 # unanswered
			db.execute(
				'UPDATE query SET answer_list = ?, answer_state = ? WHERE id = ?', (new_answer_list, new_query_state, query_id)
			)
			top_answer_id = get_top_answer(new_answer_list)
			if top_answer_id is not None:
				db.execute(
					'UPDATE query SET top_answer = ? WHERE id = ?', (str(top_answer_id), query_id)
				)
			return render_template('retina/query_create.html')

		# TODO: uncomment below
		# query = db.execute(
	    # 	'SELECT * FROM query WHERE id = ?', (query_id,)
	    # 	).fetchone()

		query = db.execute(
	    	'SELECT * FROM query'
	    	).fetchone()

		print(query)

		screen_text = ""
		sentiment=0.9
		keywords= "retina"
		return render_template('retina/post_answer.html', res=query, screen_text=screen_text)

	@app.route('/view_answer')
	def view_answer(query_id=0):
		db = get_db()
		create_fake_data()
		# query = db.execute(
		#    	'SELECT * FROM query WHERE id = ?', (query_id,)
		#    	).fetchone()
		query = db.execute(
	    	'SELECT * FROM query'
	    	).fetchone()


		print(query)

		screen_text = ""
		sentiment=0.9
		keywords= "retina"
		return render_template('retina/view_answer.html', res=query, screen_text=screen_text)


	@app.route('/vote_answer')
	def vote_answer(query_id=0):
		db = get_db()
		create_fake_data()
		if request.method == 'POST':
			# Put the answer in the db
			answer = request.form['answer']
			db.execute('INSERT INTO answer (upvotes, downvotes, query_id, content) VALUES ( ?, ?, ?, ?)',
						(0, 0, query_id, answer))
			answer= db.execute('SELECT * FROM answer WHERE content = ?',
						(answer,)).fetchone()
			answer_id = answer['id']

			# Update the corresponding query's answer_list and top_answer fields as appropriate
			query = db.execute('SELECT * FROM query WHERE id = ?', (query_id,)).fetchone()
			new_answer_list = query['answer_list'] + ',' + str(answer_id)
			new_query_state = 0 # unanswered
			db.execute(
				'UPDATE query SET answer_list = ?, answer_state = ? WHERE id = ?', (new_answer_list, new_query_state, query_id)
			)
			top_answer_id = get_top_answer(new_answer_list)
			if top_answer_id is not None:
				db.execute(
					'UPDATE query SET top_answer = ? WHERE id = ?', (str(top_answer_id), query_id)
				)
			return render_template('retina/query_create.html')

		# query = db.execute(
		#    	'SELECT * FROM query WHERE id = ?', (query_id,)
		#    	).fetchone()
		query = db.execute(
	    	'SELECT * FROM query'
	    	).fetchone()

		print(query)

		query_answer_ids = query['answer_list'].split(',')
		query_answers = []
		for answer_id in query_answer_ids:
			print(answer_id)
			answer = db.execute('SELECT * FROM answer WHERE id = ?', (int(answer_id),)).fetchone()
			net_upvotes = answer['upvotes'] - answer['downvotes'] if answer!=None else 0
			query_answers.append((answer, net_upvotes))
		return render_template('retina/vote_answer.html', res=query, answers=query_answers, top_answer=query["top_answer"])


	@app.route('/seeker_main')
	def seeker_main():
		return render_template('retina/seeker_main.html')

	@app.route('/upload_file', methods=['POST'])
	def upload_file():
		if request.method == 'POST':
			# check if the post request has the file part
			if 'file' not in request.files:
				return redirect(request.url)
			file = request.files['file']

			if file.filename == '':
				return redirect(request.url)
			if file and allowed_file(file.filename):
				file.save(os.path.join(app.static_folder, 'uploads', file.filename))

				db = get_db()
				timestamp  = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
				title = request.form.get('title')
				subtitle = request.form.get('subtitle')
				category = request.form.get('category')

				db.execute(
					'INSERT INTO query (author_id, created, title, subtitle, pic_filename, category) VALUES (?, ?, ?, ?, ?, ?)',
					(session.get('user_id'), timestamp, title, subtitle, file.filename, category)
				)
				db.commit()
				return redirect(url_for('query_display', filename=file.filename))

	@app.route('/query_view')
	def view_user_queries():
		# Fetch user queries from db
		db = get_db()

		create_fake_data()

		username = g.user["username"]
		user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

		user_query_ids = user['query_list'].split(',')
		user_queries = []
		for query_id in user_query_ids:
			print(query_id)
			query = db.execute('SELECT * FROM query WHERE id = ?', (int(query_id),)).fetchone()
			top_answer = db.execute('SELECT * FROM answer WHERE id = ?', (int(query['top_answer']),)).fetchone()
			num_answers = len(query['answer_list'].split(','))
			query_answer_state = int(query['answer_state'])
			color = 'red' if query_answer_state == 0 else 'yellow' if query_answer_state == 1 else 'green'
			user_queries.append((query, top_answer, num_answers, color))

		return render_template('retina/query_view.html', user_queries=user_queries)

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

	from flaskr import user
	app.register_blueprint(user.bp)

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
