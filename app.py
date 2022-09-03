#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import class_mapper, object_mapper
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
import collections
import logging
from logging import Formatter, FileHandler
from flask_wtf.csrf import CSRFProtect
from models import *
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

collections.Callable = collections.abc.Callable
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = 'secret'


# connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:alxadmin@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#Utils

def orm_obj_list_to_dict(obj_list):
       for u in obj_list:
        print ("\n" , u.__dict__ , "\n")

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    venues = Venue.query.order_by(db.desc(Venue.created_at)).limit(10).all()
    artists = Artist.query.order_by(db.desc(Artist.created_at)).limit(10).all()
    return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

# replace with real venues data.
@app.route('/venues')
def venues():
    data_areas = []

    # Get areas
    areas = Venue.query \
        .with_entities(Venue.city, Venue.state) \
        .group_by(Venue.city, Venue.state) \
        .all()

    # Iterate over each area
    for area in areas:
        data_venues = []

        # Get venues by area
        venues = Venue.query \
            .filter_by(state=area.state) \
            .filter_by(city=area.city) \
            .all()

        # Iterate over each venue
        for venue in venues:
            # Get upcoming shows by venue
            upcoming_shows = db.session \
                    .query(Show) \
                    .join(Venue) \
                    .filter(Show.venue_id == venue.id) \
                    .filter(Show.start_time > datetime.now()) \
                    .all()

            # Map venues
            data_venues.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows)
            })

        # Map areas
        data_areas.append({
            'city': area.city,
            'state': area.state,
            'venues': data_venues
        })

    return render_template('pages/venues.html', areas=data_areas)




# Search Venue


# implement search on artists with partial string search. Ensure it is case-insensitive.
# search for Hop should return "The Musical Hop".
# search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get("search_term", "")

    response = {}
    venues = list(Venue.query.filter(
        Venue.name.ilike(f"%{search_term}%") |
        Venue.state.ilike(f"%{search_term}%") |
        Venue.city.ilike(f"%{search_term}%") 
    ).all())
    response["count"] = len(venues)
    response["data"] = []

    for venue in venues:
        venue_unit = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(list(filter(lambda x: x.start_time > datetime.now(), venue.shows)))
        }
        response["data"].append(venue_unit)

    return render_template('pages/search_venues.html', results=response, search_term=search_term)

    if request.method == 'POST':
        return {
            'token': request.form.get('csrf_token')
        }

   
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Get venue
    data_venue = Venue.query.filter(Venue.id == venue_id).first()

    # Get the upcoming shows of this venue
    upcoming_shows = Show.query \
        .filter(Show.venue_id == venue_id) \
        .filter(Show.start_time > datetime.now()) \
        .all()

    if len(upcoming_shows) > 0:
        data_upcoming_shows = []

        # Iterate over each upcoming show
        for upcoming_show in upcoming_shows:
            artist = Artist.query \
                .filter(Artist.id == upcoming_show.artist_id) \
                .first()

            # Map upcoming shows
            data_upcoming_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': str(upcoming_show.start_time),
            })

        # Add shows data
        data_venue.upcoming_shows = data_upcoming_shows
        data_venue.upcoming_shows_count = len(data_upcoming_shows)

    # Get the past shows of this venue
    past_shows = Show.query \
        .filter(Show.venue_id == venue_id) \
        .filter(Show.start_time < datetime.now()) \
        .all()

    if len(past_shows) > 0:
        data_past_shows = []

        # Iterate over each past show
        for past_show in past_shows:
            artist = Artist.query \
                .filter(Artist.id == past_show.artist_id) \
                .first()

            # Map past shows
            data_past_shows.append({
                'artist_id': artist.id,
                'artist_name': artist.name,
                'artist_image_link': artist.image_link,
                'start_time': str(past_show.start_time),
            })

        # Add shows data
        data_venue.past_shows = data_past_shows
        data_venue.past_shows_count = len(data_past_shows)

    return render_template('pages/show_venue.html', venue=data_venue)
 
 

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  #insert form data as a new Venue record in the db, instead
 
    form = VenueForm(request.form)
    if form.validate():
        try:
            new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=",".join(form.genres.data), # convert array to string separated by commas
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website_link=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data                
            )
            db.session.add(new_venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!') # on successful db insert, flash success
            
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/           
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

        finally:
            db.session.close()
    else:
            print("\n\n", form.errors)           
    return render_template('pages/home.html')
    
    if request.method == 'POST':
        return {
            'token': request.form.get('csrf_token')
        }


# Delete Venue

# Complete this endpoint for taking a venue_id, and using
# SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

@app.route('/venues/<venue_id>/delete', methods={'GET'})
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was deleted successfully!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash('Venue was not deleted successfully.')
    finally:
        db.session.close()
    return redirect(url_for('pages/home.html'))


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  #return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(
        Artist.name.ilike(f"%{search_term}%") |
        Artist.city.ilike(f"%{search_term}%") |
        Artist.state.ilike(f"%{search_term}%")
    ).all()
    response = {
        "count": len(artists),
        "data": []
    }

    for artist in artists:
        temp = {}
        temp["name"] = artist.name
        temp["id"] = artist.id

        upcoming_shows = 0
        for show in artist.shows:
            if show.start_time > datetime.now():
                upcoming_shows = upcoming_shows + 1
        temp["upcoming_shows"] = upcoming_shows

        response["data"].append(temp)

    return render_template('pages/search_artists.html', results=response, search_term=search_term)

    if request.method == 'POST':
        return {
            'token': request.form.get('csrf_token')
        }


