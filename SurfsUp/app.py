# Import the dependencies.
from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
import numpy as np
import pandas as pd
import sqlite3


#################################################
# Database Setup
#################################################


# Create an engine to the SQLite database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(autoload_with=engine)

# Print out the available classes to see what tables are available
print("Available classes:", Base.classes.keys())

# Check if the expected tables are available
if 'measurement' in Base.classes.keys() and 'station' in Base.classes.keys():
    # Save references to each table
    Measurement = Base.classes.measurement
    Station = Base.classes.station
else:
    raise Exception("Expected tables 'measurement' and 'station' not found in the database.")

# Create our session (link) from Python to the DB
session = Session(engine)

# Additional check to list all tables in the database
def list_tables():
    conn = sqlite3.connect("hawaii.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(table[0])
    conn.close()

list_tables()


#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    return (
        f"Welcome to Holly's Climate Analysis API! Because who goes on vacation without one?!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/temp/start/end"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year from the last date in data set.
    prev_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    # Query for the date and precipitation for the last year
    precipitation = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= prev_year).all()

    # Create a dictionary with the date as the key and the precipitation as the value
    precip = {date: prcp for date, prcp in precipitation}
    return jsonify(precip)

@app.route("/api/v1.0/stations")
def stations():
    # Create a query that will allow us to get all of the stations in our database
    stations = session.query(Station.station).all()
    # Unravel results into a one-dimensional array and convert to a list
    stations = list(np.ravel(stations))
    return jsonify(stations=stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    one_year_ago = dt.datetime.strptime(last_date, "%Y-%m-%d") - dt.timedelta(days=365)

    # Perform a query to retrieve the temperature observations for the most active station
    most_active_station = session.query(Measurement.station).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    tobs_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago).all()

    # Convert the query results to a list
    tobs_list = list(np.ravel(tobs_data))

    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    # Select statement
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    if not end:
        # Calculate TMIN, TAVG, TMAX for dates greater than or equal to the start date
        start=dt.datetime.strptime(start, "%m%d%Y")
        results = session.query(*sel).filter(Measurement.date >= start).all()
    else:
        # Calculate TMIN, TAVG, TMAX for dates between the start and end date inclusive
        start=dt.datetime.strptime(start, "%m%d%Y")
        end=dt.datetime.strptime(end, "%m%d%Y")
        results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    # Convert the query results to a list
    temperature_stats_list = list(np.ravel(results))

    return jsonify(temperature_stats_list)

if __name__ == '__main__':
    app.run(debug=True)