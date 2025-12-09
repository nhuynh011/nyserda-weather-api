import json, time, os, re, requests
from flask import Flask,request, redirect, render_template
import pandas as pandas, glob
from math import radians, degrees, sin, cos, sqrt, atan2

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options  

import openmeteo_requests
import requests_cache
from retry_requests import retry

[os.remove(f'./data/{f}') for f in os.listdir('./data')]

def geographic_centroid(coordinates):
    x_sum = 0
    y_sum = 0
    z_sum = 0
    
    for lat, lon in coordinates:
        # Convert to radians
        lat_rad = radians(lat)
        lon_rad = radians(lon)
        
        # Convert to Cartesian coordinates
        x = cos(lat_rad) * cos(lon_rad)
        y = cos(lat_rad) * sin(lon_rad)
        z = sin(lat_rad)
        
        x_sum += x
        y_sum += y
        z_sum += z
    
    # Average the Cartesian coordinates
    x_avg = x_sum / len(coordinates)
    y_avg = y_sum / len(coordinates)
    z_avg = z_sum / len(coordinates)
    
    # Convert back to geographic coordinates
    lon_center = atan2(y_avg, x_avg)
    hyp = sqrt(x_avg**2 + y_avg**2)
    lat_center = atan2(z_avg, hyp)
    
    # Convert to degrees
    center_lat = degrees(lat_center)
    center_lon = degrees(lon_center)
    
    return center_lat, center_lon

def haversineDistance(farmLon, farmLat, desiredLon, desiredLat, mode):
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert decimal degrees to radians
    lat1_rad = radians(farmLat)
    lon1_rad = radians(farmLon)
    lat2_rad = radians(desiredLat)
    lon2_rad = radians(desiredLon)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    if mode == "km":
        return R * c
    elif mode == "mp": #midpoint   
        # Calculate midpoint coordinates
        bx = cos(lat2_rad) * cos(dlon)
        by = cos(lat2_rad) * sin(dlon)
        
        lat_mid = atan2(
            sin(lat1_rad) + sin(lat2_rad),
            sqrt((cos(lat1_rad) + bx)**2 + by**2)
        )
        lon_mid = lon1_rad + atan2(by, cos(lat1_rad) + bx)
        
        # Convert back to degrees
        mid_lat = degrees(lat_mid)
        mid_lon = degrees(lon_mid)
        
        # Normalize longitude to [-180, 180]
        mid_lon = (mid_lon + 540) % 360 - 180
        return (mid_lat, mid_lon)

def retrieveNyserda(farmName):
    options = Options()

    # Set download preferences
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", os.path.abspath("./data"))
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/vnd.ms-excel")

    # For CSV files specifically
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/csv,text/comma-separated-values")

    driver = webdriver.Firefox(options=options)

    location = farmName

    # Look up facility id:
    # https://der.nyserda.ny.gov/api/advsearch/f/?limit=12&name=Lodestar%20Energy%20-%20170%20Buck%20Rd&category=&subcategory=&esstype=&pwrcapmin=&pwrcapmax=&elecutil=&gasutil=&nyiso=&address=&cityzip=&vendor=&sort-by=name
    driver.get("https://der.nyserda.ny.gov/search/")

    textbox = driver.find_element(By.ID, "input-facility-name")
    textbox.send_keys(location)
    textbox.send_keys(Keys.ENTER)
    time.sleep(2) # needed for dynamic update
    driver.find_element(By.CLASS_NAME, "view-button").click()
    # Get the facility id: I don't think I can do this because of dynamic webpage elements
    # https://der.nyserda.ny.gov/facilities/

    url = driver.current_url

    #id = current_url.split('https://der.nyserda.ny.gov/facilities/')[-1]
    #print(current_url)

    driver.find_element(By.CLASS_NAME, "img-graph").click()

    # Now pull the data:

    try:
        img_element = driver.find_element(By.CSS_SELECTOR, "img.img-solar[title='Solar PV']")
        img_element.find_element(By.XPATH, "..").click()  # Get parent element
        time.sleep(5)
        driver.find_element(By.ID, "download-data-tab").click()
        time.sleep(2)
        driver.find_element(By.CSS_SELECTOR, "label[for='download-data-control-tstep-hour']").click()
        driver.find_element(By.CSS_SELECTOR, "button[title*='Download all performance data']").click()
    except Exception as e:
        print(f"Data not availible for this solar farm. Check {url}.")
        print(e)

