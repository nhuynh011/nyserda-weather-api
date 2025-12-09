import requests

# test landing page
response = requests.get('http://localhost:5000/')
print(response)
print(response.text)

# test search without min/max capacity
response = requests.get('http://localhost:5000/searchFarms?longitude=-73.7562&latitude=42.6526&radius_km=10')
print(response)
print(response.text)

# test search with min/max capacity
response = requests.get('http://localhost:5000/searchFarms?longitude=-73.7562&latitude=42.6526&radius_km=10&capacity_min=2601&capacity_max=10000')
print(response)
print(response.text)

# test cases that shouldn't work
response = requests.get('http://localhost:5000/searchFarms?latitude=42.6526&radius_km=10')
print(response)
print(response.text)

# can also test weird inputs as well, skipping for now.

# test get farm:
response = requests.get('http://localhost:5000/getFarm?farm_name=103 Sparling Road, LLC&include_weather=true')
print(response)
print(response.text)

# test invalid request:
response = requests.get('http://localhost:5000/getFarm?include_weather=true')
print(response)
print(response.text)


# test get farms:
response = requests.get('http://localhost:5000/getFarms?farm_name=103 Sparling Road, LLC;132 Pattersonville Rynex Corners Rd&include_weather=false')
print(response)
print(response.text)

# test invalid request:
response = requests.get('http://localhost:5000/getFarms?include_weather=false')
print(response)
print(response.text)

