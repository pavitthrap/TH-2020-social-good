from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.db import get_db

bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/profile', methods=('GET', 'POST'))
def user_profile():
	db = get_db()
	
	username = g.user["username"]
	user_type = "Seeker" if g.user['user_type']==0 else "Answerer"
	print(g.user['profile_pic_filename'] )
	profile_pic_filename = "user_icon_2.png" if g.user['profile_pic_filename'] == None else g.user['profile_pic_filename']

	return render_template('retina/user_profile.html', username=username, user_type=user_type,
							user_picture_filename=profile_pic_filename)