def retrieveWeather(longitude, latitude, startDate, endDate):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
      "latitude": latitude,
      "longitude": longitude,
      "start_date": startDate,
      "end_date": endDate,
      "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high", "wind_speed_10m", "shortwave_radiation", "direct_radiation", "diffuse_radiation", "direct_normal_irradiance", "global_tilted_irradiance"],
      "timezone": "America/New_York",

      }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(3).ValuesAsNumpy()
    hourly_cloud_cover_low = hourly.Variables(4).ValuesAsNumpy()
    hourly_cloud_cover_mid = hourly.Variables(5).ValuesAsNumpy()
    hourly_cloud_cover_high = hourly.Variables(6).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(7).ValuesAsNumpy()
    hourly_shortwave_radiation = hourly.Variables(8).ValuesAsNumpy()
    hourly_direct_radiation = hourly.Variables(9).ValuesAsNumpy()
    hourly_diffuse_radiation = hourly.Variables(10).ValuesAsNumpy()
    hourly_direct_normal_irradiance = hourly.Variables(11).ValuesAsNumpy()
    hourly_global_tilted_irradiance = hourly.Variables(12).ValuesAsNumpy()

    hourly_data = {"date": pandas.date_range(
      start = pandas.to_datetime(hourly.Time(), unit = "s", utc = True),
      end =  pandas.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
      freq = pandas.Timedelta(seconds = hourly.Interval()),
      inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["cloud_cover"] = hourly_cloud_cover
    hourly_data["cloud_cover_low"] = hourly_cloud_cover_low
    hourly_data["cloud_cover_mid"] = hourly_cloud_cover_mid
    hourly_data["cloud_cover_high"] = hourly_cloud_cover_high
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["shortwave_radiation"] = hourly_shortwave_radiation
    hourly_data["direct_radiation"] = hourly_direct_radiation
    hourly_data["diffuse_radiation"] = hourly_diffuse_radiation
    hourly_data["direct_normal_irradiance"] = hourly_direct_normal_irradiance
    hourly_data["global_tilted_irradiance"] = hourly_global_tilted_irradiance

    hourly_dataframe = pandas.DataFrame(data = hourly_data)
    return hourly_dataframe

app = Flask(__name__, 
            template_folder='./templates')

# import coordinates csv
lookup = pandas.read_csv("./solarFarmNyserda.csv")

lookup = lookup.drop(columns=['image'])

@app.route("/", methods=['GET'])
def root():
    # Give some documentation, brief discussion of what this api does and what it's for.
    api_info = {
        "name": "Data Processing API",
        "version": "1.0.0",
        "description": "An API for processing and analyzing data",
        "endpoints": [
            {"path": "/", "methods": ["GET"], "desc": "This documentation page"},
            {"path": "/searchFarms", "methods": ["GET", "POST"], "desc": "Get a list of solar farms's name and coordinates within a certain capacity range and/or location range."},
            {"path": "/getFarm", "methods": ["GET", "POST"], "desc": "Get data for one solar farm with or without weather data."},
            {"path": "/getFarms", "methods": ["GET", "POST"], "desc": "Get data for multiple solar farms with or without weather data."}
        ],
        "examples": {
            "curl": "curl -X GET http://localhost:5000/api",
            "python": "import requests\nresponse = requests.get('http://localhost:5000/')"
        }
    }
    
    # Render HTML template with data
    return render_template('index.html', **api_info)

@app.route("/searchFarms", methods=['GET', 'POST'])
def search():
    response = {}
    response['request'] = 'searchFarms'

    try:
        lat = float(request.args.get('latitude'))
        lon =  float(request.args.get('longitude'))
        distance = float(request.args.get('radius_km'))
    except (TypeError, ValueError):
        response['status'] = 400
        response['error'] = f'Missing or invalid required parameters (latitude, longitude, radius_km)'
        return response

    try:
        mincap = float(request.args.get('capacity_min', 0))
    except (TypeError, ValueError):
        mincap = 0
    
    try:
        maxcap = float(request.args.get('capacity_max', float('inf')))
    except (TypeError, ValueError):
        maxcap = float('inf')
    
    response['capacity_min'] = mincap if mincap > 0 else "None given"
    response['capacity_max'] = maxcap if maxcap != float('inf') else "None given"

# Process request: lookup
    # i'm just gonna include it in the csv.
    response['farms'] = []
    for _, row in lookup.iterrows():
        # Skip farms without coordinates
        if pandas.isna(row['longitude']) or pandas.isna(row['latitude']):
            continue
            
        lonFarm = float(row['longitude'])
        latFarm = float(row['latitude'])
        capacity = float(row['gencapacity (kW)'])
        
        # Check if within distance
        dis = haversineDistance(lonFarm, latFarm, lon, lat, "km")
        
        if dis <= distance:
            # Check capacity range
            if mincap <= capacity <= maxcap:
                farm_data = {
                    'name': row['locationName'],
                    'longitude': float(row['longitude']),
                    'latitude': float(row['latitude']),
                    'capacity_kw': float(row['gencapacity (kW)']),
                }
                response['farms'].append(farm_data)
    response['status'] = 200
    return json.dumps(response,indent='   ')

@app.route("/getFarm", methods=['GET', 'POST'])
def get_farm():
    # run function:
    response = {}
    response ['request'] = 'getFarm'
    # get params:
    name = request.args.get('farm_name')
    weather = request.args.get('include_weather')
    if weather != "true" and weather != "false":
        response['status'] = 400
        response['message'] = f"No weather option provided. Please provide true or false for weather: http://localhost:5000/getFarm?farm_name=103 Sparling Road, LLC&include_weather=true"
        return json.dumps(response,indent='   ')
    
    if name is None:
        response['status'] = 400
        response['message'] = f"No solar farm provided. Please call the api again with a solar farm name: http://localhost:5000/getFarm?farm_name=103 Sparling Road, LLC&include_weather=true"
        return json.dumps(response,indent='   ')

    # get farm first:
    retrieveNyserda(name) # saves into ./data

    df = pandas.read_csv(glob.glob('./data/*.csv')[0])
    df = df.iloc[1:]
    df['datetime'] = pandas.to_datetime(df['Date'] + ' ' + df['Hour (Eastern Time, Daylight-Adjusted)'].astype(str) + ':00:00')
    # keep only elec generated, datetime, date, and hour:
    required_columns = ['datetime', 'Date', 'Hour (Eastern Time, Daylight-Adjusted)', 'Electricity Generated']
    df = df[required_columns]
    df = df.rename(columns={
        'Electricity Generated': name
    })
    # pull weather from open meteo:
    
    if weather == "true":
        startDate = min(df['datetime'])
        endDate = min(max(df['datetime']), pandas.Timestamp.today())

        # change back to proper datetime format for openmeteo: YYYY-MM-DD
        startDate = startDate.strftime('%Y-%m-%d')
        endDate = endDate.strftime('%Y-%m-%d')

        # check this later
        lat = lookup.loc[lookup['locationName'] == name, 'latitude'].iloc[0]
        lon = lookup.loc[lookup['locationName'] == name, 'longitude'].iloc[0]

        # pull open meteo
        dfW = retrieveWeather(lon, lat, startDate, endDate)
        dfW['date'] = pandas.to_datetime(dfW['date']).dt.tz_localize(None)
        # join

        mask = dfW['date'] >= pandas.to_datetime(startDate)  # Find rows from startDate onwards
        if mask.any():
            idx = mask.idxmax()  # Get first True index
            dfW = dfW.iloc[idx+1:]  # Slice from that index
        else:
            response['status'] = 400
            response['message'] = f"No weather data available from {startDate}"
            return json.dumps(response,indent='   ')


        dfW_temp = dfW.reset_index(drop=True).copy()
        dfW_temp.to_csv("weather.csv")
        # Perform left join
        dfW_truncated = dfW.iloc[:len(df)].reset_index(drop=True)
        df_merged = pandas.concat([df.reset_index(drop=True), dfW_truncated], axis=1)
                
        response['status'] = 200
        response['message'] = "Data retrieved successfully with weather"
        df_merged.to_csv("export.csv")
        return json.dumps(response,indent='   ')

    elif weather == "false":
        response['status'] = 200
        response['message'] = "Data has been saved to ./data"
        df.to_csv("export.csv")
    else:
        response['status'] = 400
        response['message'] = "Weather options are not true or false. Please call the API again."
    return json.dumps(response,indent='   ')


@app.route("/getFarms", methods=['GET', 'POST'])
def get_farms():
    response = {}
    response['request'] = 'getFarm'
    # get params:
    farm_names_param = request.args.get('farm_name', '')
    weather = request.args.get('include_weather')

    # Split farm names by semicolon
    name = [name.strip() for name in farm_names_param.split(';') if name.strip()]
    
    if weather != "true" and weather != "false":
        response['status'] = 400
        response['message'] = f"No weather option provided. Please provide true or false for weather: http://localhost:5000/getFarm?farm_name=103 Sparling Road, LLC&include_weather=true"
        return json.dumps(response,indent='   ')
    
    if name is None:
        response['status'] = 400
        response['message'] = f"No solar farm provided. Please call the api again with a solar farm name: http://localhost:5000/getFarm?farm_name=103 Sparling Road, LLC&include_weather=true"
        return json.dumps(response,indent='   ')

    # Retrieve data for each farm
    coords = []
    for farm_name in name:
        retrieveNyserda(farm_name)  # saves into ./data
        # get lonlats
        lat = lookup.loc[lookup['locationName'] == farm_name, 'latitude'].iloc[0]
        lon = lookup.loc[lookup['locationName'] == farm_name, 'longitude'].iloc[0]
        coords.append((lat, lon))
        print(f"Retrieved: {farm_name}")
    time.sleep(5)
    # Now process all CSV files
    csv_files = glob.glob('./data/*.csv')

    if len(csv_files) != len(name):
        print(f"Warning: Found {len(csv_files)} CSV files but expected {len(name)} farms")
    save = []
    start = []
    end = []
    for i, csv_file in enumerate(csv_files):
        print(f"Processing: {csv_file}")
        df = pandas.read_csv(csv_file)
        df = df.iloc[1:]
        df['datetime'] = pandas.to_datetime(df['Date'] + ' ' + df['Hour (Eastern Time, Daylight-Adjusted)'].astype(str) + ':00:00')
        df = df.rename(columns={'Electricity Generated': name[i]})
        # get max start date:
        start.append(df['datetime'].min())
        end.append(df['datetime'].max())
        save.append(df[['datetime', name[i]]])
    common_start, common_end = None, None 
    # get common start date:
    if start and end:
        common_start = max(start)
        common_end = min(end)
    else:
        response['status'] = 400
        response['message'] = "No data found in CSV files"
        return json.dumps(response, indent='   ')
    filtered_dfs = []
    for df in save:
        mask = (df['datetime'] >= common_start) & (df['datetime'] <= common_end)
        filtered_df = df[mask].copy()
        filtered_dfs.append(filtered_df)

    # calculate lon lat:
    lat, lon = geographic_centroid(coords)

    # Merge all DataFrames on datetime
    merged_df = filtered_dfs[0]  # Start with first DataFrame

    for df in filtered_dfs[1:]:
        merged_df = pandas.merge(merged_df, df, on='datetime', how='inner')
    df = merged_df
    # pull weather from open meteo:
    if weather == "true":
        startDate = min(df['datetime'])
        endDate = min(max(df['datetime']), pandas.Timestamp.today())

        # change back to proper datetime format for openmeteo: YYYY-MM-DD
        startDate = startDate.strftime('%Y-%m-%d')
        endDate = endDate.strftime('%Y-%m-%d')

        # check this later

        # pull open meteo
        dfW = retrieveWeather(lon, lat, startDate, endDate)
        dfW['date'] = pandas.to_datetime(dfW['date']).dt.tz_localize(None)
        # join

        mask = dfW['date'] >= pandas.to_datetime(startDate)  # Find rows from startDate onwards
        if mask.any():
            idx = mask.idxmax()  # Get first True index
            dfW = dfW.iloc[idx+1:]  # Slice from that index
        else:
            response['status'] = 400
            response['message'] = f"No weather data available from {startDate}"
            return json.dumps(response,indent='   ')


        dfW_temp = dfW.reset_index(drop=True).copy()
        dfW_temp.to_csv("weather.csv")
        # Perform left join
        dfW_truncated = dfW.iloc[:len(df)].reset_index(drop=True)
        df_merged = pandas.concat([df.reset_index(drop=True), dfW_truncated], axis=1)
                
        response['status'] = 200
        response['message'] = "Data retrieved successfully with weather"
        df_merged.to_csv("export.csv")
        return json.dumps(response,indent='   ')

    elif weather == "false":
        response['status'] = 200
        response['message'] = "Data has been saved to ./data"
        df.to_csv("export.csv")
    else:
        response['status'] = 400
        response['message'] = "Weather options are not true or false. Please call the API again."
    return json.dumps(response,indent='   ')

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)

