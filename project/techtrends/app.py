import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

import logging, sys
log = logging.getLogger()

# global to store absolute count of calls
connection_count = 0

# should be called every time an article is queried
def increase_call_count():
    global connection_count
    connection_count += 1

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    increase_call_count()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      log.info("Requested article with id "+ str(post_id) +" not found!")
      return render_template('404.html'), 404
    else:
      log.info('Article "'+ post['title'] +'" retrieved!')
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    log.info('"About us" was retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            log.debug('Failed to created record - "title" not provided')
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            log.info('Article "'+ title +'"')

            return redirect(url_for('index'))

    return render_template('create.html')

# Define the health check
@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    log.info("Health check was executed")
    return response

# Define the database connections metric
@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    connection.close
    response = app.response_class(
            response=json.dumps({"db_connection_count": connection_count,"post_count": post_count}),
            status=200,
            mimetype='application/json'
    )
    log.info("Metrics was retrieved")
    return response

# Setup logging properties
def init_logging():
    logging_format = "%(levelname)s: %(module)s: %(asctime)s, %(message)s"
    date_format = "%d/%m/%Y %H:%M:%S"
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=logging_format, datefmt=date_format)

# start the application on port 3111
if __name__ == "__main__":
   init_logging() 
   app.run(host='0.0.0.0', port='3111')
