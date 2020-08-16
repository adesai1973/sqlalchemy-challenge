import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect

from flask import Flask, jsonify, request

def toDate(dateString): 
    return dt.datetime.strptime(dateString, "%Y-%m-%d").date()

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

print(Base.classes.keys())

# Save reference to the table
# Assign the measurement class to a variable called `Measurement`
Measurement = Base.classes.measurement

# Assign the station class to a variable called `Station`
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/YYYY-MM-DD (trip start date - enter any date before 2017-08-23)<br/>"
        f"/api/v1.0/YYYY-MM-DD (trip start date)/YYYY-MM-DD (trip end date)<br/>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all dates and precipitations"""
    # Query all passengers
    results = session.query(Measurement.date, Measurement.prcp).order_by(Measurement.date.desc()).all()

    session.close()

    # Convert list of tuples into normal list
    prcp_list = list(np.ravel(results))
    print(len(prcp_list))
    # Create a dictionary from normal list
    all_prcp = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["prcp"] = prcp
        all_prcp.append(prcp_dict)

    return jsonify(all_prcp)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all stations"""
    # Query all stations
    results = session.query(Measurement.station, func.avg(Measurement.tobs))\
                        .group_by(Measurement.station)\
                        .order_by(Measurement.station).all()

    session.close()

    # Convert list of tuples into normal list
    stations = list(np.ravel(results))

    # Create a dictionary from normal list
    all_stations = []
    for station, avg_temp in stations:
        stations_dict = {}
        stations_dict["station"] = station
        all_stations.append(stations_dict)

    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    results_last_date = session.query(Measurement.date, Measurement.prcp)\
                    .order_by(Measurement.date.desc()).first()
    last_date = pd.to_datetime(results_last_date[0])
    print(last_date)

    # date 1 year ago from last_date
    first_date = last_date - dt.timedelta(days=365)
    print(first_date)

    last_date = last_date.date()
    first_date = first_date.date()

    """Return a list of all stations organized by descending order of activity"""
    sel = [Measurement.station, 
       func.count(Measurement.tobs),
       func.min(Measurement.tobs), 
       func.max(Measurement.tobs), 
       func.avg(Measurement.tobs)]

    stations_list_stats = session.query(*sel)\
                        .group_by(Measurement.station)\
                        .order_by(func.count(Measurement.tobs).desc()).all()
    most_active_station = stations_list_stats[0][0]
    # Query TOBS for most active station
    results = session.query(Measurement.station, Measurement.date, Measurement.tobs)\
                        .filter(Measurement.station == most_active_station)\
                        .filter(Measurement.date.between(first_date, last_date)).all()

    session.close()

    # Convert list of tuples into normal list
    tobs_top_station = list(np.ravel(results))

    # Create a dictionary from normal list
    all_tobs = []
    for station, date, tobs in results:
        tobs_dict = {}
        tobs_dict["station"] = station
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)

@app.route("/api/v1.0/<start>", methods=['GET'])
def date_start(start):

    # Create our session (link) from Python to the DB
    session = Session(engine)
    #start_date = request.args.get('start', default = dt.date.today(), type = toDate)
    #end_date = request.args.get('end', type = toDate)
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    results_last_date = session.query(Measurement.date, Measurement.prcp)\
                    .order_by(Measurement.date.desc()).first()
    #end_date = pd.to_datetime(results_last_date[0])
    end_date = datetime.strptime(str(results_last_date[0]), "%Y-%m-%d").date()
    print("*******************************")
    print(start_date)
    print(end_date)


    """Return stats of tobs"""
    # Query all passengers
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

    session.close()

    # Convert list of tuples into normal list
    temp_stats = list(np.ravel(results))
    print(temp_stats)
    # Create a dictionary from normal list
    all_trip = []
    for tmin, tavg, tmax in results:
        trip_dict = {}
        trip_dict["tmin"] = tmin
        trip_dict["tavg"] = tavg
        trip_dict["tmax"] = tmax
        all_trip.append(trip_dict)

    return jsonify(all_trip)


@app.route("/api/v1.0/<start>/<end>", methods=['GET'])
def date_start_end(start, end):

    #start_date = request.args.get('start', default = dt.date.today(), type = toDate)
    #end_date = request.args.get('end', type = toDate)
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    print("*******************************")
    print(start_date)
    print(end_date)
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return stats of tobs"""
    # Query all passengers
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

    session.close()

    # Convert list of tuples into normal list
    temp_stats = list(np.ravel(results))
    print(temp_stats)
    # Create a dictionary from normal list
    all_trip = []
    for tmin, tavg, tmax in results:
        trip_dict = {}
        trip_dict["tmin"] = tmin
        trip_dict["tavg"] = tavg
        trip_dict["tmax"] = tmax
        all_trip.append(trip_dict)

    return jsonify(all_trip)


if __name__ == '__main__':
    app.run(debug=True)
