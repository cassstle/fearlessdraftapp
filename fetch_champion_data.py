import requests
import json
import os

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Set the paths for the folders in the Documents directory
base_path = os.path.join(os.path.expanduser('~'), 'Documents', 'LeagueChampions')
names_path = os.path.join(base_path, "champion_names.json")
images_dir = os.path.join(base_path, "champion_images")
splashes_dir = os.path.join(base_path, "champion_splashes")

# Create the directories if they don't exist
os.makedirs(base_path, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)
os.makedirs(splashes_dir, exist_ok=True)

# Fetch the latest champion data
ddragon_version = requests.get('https://ddragon.leagueoflegends.com/api/versions.json').json()[0]
champion_data_url = f'http://ddragon.leagueoflegends.com/cdn/{ddragon_version}/data/en_US/champion.json'
champion_data = requests.get(champion_data_url).json()

# Save champion names
with open(names_path, 'w') as f:
    json.dump(list(champion_data['data'].keys()), f)

# Download champion images and splash arts
for champion_name, champion_info in champion_data['data'].items():
    # Download champion icon
    icon_url = f"http://ddragon.leagueoflegends.com/cdn/{ddragon_version}/img/champion/{champion_info['image']['full']}"
    icon_data = requests.get(icon_url).content
    
    icon_file = os.path.join(images_dir, f"{champion_name}.png")
    with open(icon_file, 'wb') as f:
        f.write(icon_data)
    
    print(f"Downloaded {champion_name}.png")

    # Download champion splash art
    splash_url = f"http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion_name}_0.jpg"
    splash_data = requests.get(splash_url)
    
    if splash_data.status_code == 200:
        splash_file = os.path.join(splashes_dir, f"{champion_name}_splash.jpg")
        with open(splash_file, 'wb') as f:
            f.write(splash_data.content)
        print(f"Downloaded {champion_name}_splash.jpg")
    else:
        print(f"Failed to download splash art for {champion_name}")

print("All champion images, splash arts, and names downloaded successfully!")
print(f"Champion names saved to: {names_path}")
print(f"Champion images saved to: {images_dir}")
print(f"Champion splash arts saved to: {splashes_dir}")