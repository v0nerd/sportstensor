import requests
from bs4 import BeautifulSoup
import pandas as pd

# Step 3.1: Send a request to the webpage
url = 'https://www.dratings.com/predictor/mls-soccer-predictions/'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Step 3.2: Parse the table
table = soup.find('table')  # Adjust this based on the actual HTML structure

# Step 3.3: Extract data from the table
rows = table.find_all('tr')
data = []

for row in rows[1:]:
    cells = row.find_all('td')
    cell_data = []
    for cell in cells[:8]:
        if cell.find('a'):
            cell_data.append(cell.find('a').text)
            continue
        parts = cell.decode_contents().split('<br>')
        parts = [BeautifulSoup(part, 'html.parser').get_text(strip=True) for part in parts]
        cell_data.extend(parts)
    data.append(cell_data)

# Step 3.4: Create a DataFrame
df = pd.DataFrame(data, columns=['Time', 'Team A', 'Team B', 'Win A', 'Win B', 'Draw', 'Best ML A', 'Best ML B', 'Goals A', 'Goals B', 'Total Goals', 'Best O', 'Best U'])

# Step 3.5: Save or display the data
df.to_csv('mls_data.csv', index=False)
print(df)
