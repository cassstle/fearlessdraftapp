from flask import Flask, render_template, jsonify, request, url_for, send_from_directory, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import random
import uuid

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Try to initialize Google Cloud Storage client
try:
    from google.cloud import storage
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\summe\Downloads\triple-odyssey-435000-i0-8264176820f3.json"
    storage_client = storage.Client()
    bucket_name = 'fearlessdraft'
    bucket = storage_client.bucket(bucket_name)
    use_cloud_storage = True
except Exception as e:
    print(f"Failed to initialize Google Cloud Storage: {e}")
    use_cloud_storage = False

# Load champion data
champion_names_path = r"C:\Users\summe\Documents\LeagueChampions\champion_names.json"
champion_images_dir = r"C:\Users\summe\Desktop\static\champion_images"
champion_splashes_dir = r"C:\Users\summe\Desktop\static\champion_splashes"

with open(champion_names_path, 'r') as f:
    champion_names = json.load(f)

# Create a dictionary of champion data including splash image paths
champion_data = {}
for champion in champion_names:
    splash_jpg = os.path.join(champion_splashes_dir, f"{champion}_splash.jpg")
    splash_png = os.path.join(champion_splashes_dir, f"{champion}_splash.png")
    
    if os.path.exists(splash_jpg):
        splash_path = f"/static/champion_splashes/{champion}_splash.jpg"
    elif os.path.exists(splash_png):
        splash_path = f"/static/champion_splashes/{champion}_splash.png"
    else:
        splash_path = None
        print(f"Warning: No splash image found for {champion}")
    
    champion_data[champion] = {
        'name': champion,
        'icon': f"/static/champion_images/{champion}.png",
        'splash': splash_path
    }
    print(f"Champion: {champion}, Splash path: {splash_path}")

# Draft state
drafts = {}

def serialize_draft(draft):
    serialized = draft.copy()
    serialized['used_champions'] = list(draft['used_champions'])
    serialized['fearless_bans'] = list(draft['fearless_bans'])
    serialized['side_swap_requested'] = draft['side_swap_requested']
    return serialized

def deserialize_draft(draft_data):
    deserialized = draft_data.copy()
    deserialized['used_champions'] = set(draft_data['used_champions'])
    deserialized['fearless_bans'] = set(draft_data['fearless_bans'])
    return deserialized

def save_draft_data(room_id, draft_data):
    if use_cloud_storage:
        try:
            blob = bucket.blob(f'drafts/{room_id}.json')
            blob.upload_from_string(json.dumps(draft_data), content_type='application/json')
        except Exception as e:
            print(f"Failed to save draft data to cloud storage: {e}")
            save_draft_data_locally(room_id, draft_data)
    else:
        save_draft_data_locally(room_id, draft_data)

def save_draft_data_locally(room_id, draft_data):
    os.makedirs('local_drafts', exist_ok=True)
    with open(f'local_drafts/{room_id}.json', 'w') as f:
        json.dump(draft_data, f)

def load_draft_data(room_id):
    if use_cloud_storage:
        try:
            blob = bucket.blob(f'drafts/{room_id}.json')
            if blob.exists():
                return json.loads(blob.download_as_string())
        except Exception as e:
            print(f"Failed to load draft data from cloud storage: {e}")
    
    return load_draft_data_locally(room_id)

def load_draft_data_locally(room_id):
    try:
        with open(f'local_drafts/{room_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/draft_settings')
def draft_settings():
    return render_template('draft_settings.html')

@app.route('/create_draft', methods=['POST'])
def create_draft():
    mode = request.form['mode']
    pick_time = int(request.form['pick_time'])
    ban_time = int(request.form['ban_time'])
    games = int(request.form['games']) if mode == 'fearless' else 1

    room_id = str(uuid.uuid4())
    draft_order = get_draft_order(1)
    drafts[room_id] = {
        'mode': mode,
        'games': games,
        'current_game': 1,
        'pick_time': pick_time,
        'ban_time': ban_time,
        'blue_team': {'picks': [], 'bans': [], 'ready': False},
        'red_team': {'picks': [], 'bans': [], 'ready': False},
        'current_phase': 'Ready',
        'current_team': draft_order[0],
        'draft_index': -1,
        'draft_order': draft_order,
        'time_left': ban_time,
        'remaining_champions': champion_names.copy(),
        'used_champions': set(),
        'fearless_bans': set(),
        'hovered_champion': {'Blue': None, 'Red': None},
        'grace_period': False,
        'grace_time': 3,
        'side_swap_requested': {'Blue': False, 'Red': False},
        'previous_drafts': []
    }

    # Save draft data
    draft_data = serialize_draft(drafts[room_id])
    save_draft_data(room_id, draft_data)

    return render_template('create_draft.html', room_id=room_id)