@app.route('/artists')
def artists():
    data_artists = []

    # Get artists
    artists = Artist.query \
        .with_entities(Artist.id, Artist.name) \
        .order_by('id') \
        .all()

    # Iterate over each artist
    for artist in artists:
        # Get upcoming shows
        upcoming_shows = db.session \
                .query(Show) \
                .join(Artist) \
                .filter(Show.artist_id == artist.id) \
                .filter(Show.start_time > datetime.now()) \
                .all()

        # Map artists
        data_artists.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows)
        })

    return render_template('pages/artists.html', artists=data_artists)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Get artist
    data_artist = Artist.query.filter(Artist.id == artist_id).first()

    # Get the upcoming shows of this artist
    upcoming_shows = Show.query \
        .filter(Show.artist_id == artist_id) \
        .filter(Show.start_time > datetime.now()) \
        .all()

    if len(upcoming_shows) > 0:
        data_upcoming_shows = []

        # Iterate over each upcoming show
        for upcoming_show in upcoming_shows:
            venue = Venue.query \
                .filter(Venue.id == upcoming_show.venue_id) \
                .first()

            # Map upcoming shows
            data_upcoming_shows.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(upcoming_show.start_time),
            })

        # Add shows data
        data_artist.upcoming_shows = data_upcoming_shows
        data_artist.upcoming_shows_count = len(data_upcoming_shows)

    # Get the past shows of this venue
    past_shows = Show.query \
        .filter(Show.artist_id == artist_id) \
        .filter(Show.start_time < datetime.now()) \
        .all()

    if len(past_shows) > 0:
        data_past_shows = []

        # Iterate over each past show
        for past_show in past_shows:
            venue = Venue.query \
                .filter(Venue.id == upcoming_show.venue_id) \
                .first()

            # Map past shows
            data_past_shows.append({
                'venue_id': venue.id,
                'venue_name': venue.name,
                'venue_image_link': venue.image_link,
                'start_time': str(past_show.start_time),
            })

        # Add shows data
        data_artist.past_shows = data_past_shows
        data_artist.past_shows_count = len(data_past_shows)

    return render_template('pages/show_artist.html', artist=data_artist)
  # shows the artist page with the given artist_id
  # replace with real artist data from the artist table, using artist_id


#  Update Artist
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()  
    artist = Artist.query.get(artist_id)
    form.genres.data = artist.genres.split(",") # convert genre string back to array
    
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)

    if form.validate():
        try:
            artist = Artist.query.get(artist_id)

            artist.name = form.name.data
            artist.city=form.city.data
            artist.state=form.state.data
            artist.phone=form.phone.data
            artist.genres=",".join(form.genres.data) # convert array to string separated by commas
            artist.facebook_link=form.facebook_link.data
            artist.image_link=form.image_link.data
            artist.seeking_venue=form.seeking_venue.data
            artist.seeking_description=form.seeking_description.data
            artist.website_link=form.website_link.data

            db.session.add(artist)
            db.session.commit()
            flash("Artist " + artist.name + " was successfully edited!")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash("Artist was not edited successfully.")
        finally:
            db.session.close()
    else:
        print("\n\n", form.errors)
        flash("Artist was not edited successfully.")

    return redirect(url_for('show_artist', artist_id=artist_id))





#  Update Venue


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.genres.data = venue.genres.split(",") # convert genre string back to array
    
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    
    if form.validate():
        try:
            venue = Venue.query.get(venue_id)

            venue.name = form.name.data
            venue.city=form.city.data
            venue.state=form.state.data
            venue.address=form.address.data
            venue.phone=form.phone.data
            venue.genres=",".join(form.genres.data) # convert array to string separated by commas
            venue.facebook_link=form.facebook_link.data
            venue.image_link=form.image_link.data
            venue.seeking_talent=form.seeking_talent.data
            venue.seeking_description=form.seeking_description.data
            venue.website_link=form.website_link.data

            db.session.add(venue)
            db.session.commit()

            flash("Venue " + form.name.data + " edited successfully")
            
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
            flash("Venue was not edited successfully.")
        finally:
            db.session.close()
    else: 
        print("\n\n", form.errors)
        flash("Venue was not edited successfully.")

    return redirect(url_for('show_venue', venue_id=venue_id))

  # take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
 # return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  # insert form data as a new Venue record in the db, instead
  if form.validate():
      try:
          new_artist = Artist(
               name=form.name.data,
               city=form.city.data,
               state=form.state.data,
               phone=form.phone.data,
               genres=",".join(form.genres.data), # convert array to string separated by commas
               image_link=form.image_link.data,
               facebook_link=form.facebook_link.data,
               website_link=form.website_link.data,
               seeking_venue=form.seeking_venue.data,
               seeking_description=form.seeking_description.data
          )
          db.session.add(new_artist) # called upon submitting the new artist listing form
          db.session.commit()
          flash('Artist ' + request.form['name'] + ' was successfully listed!') # on successful db insert, flash success
        
      # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
      except:
            error = True
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.') # on unsuccessful db insert, flash an error instead.
      finally:
            db.session.close()
  else:
        print(form.errors)
  return render_template('pages/home.html')

  if request.method == 'POST':
        return {
            'token': request.form.get('csrf_token')
        }  
  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.order_by(db.desc(Show.start_time))

  data = []

  for show in shows:
    data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
    })

  return render_template('pages/shows.html', shows=data)
  
  
  
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    show = Show(artist_id=request.form['artist_id'], venue_id=request.form['venue_id'],
                start_time=request.form['start_time'])

    db.session.add(show)
    db.session.commit()

    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    flash('Show could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

  if request.method == 'POST':
        return {
            'token': request.form.get('csrf_token')
        }  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
