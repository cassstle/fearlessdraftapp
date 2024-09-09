import requests
from bs4 import BeautifulSoup
import csv

url = "https://www.leagueoflegends.com/en-us/champions/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

champions = soup.find_all('a', class_='style__Wrapper-sc-n3ovyt-0')

with open('champion_roles.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Champion', 'Role1', 'Role2', 'Role3'])

    for champion in champions:
        name = champion.find('span', class_='style__Name-sc-n3ovyt-2').text.strip()
        roles = champion.find('span', class_='style__Role-sc-n3ovyt-3').text.strip().split(', ')
        writer.writerow([name] + roles + [''] * (3 - len(roles)))

print("CSV file 'champion_roles.csv' has been created.")