import sys
import json
import os
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel, QScrollArea,
                             QLineEdit, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
                             QSizePolicy, QSpinBox, QDialog, QGroupBox, QRadioButton)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QFont, QIcon, QPainter
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize, QTimer

class ChampionIcon(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, champion_name, icon_path, size=60):
        super().__init__()
        pixmap = QPixmap(icon_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        self.setFixedSize(size, size)
        self.setToolTip(champion_name)
        self.champion_name = champion_name
        self.setStyleSheet("border: 1px solid #2c3033;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.champion_name)

class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.settings = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Draft Settings')
        self.setGeometry(300, 300, 400, 500)
        layout = QVBoxLayout()

        # Timer settings
        timer_group = QGroupBox("Timer Settings")
        timer_layout = QVBoxLayout()

        pick_layout = QHBoxLayout()
        pick_label = QLabel("Pick Time (seconds):")
        self.pick_time = QSpinBox()
        self.pick_time.setRange(10, 60)
        self.pick_time.setValue(30)
        pick_layout.addWidget(pick_label)
        pick_layout.addWidget(self.pick_time)
        timer_layout.addLayout(pick_layout)

        ban_layout = QHBoxLayout()
        ban_label = QLabel("Ban Time (seconds):")
        self.ban_time = QSpinBox()
        self.ban_time.setRange(10, 60)
        self.ban_time.setValue(30)
        ban_layout.addWidget(ban_label)
        ban_layout.addWidget(self.ban_time)
        timer_layout.addLayout(ban_layout)

        timer_group.setLayout(timer_layout)
        layout.addWidget(timer_group)

        # Draft mode settings
        mode_group = QGroupBox("Draft Mode")
        mode_layout = QVBoxLayout()
        self.normal_draft = QRadioButton("Normal Draft")
        self.fearless_draft = QRadioButton("Fearless Draft")
        self.true_fearless_draft = QRadioButton("True Fearless Draft")
        self.normal_draft.setChecked(True)
        mode_layout.addWidget(self.normal_draft)
        mode_layout.addWidget(self.fearless_draft)
        mode_layout.addWidget(self.true_fearless_draft)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Team links
        links_group = QGroupBox("Team Links")
        links_layout = QVBoxLayout()
        self.blue_link = QLineEdit()
        self.blue_link.setPlaceholderText("Blue Team Link")
        self.red_link = QLineEdit()
        self.red_link.setPlaceholderText("Red Team Link")
        self.spectator_link = QLineEdit()
        self.spectator_link.setPlaceholderText("Spectator Link")
        links_layout.addWidget(self.blue_link)
        links_layout.addWidget(self.red_link)
        links_layout.addWidget(self.spectator_link)
        links_group.setLayout(links_layout)
        layout.addWidget(links_group)

        # Confirm button
        confirm_button = QPushButton("Start Draft")
        confirm_button.clicked.connect(self.confirm_settings)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def confirm_settings(self):
        draft_mode = "Normal"
        if self.fearless_draft.isChecked():
            draft_mode = "Fearless"
        elif self.true_fearless_draft.isChecked():
            draft_mode = "True Fearless"
        
        self.settings = (
            self.pick_time.value(),
            self.ban_time.value(),
            draft_mode,
            self.blue_link.text(),
            self.red_link.text(),
            self.spectator_link.text()
        )
        self.accept()

class DraftSimulator(QWidget):
    def __init__(self, pick_time, ban_time, draft_mode, blue_link, red_link, spectator_link):
        super().__init__()
        self.pick_time = pick_time
        self.ban_time = ban_time
        self.draft_mode = draft_mode
        self.blue_link = blue_link
        self.red_link = red_link
        self.spectator_link = spectator_link
        self.champion_icons = {}
        self.champion_splashes = {}
        self.banned_champions = {'Blue': [], 'Red': []}
        self.picked_champions = {'Blue': [], 'Red': []}
        self.hovered_champion = {'Blue': None, 'Red': None}
        self.current_phase = 'Ban'
        self.current_team = 'Blue'
        self.draft_order = ['Blue', 'Red', 'Blue', 'Red', 'Blue', 'Red',  # First ban phase
                            'Blue', 'Red', 'Red', 'Blue', 'Blue', 'Red',  # First pick phase
                            'Red', 'Blue', 'Red', 'Blue',  # Second ban phase
                            'Red', 'Blue', 'Blue', 'Red']  # Second pick phase
        self.draft_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.time_left = self.ban_time
        self.grace_period = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('League of Legends Draft Simulator')
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("""
            QWidget {
                background-color: #0e1015;
                color: #c8aa6e;
                font-family: Arial;
            }
            QPushButton {
                background-color: #1e2328;
                border: 2px solid #c8aa6e;
                padding: 5px;
                min-width: 80px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c8aa6e;
                color: #1e2328;
            }
            QLineEdit {
                background-color: #2c3033;
                border: 1px solid #c8aa6e;
                padding: 5px;
                font-size: 16px;
            }
        """)

        main_layout = QHBoxLayout(self)

        # Blue team layout
        blue_layout = self.create_team_layout("Blue", is_left_side=True)
        main_layout.addLayout(blue_layout)

        # Center layout
        center_layout = self.create_center_layout()
        main_layout.addLayout(center_layout)

        # Red team layout
        red_layout = self.create_team_layout("Red", is_left_side=False)
        main_layout.addLayout(red_layout)

        # Load champion data
        champion_names_path = r"C:\Users\summe\Documents\LeagueChampions\champion_names.json"
        champion_images_dir = r"C:\Users\summe\Documents\LeagueChampions\champion_images"
        champion_splashes_dir = r"C:\Users\summe\Documents\LeagueChampions\champion_splashes"

        with open(champion_names_path, 'r') as f:
            self.champion_names = json.load(f)

        for champion in self.champion_names:
            icon_path = os.path.join(champion_images_dir, f'{champion}.png')
            splash_path = os.path.join(champion_splashes_dir, f'{champion}_splash.jpg')
            if os.path.exists(icon_path):
                icon = ChampionIcon(champion, icon_path)
                icon.clicked.connect(self.on_champion_click)
                self.champion_icons[champion] = icon
            if os.path.exists(splash_path):
                self.champion_splashes[champion] = splash_path

        self.arrange_icons()
        self.timer.start(1000)  # Start the timer

    def create_team_layout(self, team, is_left_side):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        team_label = QLabel(team)
        team_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {'#0099ff' if team == 'Blue' else '#ff4444'};")
        team_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(team_label)

        picks_layout = QVBoxLayout()
        picks_layout.setSpacing(2)
        for i in range(5):
            pick_row = QHBoxLayout()
            pick_row.setSpacing(5)
            
            pick_placeholder = QLabel()
            pick_placeholder.setFixedSize(240, 135)
            pick_placeholder.setStyleSheet("background-color: #2c3033; border: 1px solid #2c3033;")
            
            role_label = QLabel()
            role_label.setFixedSize(30, 135)
            role_label.setStyleSheet("background-color: #1e2328; border: 1px solid #c8aa6e;")
            
            if is_left_side:
                pick_row.addWidget(pick_placeholder)
                pick_row.addWidget(role_label)
            else:
                pick_row.addWidget(role_label)
                pick_row.addWidget(pick_placeholder)
            
            picks_layout.addLayout(pick_row)
        
        picks_frame = QFrame()
        picks_frame.setLayout(picks_layout)
        picks_frame.setStyleSheet("background-color: transparent;")
        layout.addWidget(picks_frame)
        setattr(self, f"{team.lower()}_picks_layout", picks_layout)

        bans_layout = QHBoxLayout()
        for i in range(5):  # Always 5 bans
            ban_placeholder = QLabel()
            ban_placeholder.setFixedSize(50, 50)
            ban_placeholder.setStyleSheet("background-color: #2c3033; border: 1px solid #2c3033;")
            if i == 3:
                spacer = QLabel()
                spacer.setFixedSize(10, 50)
                spacer.setStyleSheet("background-color: transparent;")
                bans_layout.addWidget(spacer)
            bans_layout.addWidget(ban_placeholder)
        bans_frame = QFrame()
        bans_frame.setLayout(bans_layout)
        bans_frame.setStyleSheet("background-color: transparent;")
        layout.addWidget(bans_frame)
        setattr(self, f"{team.lower()}_bans_layout", bans_layout)

        return layout

    def create_center_layout(self):
        layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search champions...")
        self.search_bar.textChanged.connect(self.filter_champions)
        layout.addWidget(self.search_bar)

        # Role filter icons (placeholder)
        role_filter = QHBoxLayout()
        roles = ["Top", "Jungle", "Mid", "ADC", "Support"]
        for role in roles:
            role_btn = QPushButton(role)
            role_btn.setFixedSize(80, 30)
            role_filter.addWidget(role_btn)
        layout.addLayout(role_filter)

        # Champion grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.grid = QGridLayout(scroll_content)
        self.grid.setSpacing(0)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Timer label
        self.timer_label = QLabel(f"Time left: {self.time_left}")
        self.timer_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)

        # Status and Lock In
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Current Phase: Ban | Current Team: Blue")
        self.status_label.setStyleSheet("font-size: 18px;")
        status_layout.addWidget(self.status_label)
        
        self.lock_in_button = QPushButton("Lock In")
        self.lock_in_button.clicked.connect(self.lock_in_champion)
        status_layout.addWidget(self.lock_in_button)
        
        layout.addLayout(status_layout)

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
                    if col > 11:  # 12 icons per row
                        col = 0
                        row += 1

    def filter_champions(self):
        search_text = self.search_bar.text().lower()
        filtered_champions = [champ for champ in self.champion_names if search_text in champ.lower()]
        self.arrange_icons(filtered_champions)

    def on_champion_click(self, champion_name):
        self.hovered_champion[self.current_team] = champion_name
        self.update_team_layout(self.current_team)

    def lock_in_champion(self):
        if self.hovered_champion[self.current_team]:
            if self.current_phase == 'Ban':
                self.banned_champions[self.current_team].append(self.hovered_champion[self.current_team])
            else:
                self.picked_champions[self.current_team].append(self.hovered_champion[self.current_team])
            
            self.hovered_champion[self.current_team] = None
            self.update_team_layout(self.current_team)
            self.arrange_icons()
            self.next_turn()

    def next_turn(self):
        self.draft_index += 1
        if self.draft_index < len(self.draft_order):
            self.current_team = self.draft_order[self.draft_index]
            if self.draft_index < 6 or (self.draft_index >= 12 and self.draft_index < 16):
                self.current_phase = 'Ban'
                self.time_left = self.ban_time
            else:
                self.current_phase = 'Pick'
                self.time_left = self.pick_time
            self.status_label.setText(f"Current Phase: {self.current_phase} | Current Team: {self.current_team}")
            self.timer_label.setText(f"Time left: {self.time_left}")
            self.grace_period = False
            self.timer_label.setStyleSheet("font-size: 24px; color: #ffffff;")
        else:
            self.status_label.setText("Draft Completed")
            self.lock_in_button.setEnabled(False)
            self.timer.stop()

    def update_timer(self):
        self.time_left -= 1
        self.timer_label.setText(f"Time left: {self.time_left}")
        
        if self.time_left <= 0:
            if not self.grace_period:
                self.grace_period = True
                self.time_left = 3
                self.timer_label.setStyleSheet("font-size: 24px; color: #ff0000;")
            else:
                self.grace_period = False
                self.timer_label.setStyleSheet("font-size: 24px; color: #ffffff;")
                self.auto_lock_in()

    def auto_lock_in(self):
        if self.hovered_champion[self.current_team]:
            self.lock_in_champion()
        else:
            # If no champion is hovered, select a random available champion
            available_champions = [champ for champ in self.champion_names if champ not in self.banned_champions['Blue'] + self.banned_champions['Red'] + self.picked_champions['Blue'] + self.picked_champions['Red']]
            if available_champions:
                self.hovered_champion[self.current_team] = random.choice(available_champions)
                self.lock_in_champion()
            else:
                self.next_turn()

    def update_team_layout(self, team):
        bans_layout = getattr(self, f"{team.lower()}_bans_layout")
        picks_layout = getattr(self, f"{team.lower()}_picks_layout")

        for i in range(5):  # Always 5 bans
            ban_widget = bans_layout.itemAt(i if i < 3 else i + 1).widget()
            if i < len(self.banned_champions[team]):
                ban = self.banned_champions[team][i]
                ban_icon = ChampionIcon(ban, os.path.join(r"C:\Users\summe\Documents\LeagueChampions\champion_images", f'{ban}.png'), size=50)
                ban_icon.setStyleSheet("background-color: #2c3033; border: 1px solid #ff4040;")
                bans_layout.replaceWidget(ban_widget, ban_icon)
                ban_widget.deleteLater()
            elif i == len(self.banned_champions[team]) and self.current_phase == 'Ban' and self.hovered_champion[team]:
                hover_icon = ChampionIcon(self.hovered_champion[team], os.path.join(r"C:\Users\summe\Documents\LeagueChampions\champion_images", f'{self.hovered_champion[team]}.png'), size=50)
                hover_icon.setStyleSheet("background-color: #2c3033; border: 1px solid #ffff00;")
                bans_layout.replaceWidget(ban_widget, hover_icon)
                ban_widget.deleteLater()
            else:
                ban_widget.setStyleSheet("background-color: #2c3033; border: 1px solid #2c3033;")

        for i in range(5):
            pick_row = picks_layout.itemAt(i)
            pick_widget = pick_row.itemAt(0 if team == 'Blue' else 1).widget()
            if i < len(self.picked_champions[team]):
                pick = self.picked_champions[team][i]
                self.update_pick_widget(pick_widget, pick, "#40ff40")
            elif i == len(self.picked_champions[team]) and self.current_phase == 'Pick' and self.hovered_champion[team]:
                self.update_pick_widget(pick_widget, self.hovered_champion[team], "#ffff00")
            else:
                pick_widget.clear()
                pick_widget.setStyleSheet("background-color: #2c3033; border: 1px solid #2c3033;")

    def update_pick_widget(self, widget, champion, border_color):
        splash_path = self.champion_splashes.get(champion)
        if splash_path:
            original_pixmap = QPixmap(splash_path)
            target_size = QSize(240, 135)
            
            # Scale the pixmap to fit within the target size while maintaining aspect ratio
            scaled_pixmap = original_pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Create a new pixmap with the target size
            final_pixmap = QPixmap(target_size)
            final_pixmap.fill(QColor('#2c3033'))  # Fill with background color
            
            # Calculate position to center the scaled pixmap
            x = (target_size.width() - scaled_pixmap.width()) // 2
            y = (target_size.height() - scaled_pixmap.height()) // 2
            
            # Draw the scaled pixmap onto the final pixmap
            painter = QPainter(final_pixmap)
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
            
            widget.setPixmap(final_pixmap)
            widget.setStyleSheet(f"border: 1px solid {border_color};")
        else:
            icon_path = os.path.join(r"C:\Users\summe\Documents\LeagueChampions\champion_images", f'{champion}.png')
            pixmap = QPixmap(icon_path).scaled(135, 135, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            widget.setPixmap(pixmap)
            widget.setAlignment(Qt.AlignCenter)
            widget.setStyleSheet(f"background-color: #2c3033; border: 1px solid {border_color};")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    settings_window = SettingsWindow()
    if settings_window.exec_() == QDialog.Accepted:
        if settings_window.settings:
            pick_time, ban_time, draft_mode, blue_link, red_link, spectator_link = settings_window.settings
            ex = DraftSimulator(pick_time, ban_time, draft_mode, blue_link, red_link, spectator_link)
            ex.show()
            sys.exit(app.exec_())
        else:
            print("Settings were not properly configured.")
            sys.exit(1)