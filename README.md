# NYSERDA Solar Farms and Weather API - Complete Documentation
A REST API that joins New York solar farm generation data (from NYSERDA: https://der.nyserda.ny.gov/search/) with weather conditions (from Open-Meteo: https://open-meteo.com/en/docs/historical-weather-api). The API supports both JSON responses and CSV file downloads.<br/>
<br/>
**Verion 1.0.0**: Currently only downloads CSV to server side.<br/>
Requires firefox browser for Selenium webscraping.<br/>
Base URL: `http://localhost:5000/` or `http://your-server-ip:5000/`

# API Endpoints:
### 1. Root Endpoint (`GET/`)
Returns this documentation in HTML.<br/>
<br/>
Example:<br/>
```python
import requests, json
response = requests.get('http://localhost:5000/')
```
### 2. Search Farms (`GET/`)
Search for solar farms within a geographic radius and/or capacity range. Only retrieves farms from 1MW o 10MW capacity.<br/>
Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `latitude` | float | Yes | Latitude coordinate (e.g., 42.6526). |
| `longitude` | float | Yes | Longitude coordinate (e.g., -73.7562). |
| `radius_km` | float | Yes | Search radius in kilometers. |
| `capacity_min` | float | No | Minimum capacity in kW (default: 0). |
| `capacity_max` | float | No | Maximum capacity in kW (default: unlimited). |

**Example**:<br/>
```python
import requests, json
response = requests.get('http://localhost:5000/searchFarms?longitude=-73.7562&latitude=42.6526&radius_km=10')
```
### 3. Get Farm (`GET/`)
Gets complete historical electricity generation records for a specified solar farm by its name, optionally with weather data.<br/>
Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `farm_name` | string | Yes | Solar farm name on NYSERDA website. |
| `include_weather` | bool | Yes | Include weather data at specified farm (true/false). |

**Example**:<br/>
```python
import requests, json
response = requests.get('http://localhost:5000/getFarm?farm_name=103 Sparling Road, LLC&include_weather=true')
```

### 4. Get Farms (`GET/`)
Get and merge data for multiple solar farms, optionally with weather data. Uses the geographic centroid of all farms for weather data retrieval.<br/>
Parameters:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `farm_name` | string | Yes | Solar farm name (in a semi-colon seperated list) from NYSERDA website (e.g., 03 Sparling Road, LLC;132 Pattersonville Rynex Corners Rd). |
| `include_weather` | bool | Yes | Include weather data at specified farm (true/false). |

**Example**:<br/>
```python
import requests, json
response = requests.get('getFarms?farm_name=103 Sparling Road, LLC;132 Pattersonville Rynex Corners Rd&include_weather=false')
```
### 5. Download files
Currently not availible. A future feature that allows clients to download the files that they get from endpoint /getFarm and /getFarms.<br/>

# Weather Parameters
Weather parameters pulled alongside solar farms information from OpenMeteo.
| Parameter Name | Description |
|----------------|-------------|
| `temperature_2m` | Air temperature measured at 2 meters above ground level |
| `relative_humidity_2m` | Relative humidity percentage measured at 2 meters above ground |
| `precipitation` | Total liquid-equivalent precipitation (rain, snow, sleet, etc.) |
| `cloud_cover` | Total percentage of sky covered by clouds |
| `cloud_cover_low` | Percentage of sky covered by low-level clouds |
| `cloud_cover_mid` | Percentage of sky covered by mid-level clouds |
| `cloud_cover_high` | Percentage of sky covered by high-level clouds |
| `wind_speed_10m` | Wind speed measured at 10 meters above ground level |
| `shortwave_radiation` | Incoming shortwave solar radiation (sunlight) reaching the surface |
| `direct_radiation` | Direct beam solar radiation from the sun's disc |
| `diffuse_radiation` | Scattered solar radiation from the sky |
| `direct_normal_irradiance` | Direct solar radiation perpendicular to the sun's rays |
| `global_tilted_irradiance` | Total solar radiation on a surface tilted at a specific angle |

# Additional Files:
**requirements.txt**: A list of package requirements for running this script.<br/>
**preProcessing.py**: A script that uses Selenium to scrape the NYSERDA solar farm's coordinates.<br/>
**solarFarmNyserda.csv**: A file containing the name of the solar farm, their coordinates, capacity, and town for searchFarms endpoint. Originally, this file did not have coordinates and only had solar farm names, capacity, and town. Updated using preProcessing.py to obtain the coordinates for each farm.<br/>
**testClient.py**: A test client file for unit testing.
