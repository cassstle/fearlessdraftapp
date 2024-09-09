from .app import db

class Draft(db.Model):
    id = db.Column(db.String, primary_key=True)
    mode = db.Column(db.String, nullable=False)
    games = db.Column(db.Integer, nullable=False)
    current_game = db.Column(db.Integer, nullable=False)
    pick_time = db.Column(db.Integer, nullable=False)
    ban_time = db.Column(db.Integer, nullable=False)
    current_phase = db.Column(db.String, nullable=False)
    current_team = db.Column(db.String, nullable=False)
    draft_index = db.Column(db.Integer, nullable=False)
    draft_order = db.Column(db.String, nullable=False)
    time_left = db.Column(db.Integer, nullable=False)
    used_champions = db.Column(db.String, nullable=False)
    fearless_bans = db.Column(db.String, nullable=False)
    remaining_champions = db.Column(db.String, nullable=False)
    grace_period = db.Column(db.Boolean, nullable=False)
    grace_time = db.Column(db.Integer, nullable=False)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.String, db.ForeignKey('draft.id'), nullable=False)
    color = db.Column(db.String, nullable=False)
    picks = db.Column(db.String, nullable=False)
    bans = db.Column(db.String, nullable=False)
    ready = db.Column(db.Boolean, nullable=False)
    hovered_champion = db.Column(db.String, nullable=True)

class PreviousDraft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.String, db.ForeignKey('draft.id'), nullable=False)
    game_number = db.Column(db.Integer, nullable=False)
    blue_team_picks = db.Column(db.String, nullable=False)
    blue_team_bans = db.Column(db.String, nullable=False)
    red_team_picks = db.Column(db.String, nullable=False)
    red_team_bans = db.Column(db.String, nullable=False)