def get_draft_order(game_number):
    base_order = ['Blue', 'Red', 'Blue', 'Red', 'Blue', 'Red', 'Blue', 'Red', 'Red', 'Blue', 'Blue', 'Red', 'Red', 'Blue', 'Red', 'Blue', 'Red', 'Blue', 'Blue', 'Red']
    
    if game_number == 5:
        draft_order = base_order[6:12] + base_order[16:]
    elif game_number == 4:
        draft_order = base_order[:12] + base_order[16:]
    else:
        draft_order = base_order
    
    return draft_order

@app.route('/join/<room_id>/<role>')
def join_draft(room_id, role):
    if room_id not in drafts:
        # Try to load draft data
        draft_data = load_draft_data(room_id)
        if draft_data:
            drafts[room_id] = deserialize_draft(draft_data)
        else:
            return "Invalid room ID", 404
    return render_template('index.html', room_id=room_id, role=role, champions=champion_data)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    role = data.get('role', 'spectator')
    join_room(room)
    print(f"User {username} joined room {room} as {role}. Current draft state: {drafts[room]}")
    emit('status', {'msg': f'{username} has entered the draft as {role}.'}, room=room)
    emit('update_draft', serialize_draft(drafts[room]), room=room)

@socketio.on('ready_up')
def ready_up(data):
    print(f"Received ready_up event: {data}")
    room = data['room']
    team = data['team']
    user_role = data['role']
    
    if user_role.lower() != team.lower():
        print(f"Invalid ready_up attempt: User role {user_role} doesn't match team {team}")
        return
    
    draft = drafts[room]
    draft[f"{team.lower()}_team"]['ready'] = True
    print(f"{team} team is ready in room {room}")
    
    if draft['blue_team']['ready'] and draft['red_team']['ready']:
        print(f"Both teams are ready in room {room}. Starting draft.")
        start_draft(room)
    else:
        print(f"Updating draft state in room {room}: Blue ready: {draft['blue_team']['ready']}, Red ready: {draft['red_team']['ready']}")
        emit('update_draft', serialize_draft(draft), room=room)

def start_draft(room):
    print(f"Starting draft for room: {room}")
    draft = drafts[room]
    draft['current_phase'] = 'Ban'
    draft['time_left'] = draft['ban_time']
    draft['blue_team']['picks'] = []
    draft['red_team']['picks'] = []
    draft['blue_team']['bans'] = []
    draft['red_team']['bans'] = []
    draft['hovered_champion'] = {'Blue': None, 'Red': None}
    draft['side_swap_requested'] = {'Blue': False, 'Red': False}
    next_turn(room)
    emit('clear_draft', room=room)
    emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

def next_turn(room):
    print(f"Next turn for room: {room}")
    draft = drafts[room]
    draft['draft_index'] += 1
    if draft['draft_index'] < len(draft['draft_order']):
        draft['current_team'] = draft['draft_order'][draft['draft_index']]
        if draft['current_game'] < 4:
            if draft['draft_index'] < 6 or (draft['draft_index'] >= 12 and draft['draft_index'] < 16):
                draft['current_phase'] = 'Ban'
                draft['time_left'] = draft['ban_time']
            else:
                draft['current_phase'] = 'Pick'
                draft['time_left'] = draft['pick_time']
        elif draft['current_game'] == 4:
            if draft['draft_index'] < 6:
                draft['current_phase'] = 'Ban'
                draft['time_left'] = draft['ban_time']
            else:
                draft['current_phase'] = 'Pick'
                draft['time_left'] = draft['pick_time']
        else:  # Game 5
            draft['current_phase'] = 'Pick'
            draft['time_left'] = draft['pick_time']
        draft['grace_period'] = False
        draft['grace_time'] = 3
    else:
        draft['current_phase'] = 'Complete'
    print(f"Updated draft state for room {room}: {draft}")
    emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

@socketio.on('update_timer')
def update_timer(data):
    room = data['room']
    draft = drafts[room]
    if draft['current_phase'] not in ['Ready', 'Complete']:
        if not draft['grace_period']:
            draft['time_left'] = max(0, draft['time_left'] - 1)
            if draft['time_left'] == 0:
                draft['grace_period'] = True
        else:
            draft['grace_time'] -= 1
            if draft['grace_time'] == 0:
                auto_lock_in(room)
        
        emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

@socketio.on('hover_champion')
def hover_champion(data):
    room = data['room']
    champion = data['champion']
    team = data['team']
    user_role = data['role']
    
    if user_role.lower() != team.lower():
        print(f"Invalid hover attempt: User role {user_role} doesn't match team {team}")
        return
    
    draft = drafts[room]
    if draft['current_phase'] in ['Ban', 'Pick'] and draft['current_team'] == team:
        draft['hovered_champion'][team] = champion
        emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

