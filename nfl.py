import requests
from bs4 import BeautifulSoup
import pandas as pd

# Step 3.1: Send a request to the webpage
url = 'https://www.dratings.com/predictor/nfl-football-predictions/'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Step 3.2: Parse the table
table = soup.find('table')  # Adjust this based on the actual HTML structure

# Step 3.3: Extract data from the table
rows = table.find_all('tr')
data = []

for row in rows[1:]:
    cells = row.find_all('td')
    cells = [cell.text.strip() for cell in cells[:9]]
    data.append(cells)

# Step 3.4: Create a DataFrame
df = pd.DataFrame(data, columns=['Time', 'Teams', 'Quarterbacks', 'Win', 'Best ML', 'Best Spread', 'Points', 'Total Points', 'Best O/U'])

# Step 3.5: Save or display the data
df.to_csv('nfl_data.csv', index=False)
print(df)
