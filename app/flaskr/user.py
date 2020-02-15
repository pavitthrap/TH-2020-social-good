from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.db import get_db

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/profile', methods=('GET', 'POST'))
def user_profile():
	db = get_db()
	
	username = g.user["username"]
	user_type = "Seeker" # user['user_type']
	user_picture_filename = "user_icon_2.png" # user['user_picture_filename']

	return render_template('retina/user_profile.html', username=username, user_type=user_type,
							user_picture_filename=user_picture_filename)