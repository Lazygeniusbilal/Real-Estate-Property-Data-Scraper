# Import Dependencies
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Initialize lists to store the data
address = []
price = []
bathrooms = []
bedrooms = []
area = []
property_type_list = []

# Define the property types and city indices to iterate over
property_types = ['residential', 'commercial']
city_indices = [1, 2, 3]

# Loop through each property type and city index
for property_type in property_types:
    for city_index in city_indices:
        for i in range(1, 3):  # 1 to 51 pages
            url = f"https://www.graana.com/sale/{property_type}-properties-sale-{city_index}/?pageSize=30&page={i}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            divs = soup.find_all('div', class_='MuiBox-root mui-style-zf9afz')
            
            for div in divs:
                address_tag = div.find('h5', class_="MuiTypography-root MuiTypography-subtitle2New mui-style-3bzwbl")
                price_tag = div.find('div', class_="MuiTypography-root MuiTypography-h4New mui-style-gz23my")
                if address_tag and price_tag:
                    address.append(address_tag.text.strip())
                    price.append(price_tag.text.strip())
                    property_type_list.append(property_type)
                    
            property_tags = soup.find_all('div', class_='MuiTypography-root MuiTypography-body2New mui-style-1548769')
            for j in range(0, len(property_tags), 3):  # Step by 3 as each property has 3 pieces of info
                try:
                    bathrooms.append(property_tags[j].text.strip())
                    bedrooms.append(property_tags[j+1].text.strip())
                    area.append(property_tags[j+2].text.strip())
                except IndexError:
                    # Handle cases where the number of divs is not a multiple of 3
                    break

# Convert the lists to a DataFrame for easy viewing and manipulation
df = pd.DataFrame({
    'Address': address,
    'Price': price,
    'Bathrooms': bathrooms,
    'Bedrooms': bedrooms,
    'Area': area,
    'Property Type': property_type_list
})

# Display the DataFrame
print(df)
 