@socketio.on('lock_in_champion')
def lock_in_champion(data):
    room = data['room']
    user_role = data['role']
    draft = drafts[room]
    current_team = draft['current_team']
    
    print(f"Lock-in attempt: Room {room}, User role {user_role}, Current team {current_team}, Draft index {draft['draft_index']}, Current phase {draft['current_phase']}")
    
    if user_role.lower() != current_team.lower():
        print(f"Invalid lock-in attempt: User role {user_role} doesn't match current team {current_team}")
        return
    
    hovered_champion = draft['hovered_champion'][current_team]
    
    if hovered_champion and hovered_champion in draft['remaining_champions']:
        if draft['current_phase'] == 'Ban':
            draft[f"{current_team.lower()}_team"]['bans'].append(hovered_champion)
            draft['remaining_champions'].remove(hovered_champion)
        elif draft['current_phase'] == 'Pick':
            draft[f"{current_team.lower()}_team"]['picks'].append(hovered_champion)
            draft['fearless_bans'].add(hovered_champion)
            draft['remaining_champions'].remove(hovered_champion)
        
        draft['used_champions'].add(hovered_champion)
        draft['hovered_champion'][current_team] = None
        
        emit('update_draft', serialize_draft(draft), room=room, broadcast=True)
        
        if all_picks_complete(draft):
            if draft['mode'] == 'fearless' and draft['current_game'] < draft['games']:
                start_next_game(room)
            else:
                end_draft(room)
        else:
            next_turn(room)
    
    print(f"Updated draft state after lock-in: {draft}")

    # Update draft data
    draft_data = serialize_draft(draft)
    save_draft_data(room, draft_data)

def auto_lock_in(room):
    draft = drafts[room]
    if draft['hovered_champion'][draft['current_team']]:
        lock_in_champion({'room': room, 'role': draft['current_team'].lower()})
    else:
        available_champions = draft['remaining_champions']
        if available_champions:
            champion = random.choice(available_champions)
            draft['hovered_champion'][draft['current_team']] = champion
            lock_in_champion({'room': room, 'role': draft['current_team'].lower()})
        else:
            next_turn(room)

def all_picks_complete(draft):
    return len(draft['blue_team']['picks']) == 5 and len(draft['red_team']['picks']) == 5

def start_next_game(room):
    draft = drafts[room]
    
    # Save the current draft before starting a new game
    previous_draft = {
        'game': draft['current_game'],
        'blue_team': draft['blue_team'].copy(),
                'red_team': draft['red_team'].copy()
    }
    draft['previous_drafts'].append(previous_draft)
    
    draft['current_game'] += 1
    print(f"Starting game {draft['current_game']}")
    draft['blue_team']['picks'] = []
    draft['red_team']['picks'] = []
    draft['blue_team']['bans'] = []
    draft['red_team']['bans'] = []
    draft['blue_team']['ready'] = False
    draft['red_team']['ready'] = False
    draft['remaining_champions'] = [champ for champ in champion_names if champ not in draft['fearless_bans']]
    draft['current_phase'] = 'Ready'
    draft['draft_index'] = -1
    draft['draft_order'] = get_draft_order(draft['current_game'])
    print(f"New draft order: {draft['draft_order']}")
    draft['hovered_champion'] = {'Blue': None, 'Red': None}
    draft['time_left'] = draft['ban_time']  # Reset the timer
    draft['side_swap_requested'] = {'Blue': False, 'Red': False}
    
    emit('clear_draft', room=room)
    emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

    # Update draft data
    draft_data = serialize_draft(draft)
    save_draft_data(room, draft_data)

def end_draft(room):
    draft = drafts[room]
    draft['current_phase'] = 'Complete'
    emit('draft_complete', room=room)
    emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

    # Save final draft data
    draft_data = serialize_draft(draft)
    save_draft_data(room, draft_data)

@socketio.on('side_swap_request')
def side_swap_request(data):
    room = data['room']
    team = data['team']
    draft = drafts[room]
    
    if draft['current_phase'] == 'Ready':
        draft['side_swap_requested'][team] = True
        other_team = 'Red' if team == 'Blue' else 'Blue'
        
        if draft['side_swap_requested'][other_team]:
            # Both teams have requested a side swap
            swap_sides(room)
        else:
            emit('side_swap_requested', {'team': team}, room=room)
        
        emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

def swap_sides(room):
    draft = drafts[room]
    draft['blue_team'], draft['red_team'] = draft['red_team'], draft['blue_team']
    draft['side_swap_requested'] = {'Blue': False, 'Red': False}
    emit('sides_swapped', room=room)
    emit('update_draft', serialize_draft(draft), room=room, broadcast=True)

@app.route('/get_previous_draft/<room_id>/<int:game_number>')
def get_previous_draft(room_id, game_number):
    if room_id in drafts:
        draft = drafts[room_id]
        if 0 < game_number <= len(draft['previous_drafts']):
            return jsonify(draft['previous_drafts'][game_number - 1])
    return jsonify({"error": "Draft not found"}), 404

if __name__ == '__main__':
    socketio.run(app, debug=True)