import os

from flask import Flask, g, render_template, request, url_for, redirect, session, request
import json
import threading
import datetime
import time

from flaskr.db import get_db

def after_this_request(f):
	print("after called")
	if not hasattr(g, 'after_request_callbacks'):
		g.after_request_callbacks = []
	g.after_request_callbacks.append(f)
	return f

###############################
# Azure stuff
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import TextOperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import TextRecognitionMode
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

from array import array
import os
from PIL import Image
import sys
import time
import time
import requests
from pprint import pprint
import re

counter = 0

# Add your Computer Vision subscription key and Computer Vision endpoint
subscription_key = '778bdd6307a54f5b8054a00930642d02'
endpoint = 'https://retinaid.cognitiveservices.azure.com/'
assert subscription_key
assert endpoint

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

category_tags = {"food_" : "Food", "drink_" : "Drinks", "text_menu" : "Text -- Menus", "text_sign" : "Text -- Sign", "animal_" : "Animal", "abstract_" : "Abstract"}

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
	query_ids = [3,1,2]
	answer_ids = [3, 5, 2, 7, 8, 9, 10]

	# Check to see if fake data's already been created
	answer = db.execute(
            'SELECT * FROM answer WHERE id = ?', (answer_ids[0],)
        ).fetchone()
	if answer:
		return query_ids
	
	# Create fake data
	username = g.user['username']
	db.execute(
		'UPDATE user SET query_list = ? WHERE username = ?', ("1,3,2", username)
	)
	db.execute(
	'INSERT INTO query (id, author_id, title, subtitle, pic_filename, category, top_answer, answer_list, answer_state, machine_answer_id) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
	(query_ids[2], 2, "What is the thing", "Price below", "garden.JPG", "miscellaneous", "10", "10", 2, answer_ids[6])
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[6], 4, 1, 3, 'Garden Fork', "dave")
	)
	#another one
	db.execute(
	'INSERT INTO query (id, author_id, title, subtitle, pic_filename, category, top_answer, answer_list, answer_state, machine_answer_id) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
	(query_ids[0], 2, "What is the price", "Price below", "xbox_price.JPG", "price tag", "8", "8,9", 1, answer_ids[4])
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[4], 8, 2, 3, '$399.99', "dave")
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[5], 4, 4, 3, '$3990', "jane")
	)

	#another one
	
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[1], 4, 2, 1, 'apple spoiled', "bob")
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[3], 2, 4, 1, 'boy', "tester")
	)
	db.execute(
	'INSERT INTO query (id, author_id, title, subtitle, pic_filename, category, top_answer, answer_list, answer_state, machine_answer_id) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
	(query_ids[1], 2, "Is this apple bad", "apple below", "124687474-rotten-apple-on-a-white-background.jpg", "produce", "3", "3,5,2,7", 0, answer_ids[1])
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[0], 16, 3, query_ids[1], 'contains fungus', "helpful hank")
	)
	db.execute(
	'INSERT INTO answer (id, upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?, ?)',
	(answer_ids[2], 0, 0, query_ids[1], 'A house on the hill', "confused craig")
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
		# local_image_path = "flaskr/static/scam.jpg"
		# local_image = open(local_image_path, "rb") 
		
		# print("===== Describe the sample image =====")
		# # Call API
		# description_features = ["categories"]
		# description_results = computervision_client.describe_image_in_stream(local_image)
		# description_categories = computervision_client.analyze_image_in_stream(local_image, description_features)
		# print(description_results)
		# print("CATEGORIES\n")
		# print(description_categories)

		# # Get the captions (descriptions) from the response, with confidence level
		# print("Description of remote image: ")
		# if (len(description_results.captions) == 0):
		# 	print("No description detected.")
		# else:
		# 	print("Description: '{}'".format(description_results.captions[0].text))
		return render_template('retina/query_create.html')

	# @app.route('/query_display')
	# def query_display():
	# 	screen_text = ""
	# 	print("REQ ARGS:", request.args)
	# 	full_path = os.path.join(request.host_url, 'static', 'uploads', request.args['filename'])
	# 	return render_template('retina/query_display.html', screen_text=screen_text, display_image = full_path)

	@app.route('/post_answer', methods=('GET', 'POST'))
	def post_answer():
		db = get_db()
		query_id = request.args.get('query_id')
		# query_ids = create_fake_data()
		if request.method == 'POST':
			# Put the answer in the db
			answer = request.form['answer']
			db.execute('INSERT INTO answer (upvotes, downvotes, query_id, content, username) VALUES ( ?, ?, ?, ?, ?)',
						(0, 0, query_id, answer, g.user["username"]))
			answer= db.execute('SELECT * FROM answer WHERE content = ?',
						(answer,)).fetchone()
			answer_id = answer['id']

			# Update the corresponding query's answer_list and top_answer fields as appropriate
			query = db.execute('SELECT * FROM query WHERE id = ?', (query_id,)).fetchone()
			new_answer_list = (query['answer_list'] + ',' + str(answer_id)) if (query != None) else str(answer_id)
			new_query_state = 0 # unanswered
			db.execute(
				'UPDATE query SET answer_list = ?, answer_state = ? WHERE id = ?', (new_answer_list, new_query_state, query_id)
			)
			top_answer_id = get_top_answer(new_answer_list)
			if top_answer_id is not None:
				db.execute(
					'UPDATE query SET top_answer = ? WHERE id = ?', (str(top_answer_id), query_id)
				)

			db.commit()
			return redirect(url_for("index"))

		# TODO: uncomment below
		# query = db.execute(
	    # 	'SELECT * FROM query WHERE id = ?', (query_id,)
	    # 	).fetchone()

		query = db.execute(
	    	'SELECT * FROM query'
	    	).fetchone()

		print(query)

		return render_template('retina/post_answer.html', res=query)

	@app.route('/view_answer')
	def view_answer():
		query_id = request.args.get('query_id')

		(print(query_id))
		db = get_db()
		# create_fake_data()

		query = db.execute(
		   	'SELECT * FROM query WHERE id = ?', (query_id,)
		   	).fetchone()

		machine_answer_id = int(query["machine_answer_id"])
		machine_answer = db.execute('SELECT * FROM answer WHERE id = ?', (machine_answer_id,)).fetchone() if machine_answer_id > 0 else None
		user_answer = db.execute('SELECT * FROM answer WHERE id = ?', (int(query["top_answer"]),)).fetchone()

		return render_template('retina/view_answer.html', res=query, machine_answer=machine_answer, top_answer=user_answer)


	@app.route('/vote_answer')
	def vote_answer():
		db = get_db()
		# create_fake_data()
		query_id = request.args.get('query_id')
		answer_id = request.args.get('answer_id')
		up = request.args.get('up')
		# print("UP", up)

		if answer_id != None:
			answer = db.execute('SELECT * FROM answer WHERE id = ?', (int(answer_id),)).fetchone()
			#print(answer["content"], print(answer["upvotes"]))
			upvotes = answer["upvotes"]
			downvotes = answer["downvotes"]
			if up: db.execute('UPDATE answer SET upvotes = ? WHERE id = ?', (upvotes + 1, answer_id))
			else: db.execute('UPDATE answer SET downvotes = ? WHERE id = ?', (downvotes + 1, answer_id))
		db.commit()

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
			return render_template('retina/query_create.html', query_id=query_id)

		query = db.execute(
		   	'SELECT * FROM query WHERE id = ?', (query_id,)
		   	).fetchone()
		# query = db.execute(
	 #    	'SELECT * FROM query'
	 #    	).fetchone()


		query_answer_ids = query['answer_list'].split(',')
		if  query['answer_list'] == '':
			return render_template('retina/vote_answer.html', res=query, answers=[], top_answer=None)

		query_answers = []
		for answer_id in query_answer_ids:
			answer = db.execute('SELECT * FROM answer WHERE id = ?', (int(answer_id),)).fetchone()
			print(answer_id, answer["upvotes"])
			net_upvotes = answer['upvotes'] - answer['downvotes'] if answer!=None else 0
			query_answers.append((answer, net_upvotes))
		return render_template('retina/vote_answer.html', res=query, answers=query_answers, top_answer=query["top_answer"])


	@app.route('/seeker_main')
	def seeker_main():
		return render_template('retina/seeker_main.html')

	@app.route('/leaderboard')
	def leaderboard():
		return render_template('retina/leaderboard.html')

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
				file_path = os.path.join(app.static_folder, 'uploads', file.filename)
				file.save(file_path)

				db = get_db()
				timestamp  = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
				title = request.form.get('title')
				subtitle = request.form.get('subtitle')

				#TODO - add username
				db.execute(
					'INSERT INTO query (author_id, created, title, subtitle, pic_filename, category, top_answer, answer_list) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
					(session.get('user_id'), timestamp, title, subtitle, file.filename, '', '0', '')
				)

				# Get query ID
				query = db.execute('SELECT * FROM query WHERE title = ?', (title,)).fetchone()
				query_id = query['id']
				
				print(query, query["title"])

				# Generate machine description
				print("===== Describe the local image =====")
				local_image = open(file_path, "rb") 
				description_results = computervision_client.describe_image_in_stream(local_image)
				local_image = open(file_path, "rb") 
				description_features = ["categories"]
				description_categories = computervision_client.analyze_image_in_stream(local_image, description_features)

				image_category = "Miscellaneous"
				if (len(description_categories.categories) > 0):
					image_category = '{}'.format(description_categories.categories[0].name)
					if image_category in category_tags:
						image_category = category_tags[image_category]
					else:
						image_category = "Miscellaneous"

				db.execute('UPDATE query SET category = ? WHERE id = ?', (image_category, query_id)).fetchone()

				print("Description of local image: ")
				description = ""
				if (len(description_results.captions) == 0):
					description = "None"
					print("No description detected.")
				else:
					description = description_results.captions[0].text
					print("Description: '{}'".format(description_results.captions[0].text))
				db.execute(
					'INSERT INTO answer (query_id, content, username) VALUES (?, ?, ?)',
					(query_id, description_results.captions[0].text, g.user['username'])
				)
				# Get answer ID
				answer = db.execute('SELECT * FROM answer WHERE content = ?', (description_results.captions[0].text,)).fetchone()
				answer_id = answer['id']
				db.execute(
					'UPDATE query SET machine_answer_id = ? WHERE title = ?', (answer_id, title)
				)

				# Update user query list
				user = db.execute('SELECT * FROM user WHERE username = ?', (g.user['username'],)).fetchone()
				if user['query_list'] == "":
					new_query_list = str(query_id)
				else:
					new_query_list = user['query_list'] + ',' + str(query_id)
				db.execute('UPDATE user SET query_list = ? WHERE username = ?', (new_query_list, g.user['username']))
				db.commit()
				return redirect(url_for('index'))

	@app.route('/query_view')
	def view_user_queries():
		# Fetch user queries from db
		db = get_db()
		print('h')

		create_fake_data()
		print('hi')

		username = g.user["username"]
		users = db.execute(
            'SELECT * FROM user')
		query_list = []
		for row in iter(users.fetchall()):
			if row["user_type"] == 0: 
				curr_query_list = row["query_list"].split(",")
				if row["query_list"] != '':
					query_list.extend(curr_query_list)

				


		# if user['query_list'] == '':
		# 	return render_template('retina/query_view.html', user_queries=[], num_queries=0)

		# user_query_ids = user['query_list'].split(',')
		user_queries = []
		user_query_ids = query_list
		for query_id in user_query_ids:
			print(query_id)
			query = db.execute('SELECT * FROM query WHERE id = ?', (int(query_id),)).fetchone()
			top_answer = db.execute('SELECT * FROM answer WHERE id = ?', (int(query['top_answer']),)).fetchone()
			num_answers = len(query['answer_list'].split(','))
			query_answer_state = int(query['answer_state'])
			color = 'red' if query_answer_state == 0 else 'yellow' if query_answer_state == 1 else 'green'
			query_id = int(query_id)
			user_queries.append((query, top_answer, num_answers, color, query_id))

		return render_template('retina/query_view.html', user_queries=user_queries, num_queries=len(user_queries))

	@app.route('/past_queries')
	def past_queries():
		# Fetch user queries from db
		db = get_db()

		# create_fake_data()
		# db.commit()

		username = g.user["username"]
		user = db.execute(
			'SELECT * FROM user WHERE username = ?', (username,)).fetchone()

		if user['query_list'] == '':
			return render_template('retina/past_queries.html', user_queries=[], num_queries=0)

		user_query_ids = user['query_list'].split(',')
		user_queries = []
		for query_id in user_query_ids:
			query = db.execute('SELECT * FROM query WHERE id = ?', (int(query_id),)).fetchone()
			print(query_id)
			top_answer = db.execute('SELECT * FROM answer WHERE id = ?', (int(query['top_answer']),)).fetchone()
			num_answers = len(query['answer_list'].split(','))
			query_answer_state = int(query['answer_state'])
			color = 'red' if query_answer_state == 0 else 'yellow' if query_answer_state == 1 else 'green'
			query_id = int(query_id)
			user_queries.append((query, top_answer, num_answers, color, query_id))
		
		db.commit()
		return render_template('retina/past_queries.html', user_queries=user_queries, num_queries=len(user_queries))

	@app.route('/profile', methods=('GET', 'POST'))
	def user_profile():
		db = get_db()
		# create_fake_data()

		username = g.user["username"]
		user_type = "Seeker" if g.user['user_type']==0 else "Answerer"
		print(g.user['profile_pic_filename'] )
		profile_pic_filename = "user_icon_2.png" if g.user['profile_pic_filename'] == None else g.user['profile_pic_filename']
		
		user = db.execute(
	            'SELECT * FROM user WHERE username = ?', (username,)
	        ).fetchone()

		user_query_ids = user['query_list'].split(',')
		print(user_query_ids)
		# Seeker profile
		if g.user['user_type']==0:
			return render_template('retina/user_profile.html', username=username, user_type=user_type,
								user_picture_filename=profile_pic_filename, num_queries=len(user_query_ids))
		else:
			return render_template('retina/ans_user_profile.html', username=username, user_type=user_type,
								user_picture_filename=profile_pic_filename, num_queries=len(user_query_ids))


	@app.route('/', methods=('GET', 'POST'))
	def index():
		if g.user is None:
			return redirect(url_for('auth.login'))
		if g.user["user_type"] == 0:
			return render_template('blog/index.html')
		elif g.user["user_type"] == 1:
			return redirect(url_for('view_user_queries'))

	from flaskr import db
	db.init_app(app)

	from flaskr import auth
	app.register_blueprint(auth.bp)

	from flaskr import blog
	app.register_blueprint(blog.bp)

	app.add_url_rule('/', endpoint='index')


	return app
