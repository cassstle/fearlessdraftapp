import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel, QScrollArea,
                             QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFrame)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QFont
from PyQt5.QtCore import Qt, pyqtSignal

class ChampionIcon(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, champion_name, icon_path, size=60):
        super().__init__()
        pixmap = QPixmap(icon_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        self.setToolTip(champion_name)
        self.champion_name = champion_name
        self.setStyleSheet("border: 2px solid transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.champion_name)

class DraftSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.champion_icons = {}
        self.banned_champions = {'Blue': [], 'Red': []}
        self.picked_champions = {'Blue': [], 'Red': []}
        self.current_phase = 'Ban'
        self.current_team = 'Blue'
        self.draft_order = ['Blue', 'Red', 'Blue', 'Red', 'Blue', 'Red',  # First ban phase
                            'Blue', 'Red', 'Red', 'Blue', 'Blue', 'Red',  # First pick phase
                            'Blue', 'Red', 'Blue', 'Red',                 # Second ban phase
                            'Red', 'Blue', 'Red', 'Blue']                 # Second pick phase
        self.draft_index = 0
        self.selected_champion = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('League of Legends Draft Simulator')
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e2328;
                color: #c8aa6e;
                font-family: Arial;
            }
            QPushButton {
                background-color: #1e2328;
                border: 2px solid #c8aa6e;
                padding: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #c8aa6e;
                color: #1e2328;
            }
            QLineEdit {
                background-color: #2c3033;
                border: 1px solid #c8aa6e;
                padding: 5px;
            }
        """)

        main_layout = QHBoxLayout()

        # Blue team layout
        blue_layout = self.create_team_layout("Blue")
        main_layout.addLayout(blue_layout)

        # Center layout
        center_layout = QVBoxLayout()
        self.status_label = QLabel("Current Phase: Ban | Current Team: Blue")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        center_layout.addWidget(self.status_label)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search champions...")
        self.search_bar.textChanged.connect(self.filter_champions)
        center_layout.addWidget(self.search_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.grid = QGridLayout(scroll_content)
        self.grid.setSpacing(10)
        scroll.setWidget(scroll_content)
        center_layout.addWidget(scroll)

        self.selected_champ_label = QLabel("Selected: None")
        self.selected_champ_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.selected_champ_label)

        buttons_layout = QHBoxLayout()
        self.ban_button = QPushButton("Ban")
        self.ban_button.clicked.connect(self.ban_champion)
        self.pick_button = QPushButton("Pick")
        self.pick_button.clicked.connect(self.pick_champion)
        buttons_layout.addWidget(self.ban_button)
        buttons_layout.addWidget(self.pick_button)
        center_layout.addLayout(buttons_layout)

        main_layout.addLayout(center_layout)

        # Red team layout
        red_layout = self.create_team_layout("Red")
        main_layout.addLayout(red_layout)

        self.setLayout(main_layout)

        # Load champion data
        champion_names_path = r"C:\Users\summe\Documents\LeagueChampions\champion_names.json"
        champion_images_dir = r"C:\Users\summe\Documents\LeagueChampions\champion_images"

        with open(champion_names_path, 'r') as f:
            self.champion_names = json.load(f)

        for champion in self.champion_names:
            icon_path = os.path.join(champion_images_dir, f'{champion}.png')
            if os.path.exists(icon_path):
                icon = ChampionIcon(champion, icon_path)
                icon.clicked.connect(self.on_champion_click)
                self.champion_icons[champion] = icon

        self.arrange_icons()

    def create_team_layout(self, team):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        team_label = QLabel(f"{team} Team")
        team_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        team_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(team_label)

        bans_label = QLabel("Bans")
        bans_label.setStyleSheet("font-size: 18px;")
        bans_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(bans_label)

        bans_layout = QHBoxLayout()
        for i in range(5):
            ban_placeholder = QLabel()
            ban_placeholder.setStyleSheet("background-color: #2c3033; min-width: 60px; min-height: 60px;")
            bans_layout.addWidget(ban_placeholder)
        layout.addLayout(bans_layout)
        setattr(self, f"{team.lower()}_bans_layout", bans_layout)

        picks_label = QLabel("Picks")
        picks_label.setStyleSheet("font-size: 18px;")
        picks_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(picks_label)

        picks_layout = QVBoxLayout()
        for i in range(5):
            pick_placeholder = QLabel()
            pick_placeholder.setStyleSheet("background-color: #2c3033; min-width: 60px; min-height: 60px;")
            picks_layout.addWidget(pick_placeholder)
        layout.addLayout(picks_layout)
        setattr(self, f"{team.lower()}_picks_layout", picks_layout)

        layout.addStretch()
        return layout

    def arrange_icons(self, champions_to_show=None):
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)

        row, col = 0, 0
        for champion, icon in self.champion_icons.items():
            if champions_to_show is None or champion in champions_to_show:
                if champion not in self.banned_champions['Blue'] + self.banned_champions['Red'] + \
                   self.picked_champions['Blue'] + self.picked_champions['Red']:
                    self.grid.addWidget(icon, row, col)
                    col += 1
                    if col > 9:  # 10 icons per row
                        col = 0
                        row += 1

    def filter_champions(self):
        search_text = self.search_bar.text().lower()
        filtered_champions = [champ for champ in self.champion_names if search_text in champ.lower()]
        self.arrange_icons(filtered_champions)

    def on_champion_click(self, champion_name):
        if self.selected_champion:
            self.champion_icons[self.selected_champion].setStyleSheet("border: 2px solid transparent;")
        self.selected_champion = champion_name
        self.champion_icons[champion_name].setStyleSheet("border: 2px solid #c8aa6e;")
        self.selected_champ_label.setText(f"Selected: {champion_name}")

    def ban_champion(self):
        if self.selected_champion and self.current_phase == 'Ban':
            self.banned_champions[self.current_team].append(self.selected_champion)
            self.update_team_layout(self.current_team)
            self.arrange_icons()
            self.next_turn()
            self.reset_selection()

    def pick_champion(self):
        if self.selected_champion and self.current_phase == 'Pick':
            self.picked_champions[self.current_team].append(self.selected_champion)
            self.update_team_layout(self.current_team)
            self.arrange_icons()
            self.next_turn()
            self.reset_selection()

    def reset_selection(self):
        if self.selected_champion:
            self.champion_icons[self.selected_champion].setStyleSheet("border: 2px solid transparent;")
        self.selected_champion = None
        self.selected_champ_label.setText("Selected: None")

    def next_turn(self):
        self.draft_index += 1
        if self.draft_index < len(self.draft_order):
            self.current_team = self.draft_order[self.draft_index]
            if self.draft_index < 6:
                self.current_phase = 'Ban'
            elif self.draft_index < 12:
                self.current_phase = 'Pick'
            elif self.draft_index < 16:
                self.current_phase = 'Ban'
            else:
                self.current_phase = 'Pick'
            self.status_label.setText(f"Current Phase: {self.current_phase} | Current Team: {self.current_team}")
        else:
            self.status_label.setText("Draft Completed")
            self.ban_button.setEnabled(False)
            self.pick_button.setEnabled(False)

    def update_team_layout(self, team):
        bans_layout = getattr(self, f"{team.lower()}_bans_layout")
        picks_layout = getattr(self, f"{team.lower()}_picks_layout")

        for i in range(5):
            ban_widget = bans_layout.itemAt(i).widget()
            if i < len(self.banned_champions[team]):
                ban = self.banned_champions[team][i]
                ban_icon = ChampionIcon(ban, os.path.join(r"C:\Users\summe\Documents\LeagueChampions\champion_images", f'{ban}.png'), size=50)
                ban_icon.setStyleSheet("background-color: #2c3033; border: 2px solid #ff4040;")
                bans_layout.replaceWidget(ban_widget, ban_icon)
                ban_widget.deleteLater()
            else:
                ban_widget.setStyleSheet("background-color: #2c3033; min-width: 50px; min-height: 50px;")

        for i in range(5):
            pick_widget = picks_layout.itemAt(i).widget()
            if i < len(self.picked_champions[team]):
                pick = self.picked_champions[team][i]
                pick_icon = ChampionIcon(pick, os.path.join(r"C:\Users\summe\Documents\LeagueChampions\champion_images", f'{pick}.png'))
                pick_icon.setStyleSheet("background-color: #2c3033; border: 2px solid #40ff40;")
                picks_layout.replaceWidget(pick_widget, pick_icon)
                pick_widget.deleteLater()
            else:
                pick_widget.setStyleSheet("background-color: #2c3033; min-width: 60px; min-height: 60px;")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DraftSimulator()
    ex.show()
    sys.exit(app.exec_())