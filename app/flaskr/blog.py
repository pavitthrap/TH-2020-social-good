from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
import click
from flaskr.db import get_db
import click

bp = Blueprint('blog', __name__)



# setup speech recognition
#################################################
# import azure.cognitiveservices.speech as speechsdk
# import time
# import requests
# from pprint import pprint
# import re


# counter = 0

# subscription_key = "cc5ab8a32df6484981ec582e6669bd36"
# assert subscription_key


# text_analytics_base_url = "https://eastus2.api.cognitive.microsoft.com/text/analytics/v2.0"


# speech_key = "6fd6a1d3a05742f8bfaf9ffdccfffbb6"
# service_region = "westus"
# key_phrase_api_url = text_analytics_base_url + "/keyPhrases"
# senti_phrase_api_url = text_analytics_base_url + "/sentiment"

# speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

# # Set up the speech recognizer
# speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

# done = False

###############################################

# def stop_cb(evt):
#     #"""callback that stops continuous recognition upon receiving an event `evt`"""
#     print('CLOSING on {}'.format(evt))
#     speech_recognizer.stop_continuous_recognition()
#     done = True


###############################################

# speech_recognizer.recognizing.connect(lambda evt: print(evt.result.text))
# speech_recognizer.recognized.connect(lambda evt: analyze_speech(rec.join(evt.result.text)))
# speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
# speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
# speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
# # stop continuous recognition on either session stopped or canceled events
# speech_recognizer.session_stopped.connect(stop_cb)
# speech_recognizer.canceled.connect(stop_cb)
#################################################


# def sustain_speech():
#     print("sustain called")
#     speech_recognizer.start_continuous_recognition()
#     for i in range(105):
#         time.sleep(.5)
#     speech_recognizer.stop_continuous_recognition()





# @bp.route('/', methods=('GET', 'POST'))
# def index():
#     # row = get_db().execute(
#     #         'SELECT * FROM status WHERE id = (SELECT MAX(id) FROM status);'
#     #     ).fetchone()

#     """Show all the posts, most recent first."""

#     state = getattr(g, 'state', None)
#     if state is None:
#         g.state = 1


#     if request.method == 'POST':
#         print(request.form)
#         if 'phonedemo' in request.form:
#             g.state = 1
#         elif 'appdemo' in request.form:
#             g.state = 4
#         elif 'demo1.x' in request.form:
#             g.state = 2
#             @after_this_request
#             def after_fn():
#                 sustain_speech()
#         else:
#             g.state = 3
#         return render_template('blog/index.html')

#     # db = get_db()
#     # posts = db.execute(
#     #     'SELECT p.id, title, body, created, author_id, username'
#     #     ' FROM post p JOIN user u ON p.author_id = u.id'
#     #     ' ORDER BY created DESC'
#     # ).fetchall()
#     return render_template('blog/index.html')

    # if request.method == 'POST':
    #     print(request.form)
    #     if 'phonedemo' in request.form:
    #         g.state = 1
    #     elif 'appdemo' in request.form:
    #         g.state = 5
    #     elif 'demo1.x' in request.form:
    #         g.state = 2
    #     else:
    #         g.state = 3
    #     return render_template('blog/index.html')

    # db = get_db()
    # posts = db.execute(
    #     'SELECT p.id, title, body, created, author_id, username'
    #     ' FROM post p JOIN user u ON p.author_id = u.id'
    #     ' ORDER BY created DESC'
    # ).fetchall()
    # return render_template('blog/index.html')



def get_post(id, check_author=True):
    """Get a post and its author by id.
    Checks that the id exists and optionally that the current user is
    the author.
    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ? WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a post.
    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))


@bp.route('/register_beta', methods=('GET', 'POST'))
def register_beta():
    if request.method == 'POST':
        username = request.form['name']
        password = request.form['email']
        db = get_db()
        error = None

        # if not username:
        #     error = 'Username is required.'
        # elif not password:
        #     error = 'Password is required.'
        # elif db.execute(
        #     'SELECT id FROM user WHERE username = ?', (username,)
        # ).fetchone() is not None:
        #     error = 'User {} is already registered.'.format(username)

        # if error is None:
        #     db.execute(
        #         'INSERT INTO user (username, password) VALUES (?, ?)',
        #         (username, generate_password_hash(password))
        #     )
        #     db.commit()
        #     return redirect(url_for('auth.login'))

        # flash(error)

    return render_template('auth/register_beta.html')
