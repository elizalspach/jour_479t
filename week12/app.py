# load libraries
from flask import Flask, jsonify, request
import pandas as pd
import os

# start app
app = Flask(__name__)

# load the NIL deals data once when the app starts
# source: CalMatters public records request — UCLA NIL transaction data 2022-2024
# https://github.com/CalMatters/data-nil-deals
nil_data = pd.read_csv('week12/data/nil_deals.csv')

# clean column names by stripping white space
nil_data.columns = [col.strip() for col in nil_data.columns]

# defining a function that converts a dataframe into a list of JSON dictionaries
def rows_to_json(df):
    """Convert a DataFrame to a list of dicts, handling NaN values."""
    return df.where(pd.notna(df), None).to_dict(orient='records')

"""
Below is the information for the root directory.
When we go to the root directory '/' there will be a landing page with all of the available endpoints as JSON.
Reminder that you have to run python week12/app.py in the terminal and ensure the app is running before you can actually access this endpoint.
"""
@app.route('/') # defines the URL endpoint: /
def index():
    return jsonify({
        'description': 'UCLA NCAA NIL Deals API (2022–2024)',
        'source': 'CalMatters public records request — https://github.com/CalMatters/data-nil-deals',
        'note': 'Athlete names are not included in this dataset to protect student privacy.',
        'endpoints': [
            {
                'path': '/api/deals',
                'method': 'GET',
                'description': 'Return all NIL deal records',
                'params': ['sport', 'deal_type', 'payment_type', 'year', 'min_value', 'max_value']
            },
            {
                'path': '/api/deals/search',
                'method': 'GET',
                'description': 'Search by brand/vendor name. Returns all records with case-insensitive partial matches.',
                'params': ['brand (required)']
            },
            {
                'path': '/api/deals/sports',
                'method': 'GET',
                'description': 'List all unique sports in the dataset.',
                'params': []
            },
            {
                'path': '/api/deals/top',
                'method': 'GET',
                'description': 'Top-N highest-value NIL deals.',
                'params': ['n (default: 10)']
            },
        ]
    })

"""
Endpoint 1: GET /api/deals
   Returns all records.
   Supports optional query parameters

   Examples of parameters:
     ?sport=Football
     ?deal_type=Endorsement
     ?payment_type=Cash
     ?year=2023
     ?min_value=10000
     ?max_value=100000
"""
@app.route('/api/deals') # defines the URL endpoint: /api/deals
def get_deals(): # function that runs when this endpoint is accessed
    # create a dataframe that is a copy of our nil_data dataframe, so we don't modify the original
    df = nil_data.copy()

    ## This is where we define our parameters

    # get the value of ?sport= from the URL (returns None if not provided)
    sport = request.args.get('sport')
    # get the value of ?deal_type= from the URL
    deal_type = request.args.get('deal_type')
    # get the value of ?payment_type= from the URL
    payment_type = request.args.get('payment_type')
    # get the value of ?year= and convert it to an integer
    year = request.args.get('year', type=int)
    # get the value of ?min_value= and convert it to a float
    min_value = request.args.get('min_value', type=float)
    # get the value of ?max_value= and convert it to a float
    max_value = request.args.get('max_value', type=float)

    # if a sport was provided in the URL
    if sport:
        # filter the dataframe to only include rows where sport matches (case-insensitive)
        df = df[df['sport'].str.lower() == sport.lower()]
    # if a deal type was provided,
    if deal_type:
        # filter rows where deal_type matches (case-insensitive)
        df = df[df['deal_type'].str.lower() == deal_type.lower()]
    # if a payment type was provided,
    if payment_type:
        # filter rows where payment_type matches (case-insensitive)
        df = df[df['payment_type'].str.lower() == payment_type.lower()]
    # if a year was provided,
    if year:
        # filter to only rows matching that year
        df = df[df['year'] == year]
    # if a minimum value was provided,
    if min_value is not None:
        # filter to only rows where deal_value is greater than or equal to min_value
        df = df[df['deal_value'] >= min_value]
    # if a maximum value was provided,
    if max_value is not None:
        # filter to only rows where deal_value is less than or equal to max_value
        df = df[df['deal_value'] <= max_value]

    # return the result after this filtering
    return jsonify({
        # return the total number of rows after filtering
        'count': len(df),
        # convert dataframe to JSON format using the rows_to_json() function we defined earlier
        'results': rows_to_json(df)
    })


"""
Endpoint 2: GET /api/deals/search?brand=

Brand parameter is required.
Example: GET /api/deals/search?brand=Nike

Case-insensitive partial-match search on the "brand" (Vendor Name) column
"""
@app.route('/api/deals/search') # defines the endpoint: /api/deals/search
def search_by_brand():  # function that runs when this endpoint is accessed

    ### Defining our brand parameter
    # get the value of ?brand= from the URL
    # if no brand is provided, default to an empty string ''
    brand = request.args.get('brand', '')
    # if the user did NOT provide a brand parameter,
    if not brand:
        # return an error message as JSON
        # 400 error means the client made a mistake
        ### This makes our brand parameter required
        return jsonify({'error': 'Provide a ?brand= query parameter'}), 400

    # create a filtered dataframe that looks at 'brand' to see if it contains
    # the string that the user specified in ?brand= in the URL
    # case=False makes it case-insensitive
    # na=False prevents errors if there are missing values
    df = nil_data[nil_data['brand'].str.contains(brand, case=False, na=False)]

    # return results as JSON
    return jsonify({
        # return count of total rows
        'count': len(df),
        # return the data as JSON
        'results': rows_to_json(df)
    })

"""
Endpoint 3: GET /api/deals/sports
Returns a list of all unique sports in the dataset.
No parameters
"""
@app.route('/api/deals/sports')
def get_sports():
    sports = sorted(nil_data['sport'].dropna().unique().tolist())
    return jsonify({'sports': sports})

"""
Endpoint 4: GET /api/deals/top?n=10

Returns the top N highest-value NIL deals. Default N is 10.
"""
@app.route('/api/deals/top')
def top_deals():
    ### Defining our parameter n
    # if there is something after ?n=, save it to the object n.
    # if there is nothing after ?n=, default to 10
    # ensure n is an integer
    n = request.args.get('n', default=10, type=int)
    # filter our nil data to the largest N deal values
    df = nil_data.nlargest(n, 'deal_value')

    # return as JSON
    return jsonify({
        'count': len(df), # give the count of rows (this should be same as N)
        'results': rows_to_json(df) # turn rows to json
    })


if __name__ == '__main__':
    # debug=True gives you auto-reload when you save the file
    # port=5000 tells Flask which port to run the server on
    # so you can access it at http://127.0.0.1:5000/
    app.run(debug=True, port=5000)
