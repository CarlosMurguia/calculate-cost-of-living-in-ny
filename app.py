import os
import pandas as pd
import numpy as np
import plotly
import plotly.plotly as py
import plotly.graph_objs as go

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, inspect

from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_url_path='/static')

#################################################
# Database Setup
#################################################

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db/data.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS "] = True


engine = create_engine("sqlite:///db/data.sqlite", echo = False)

db = SQLAlchemy(app)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(db.engine, reflect=True)

# Save references to each table
wages = Base.classes.wages
zillowRentData = Base.classes.rent


@app.route("/")
def index():
    """Return the homepage."""
    return render_template("index.html")

@app.route("/map")
def map():
    """Return the homepage."""
    return render_template("map.html")

# Returns json list of all professions from database
# Information is returned from title column of wages table
@app.route("/professions")
def professions():
    # Retrieve median income for profession from database
    stmt = db.session.query(wages).statement
    df = pd.read_sql_query(stmt, db.session.bind)
    print(df)
    # Create a dictionary
    data = {
        "professions": df["Title"].values.tolist()
    }
    return jsonify(data)


# Returns wages information in json format based on profession
# If profession is not found empty json object is returned
@app.route("/wages/<profession>")
def wages_profession(profession):
    print(profession)
    stmt = db.session.query(wages).statement
    df = pd.read_sql_query(stmt, db.session.bind)
    sample_data = df.loc[df['Title'] == profession, ["Title",
                                                     "Employment",
                                                     "Mean",
                                                     "Median",
                                                     "Entry",
                                                     "Experienced" ]]
    if sample_data.empty:
        return jsonify({})

    # Format the data to send as json
    data = {
        "Title": sample_data['Title'].values[0],
        "Employment": sample_data['Employment'].values[0],
        "Mean": sample_data['Mean'].values[0],
        "Median": sample_data['Median'].values[0],
        "Entry": sample_data['Entry'].values[0],
        "Experienced": sample_data['Experienced'].values[0]
    }
    return jsonify(data)

@app.route("/neighborhoods")
def neighborhoods_data():
    """Return all neighborhoods and mean rents for NYC"""
    sel = [
        zillowRentData.field2, #neighborhood
        zillowRentData.field3, #city
        zillowRentData.field4, #state
        zillowRentData.field101, #most recent mean rent
    ]
    nycNeighborhoods = db.session.query(*sel).filter(zillowRentData.field3 == "New York").all()
    
    print(nycNeighborhoods)
    return jsonify(nycNeighborhoods)


@app.route("/neighborhoods/<name>")
def hood_data(name):
    """Return mean rent for a neighborhood"""
    sel = [
        zillowRentData.field2, #neighborhood
        zillowRentData.field3, #city
        zillowRentData.field4, #state
        zillowRentData.field101, #most recent mean rent
    ]
    
    nycNeighborhoods = db.session.query(*sel).filter(zillowRentData.field3 == "New York").filter(zillowRentData.field2 == name).all()
    
    # create dictionary entry for each row of neighborhood info
    neighborhood_data = {}

    for result in nycNeighborhoods:
        neighborhood_data["Neighborhood"] = result[0]
        neighborhood_data["City"] = result[1]
        neighborhood_data["State"] = result[2]
        neighborhood_data["MeanRent"] = result[3]
    
    print(neighborhood_data)
    return jsonify(neighborhood_data)


if __name__ == "__main__":
    port = int(os.environ.get('PORT',5000))
    app.run(host='127.0.0.1', port=5000)