import time, re
import pandas

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


def locateNyserda(farmName):
    driver = webdriver.Firefox()

    location = farmName
    driver.get("https://der.nyserda.ny.gov/search/")

    textbox = driver.find_element(By.ID, "input-facility-name")
    textbox.send_keys(location)
    textbox.send_keys(Keys.ENTER)
    time.sleep(5) # needed for dynamic update
    driver.find_element(By.CLASS_NAME, "view-button").click()
    # Get the facility id: I don't think I can do this because of dynamic webpage elements
    # https://der.nyserda.ny.gov/facilities/
    map_pin_div = driver.find_element(By.ID, "map-pin")
    anchor_tag = map_pin_div.find_element(By.TAG_NAME, "a")
    url = anchor_tag.get_attribute("href")
    
    driver.quit()
    driver = webdriver.Firefox()
    # grab coords:
    print(url)
    driver.get(url)

    # Get window size
    window_size = driver.get_window_size()
    center_x = window_size['width'] // 2
    center_y = window_size['height'] // 2

    # Move to center and click
    actions = ActionChains(driver)
    actions.move_by_offset(center_x, center_y).click().perform()

    # Wait a bit more for any JavaScript redirects
    time.sleep(5)
    url = driver.current_url
    print(f"Final URL: {url}")

    match = re.search(r'@([-\d.]+),([-\d.]+)', url)
    if match:
        latitude = float(match.group(1))
        longitude = float(match.group(2))
    else:
        longitude = None
        latitude = None
    driver.quit()
    return (latitude, longitude)

lookup = pandas.read_csv("./solarFarmNyserda.csv")

# Create new columns for latitude and longitude if they don't exist
if 'latitude' not in lookup.columns:
    lookup['latitude'] = None
if 'longitude' not in lookup.columns:
    lookup['longitude'] = None

# Loop through each row and get coordinates
for index, row in lookup.iterrows():
    farm_name = row['locationName']
    
    try:
        print(f"Processing farm: {farm_name}")
        lat, lon = locateNyserda(farm_name)
        
        # Update the dataframe with coordinates
        lookup.at[index, 'latitude'] = lat
        lookup.at[index, 'longitude'] = lon
        print(lat, lon)
        
        print(f"  Found coordinates: {lat}, {lon}")
        
        # Optional: add a small delay between requests to be polite
        time.sleep(1)
        
    except Exception as e:
        print(f"  Error processing {farm_name}: {e}")
        lookup.at[index, 'latitude'] = None
        lookup.at[index, 'longitude'] = None
    if index %25 == 0:
        print(f"\n--- Saving checkpoint after {index} farms ---")
        lookup.to_csv("./solarFarmNyserda.csv", index=False)
        print("Checkpoint saved!\n")

# Save the updated CSV file
lookup.to_csv("./solarFarmNyserda.csv", index=False)
print("CSV file saved with coordinates")