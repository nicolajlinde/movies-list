from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, InputRequired
from dotenv import load_dotenv
import requests
import os
from pprint import pprint

load_dotenv()
TMDB_KEY = os.getenv('TMDB_KEY')

app = Flask(__name__)
# Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new-books-collection.db'
db = SQLAlchemy(app)

# Bootstrap
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer(), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    rating = db.Column(db.Float(), nullable=False)
    ranking = db.Column(db.Integer(), nullable=False)
    review = db.Column(db.String(80), nullable=False)
    img_url = db.Column(db.String(80), nullable=False)


db.create_all()


class RateMovieForm(FlaskForm):
    rating = FloatField('Your rating out of 10 e.g. 7.5', validators=[DataRequired(), NumberRange(min=0, max=10)])
    review = TextAreaField('Your review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddMovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/')
def index():  # put application's code here
    # This line creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/add', methods=['POST', 'GET'])
def add():
    form = AddMovieForm()
    if request.method == 'POST' and form.validate_on_submit():
        url = 'https://api.themoviedb.org/3/search/movie'
        movie_title = request.form['title']
        params = {
            'api_key': TMDB_KEY,
            'query': movie_title
        }
        response = requests.get(url=url, params=params)
        response.raise_for_status()
        data = response.json()['results']
        return render_template('select.html', data=data)

    return render_template('add.html', form=form)


@app.route('/add/movie/<int:id>')
def select(id):
    url = f'https://api.themoviedb.org/3/movie/{id}'
    params = {
        'api_key': TMDB_KEY,
    }
    response = requests.get(url=url, params=params)
    response.raise_for_status()
    data = response.json()
    new_movie = Movie(
        title=data['title'],
        year=data['release_date'],
        description=data['overview'],
        rating=round(data['vote_average'], 1),
        img_url=f"https://image.tmdb.org/t/p/original/{data['poster_path']}",
        ranking='None',
        review='None'
    )
    db.session.add(new_movie)
    db.session.commit()
    movie = Movie.query.filter_by(title=data['title']).first()
    return redirect(url_for('edit', id=movie.id))


@app.route('/edit/<int:id>', methods=['POST', 'GET'])
def edit(id):
    movie = Movie.query.filter_by(id=id).first()
    movie_form = {'rating': movie.rating, 'review': movie.review}
    form = RateMovieForm(data=movie_form)
    if request.method == 'POST' and form.validate_on_submit():
        movie.rating = request.form['rating']
        movie.review = request.form['review']

        db.session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('edit.html', movie=movie, form=form)


@app.route('/delete/<int:id>')
def delete(id):
    movie = Movie.query.get(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
