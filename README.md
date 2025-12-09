# NYSERDA Solar Farms and Weather API - Complete Documentation
A REST API that joins New York solar farm generation data (from NYSERDA) with weather conditions (from Open-Meteo). The API supports both JSON responses and CSV file downloads.<br/>
<br/>
Verion 0: Currently only downloads CSV to server side.<br/>
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
### 2. Search Farms
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
### 3. Get Farm
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

### 4. Get Farms
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
