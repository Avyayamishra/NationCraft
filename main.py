#!/usr/bin/env python3
"""
NationCraft: Decisions of a President - GUI Version
A modern GUI-based presidential simulation game with SQLite database integration.
"""

import sqlite3
import json
import random
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import customtkinter as ctk
from tkinter import messagebox
import threading
import time

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class DatabaseManager:
    """Handles all database operations for the game."""
    
    def __init__(self, db_path: str = "nationcraft.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table 1: Game Sessions (save/load functionality)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                save_name TEXT UNIQUE NOT NULL,
                country_name TEXT NOT NULL,
                current_year INTEGER NOT NULL,
                current_turn INTEGER NOT NULL,
                economy INTEGER NOT NULL,
                happiness INTEGER NOT NULL,
                stability INTEGER NOT NULL,
                relations INTEGER NOT NULL,
                military_power INTEGER NOT NULL,
                environment INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 2: High Scores (leaderboard)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS high_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                country_name TEXT NOT NULL,
                years_survived INTEGER NOT NULL,
                turns_survived INTEGER NOT NULL,
                final_economy INTEGER NOT NULL,
                final_happiness INTEGER NOT NULL,
                final_stability INTEGER NOT NULL,
                final_relations INTEGER NOT NULL,
                cause_of_downfall TEXT NOT NULL,
                achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 3: Game Events/Cases (dynamic case management)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                options TEXT NOT NULL, -- JSON string
                difficulty_level TEXT DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize with default events if table is empty
        self.populate_default_events()
    
    def populate_default_events(self):
        """Populate the database with enhanced default game events with reasons."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if events already exist
        cursor.execute("SELECT COUNT(*) FROM game_events")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        default_events = [
            {
                "category": "economy",
                "title": "Auto Industry Strike",
                "description": "A major strike has broken out in the automobile industry. Workers demand higher wages and better working conditions. Production has halted at major plants.",
                "options": [
                    {
                        "text": "Approve higher wages immediately",
                        "effects": {"economy": -10, "happiness": 20, "stability": 5},
                        "reason": "Higher wages strain the budget but boost worker morale and loyalty. Quick resolution prevents prolonged disruption."
                    },
                    {
                        "text": "Reject demands and deploy police",
                        "effects": {"economy": 5, "happiness": -15, "stability": -10},
                        "reason": "Forceful suppression saves money short-term but creates deep resentment and potential for future unrest."
                    },
                    {
                        "text": "Negotiate for partial wage increase",
                        "effects": {"economy": -5, "happiness": 10, "stability": 5},
                        "reason": "Compromise shows leadership while balancing economic concerns. Both sides make concessions."
                    },
                    {
                        "text": "Offer alternative benefits package",
                        "effects": {"economy": -3, "happiness": 8, "relations": 3},
                        "reason": "Creative solutions like healthcare or training programs cost less than wages but still address worker concerns."
                    }
                ]
            },
            {
                "category": "diplomacy",
                "title": "Border Dispute Escalation",
                "description": "A neighboring country has moved troops near your eastern border, claiming historical territorial rights. International observers are watching closely.",
                "options": [
                    {
                        "text": "Deploy military to the border",
                        "effects": {"military_power": 10, "relations": -15, "economy": -8},
                        "reason": "Military posturing shows strength but escalates tensions and drains resources for deployment and maintenance."
                    },
                    {
                        "text": "Request UN mediation",
                        "effects": {"relations": 8, "stability": 5, "economy": -3},
                        "reason": "Diplomatic approach enhances international standing and provides neutral arbitration, though it requires funding."
                    },
                    {
                        "text": "Offer territorial compromise",
                        "effects": {"relations": 15, "happiness": -10, "stability": -5},
                        "reason": "Peaceful resolution improves diplomatic ties but appears weak to citizens who view it as giving up sovereign land."
                    },
                    {
                        "text": "Impose targeted economic sanctions",
                        "effects": {"economy": -5, "relations": -8, "stability": 3},
                        "reason": "Economic pressure shows resolve without military action, but reduces trade and may hurt your own economy."
                    }
                ]
            },
            {
                "category": "environment",
                "title": "Industrial Pollution Crisis",
                "description": "Several major factories have been releasing toxic chemicals into the air and water. Environmental groups are protesting, and public health concerns are rising.",
                "options": [
                    {
                        "text": "Immediately shut down polluting factories",
                        "effects": {"environment": 20, "economy": -15, "happiness": -8},
                        "reason": "Decisive environmental action prevents health disasters but causes massive job losses and economic disruption."
                    },
                    {
                        "text": "Implement gradual emission standards",
                        "effects": {"environment": 8, "economy": -5, "happiness": 5},
                        "reason": "Balanced approach gives companies time to adapt while showing environmental commitment. Moderate costs for all."
                    },
                    {
                        "text": "Ignore environmental concerns",
                        "effects": {"economy": 5, "environment": -10, "happiness": -12, "stability": -8},
                        "reason": "Prioritizing industry over environment leads to health crises, public outrage, and long-term ecological damage."
                    },
                    {
                        "text": "Invest heavily in green technology subsidies",
                        "effects": {"environment": 15, "economy": -10, "relations": 8},
                        "reason": "Forward-thinking investment creates jobs in new sectors and improves international image, but requires significant upfront costs."
                    }
                ]
            },
            {
                "category": "politics",
                "title": "Government Corruption Scandal",
                "description": "Investigative journalists have exposed a major corruption ring involving high-ranking government officials and defense contractors. The media is demanding accountability.",
                "options": [
                    {
                        "text": "Launch comprehensive investigation",
                        "effects": {"stability": 15, "happiness": 10, "economy": -5},
                        "reason": "Transparent accountability restores public trust and strengthens institutions, though investigations are costly and time-consuming."
                    },
                    {
                        "text": "Attempt to suppress the story",
                        "effects": {"stability": -15, "happiness": -20, "economy": 5},
                        "reason": "Cover-up attempts backfire when exposed, creating deeper scandals and destroying credibility with the public."
                    },
                    {
                        "text": "Quietly remove officials without fanfare",
                        "effects": {"stability": 5, "happiness": -5, "economy": 3},
                        "reason": "Minimal response addresses the immediate problem but doesn't satisfy demands for justice and transparency."
                    },
                    {
                        "text": "Blame opposition and deflect",
                        "effects": {"stability": -8, "happiness": -10, "relations": -5},
                        "reason": "Political deflection appears defensive and dishonest, damaging relationships with both domestic opposition and international partners."
                    }
                ]
            },
            {
                "category": "military",
                "title": "Defense Modernization Pressure",
                "description": "Military leaders warn that neighboring countries are advancing their weapons systems. They request significant budget increases for modernization programs.",
                "options": [
                    {
                        "text": "Approve major defense spending increase",
                        "effects": {"military_power": 15, "economy": -12, "stability": 8},
                        "reason": "Strong military deters threats and reassures citizens, but diverts funds from civilian programs and increases deficit spending."
                    },
                    {
                        "text": "Maintain current defense budget",
                        "effects": {"military_power": -5, "stability": 3, "happiness": 5},
                        "reason": "Fiscal responsibility pleases taxpayers but may leave military outdated, potentially creating security vulnerabilities."
                    },
                    {
                        "text": "Reduce defense spending for social programs",
                        "effects": {"economy": 10, "military_power": -15, "stability": -8},
                        "reason": "Reallocation helps civilian needs but weakens defense capabilities and may alarm military leadership and allies."
                    },
                    {
                        "text": "Seek international defense partnerships",
                        "effects": {"military_power": 8, "relations": -5, "economy": 3},
                        "reason": "Shared defense costs reduce expenses but create dependency on allies and may compromise strategic autonomy."
                    }
                ]
            },
            {
                "category": "economy",
                "title": "Economic Recession Warning",
                "description": "Economic indicators show the country is entering a recession. Unemployment is rising, businesses are closing, and consumer confidence is at a five-year low.",
                "options": [
                    {
                        "text": "Launch massive stimulus package",
                        "effects": {"economy": 15, "happiness": 10, "stability": 5},
                        "reason": "Government spending jumpstarts economic activity and provides immediate relief, but increases national debt significantly."
                    },
                    {
                        "text": "Implement austerity measures",
                        "effects": {"economy": -5, "happiness": -10, "stability": -5},
                        "reason": "Fiscal restraint may worsen short-term conditions but aims for long-term stability by reducing government debt burden."
                    },
                    {
                        "text": "Increase taxes on wealthy individuals",
                        "effects": {"economy": 8, "happiness": -8, "stability": -3},
                        "reason": "Revenue from high earners funds programs but may discourage investment and create capital flight among the wealthy."
                    },
                    {
                        "text": "Attract foreign investment with incentives",
                        "effects": {"economy": 12, "relations": -3, "stability": 3},
                        "reason": "Foreign capital creates jobs and growth but may create dependency and concerns about national economic sovereignty."
                    }
                ]
            },
            {
                "category": "social",
                "title": "Healthcare System Crisis",
                "description": "Hospitals are overwhelmed, medical staff are burned out, and critical supplies are running short. Citizens are demanding immediate healthcare system reforms.",
                "options": [
                    {
                        "text": "Massively increase healthcare funding",
                        "effects": {"happiness": 15, "economy": -10, "stability": 8},
                        "reason": "Investment in healthcare saves lives and improves quality of life but requires significant budget reallocation or new taxes."
                    },
                    {
                        "text": "Privatize significant portions of healthcare",
                        "effects": {"economy": 8, "happiness": -12, "stability": -5},
                        "reason": "Market solutions may improve efficiency and reduce government costs but limit access for lower-income citizens."
                    },
                    {
                        "text": "Implement gradual healthcare reforms",
                        "effects": {"happiness": 8, "economy": -5, "stability": 3},
                        "reason": "Step-by-step improvements balance budget concerns with healthcare needs but may not address urgent crisis fast enough."
                    },
                    {
                        "text": "Import healthcare workers and expand medical training",
                        "effects": {"happiness": 10, "economy": -8, "relations": 5},
                        "reason": "Expanding healthcare capacity through immigration and education provides long-term solutions but requires time and investment."
                    }
                ]
            }
        ]
        
        for event in default_events:
            cursor.execute('''
                INSERT INTO game_events (category, title, description, options)
                VALUES (?, ?, ?, ?)
            ''', (event["category"], event["title"], event["description"], json.dumps(event["options"])))
        
        conn.commit()
        conn.close()
    
    def save_game(self, save_name: str, game_state: Dict):
        """Save current game state to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO game_sessions 
            (save_name, country_name, current_year, current_turn, economy, happiness, 
             stability, relations, military_power, environment, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            save_name,
            game_state["country_name"],
            game_state["current_year"],
            game_state["current_turn"],
            game_state["stats"]["economy"],
            game_state["stats"]["happiness"],
            game_state["stats"]["stability"],
            game_state["stats"]["relations"],
            game_state["stats"]["military_power"],
            game_state["stats"]["environment"]
        ))
        
        conn.commit()
        conn.close()
    
    def load_game(self, save_name: str) -> Optional[Dict]:
        """Load game state from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM game_sessions WHERE save_name = ?', (save_name,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "country_name": row[2],
            "current_year": row[3],
            "current_turn": row[4],
            "stats": {
                "economy": row[5],
                "happiness": row[6],
                "stability": row[7],
                "relations": row[8],
                "military_power": row[9],
                "environment": row[10]
            }
        }
    
    def get_saved_games(self) -> List[Tuple]:
        """Get list of all saved games."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT save_name, country_name, current_year, updated_at FROM game_sessions ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def save_high_score(self, score_data: Dict):
        """Save high score to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO high_scores 
            (player_name, country_name, years_survived, turns_survived, 
             final_economy, final_happiness, final_stability, final_relations, cause_of_downfall)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            score_data["player_name"],
            score_data["country_name"],
            score_data["years_survived"],
            score_data["turns_survived"],
            score_data["final_stats"]["economy"],
            score_data["final_stats"]["happiness"],
            score_data["final_stats"]["stability"],
            score_data["final_stats"]["relations"],
            score_data["cause_of_downfall"]
        ))
        
        conn.commit()
        conn.close()
    
    def get_leaderboard(self, limit: int = 10) -> List[Tuple]:
        """Get top scores from leaderboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT player_name, country_name, years_survived, turns_survived, cause_of_downfall, achieved_at
            FROM high_scores 
            ORDER BY years_survived DESC, turns_survived DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_random_event(self) -> Dict:
        """Get a random event from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT title, description, options FROM game_events ORDER BY RANDOM() LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "title": row[0],
            "description": row[1],
            "options": json.loads(row[2])
        }


class NationCraftGUI:
    """Main GUI application class for NationCraft."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.root = ctk.CTk()
        self.root.title("🏛️ NationCraft: Decisions of a President")
        self.root.geometry("1200x800")
        
        # Game state
        self.stats = {
            "economy": 50,
            "happiness": 50,
            "stability": 50,
            "relations": 50,
            "military_power": 50,
            "environment": 50
        }
        self.current_year = 2024
        self.current_turn = 0
        self.country_name = ""
        self.player_name = ""
        self.current_event = None
        
        # GUI components
        self.main_frame = None
        self.game_frame = None
        self.stats_frame = None
        self.event_frame = None
        self.stats_bars = {}
        self.stats_labels = {}
        
        self.setup_main_menu()
    
    def setup_main_menu(self):
        """Setup the main menu interface."""
        # Clear existing frames
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="🏛️ NATIONCRAFT: DECISIONS OF A PRESIDENT",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(30, 10))
        
        subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="⚖️ One choice can change a nation. Lead wisely, survive history.",
            font=ctk.CTkFont(size=16)
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Menu buttons
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(pady=20)
        
        new_game_btn = ctk.CTkButton(
            button_frame,
            text="🆕 New Game",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=200,
            height=50,
            command=self.new_game_setup
        )
        new_game_btn.pack(pady=10)
        
        load_game_btn = ctk.CTkButton(
            button_frame,
            text="💾 Load Game",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=200,
            height=50,
            command=self.load_game_menu
        )
        load_game_btn.pack(pady=10)
        
        leaderboard_btn = ctk.CTkButton(
            button_frame,
            text="🏆 Leaderboard",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=200,
            height=50,
            command=self.show_leaderboard
        )
        leaderboard_btn.pack(pady=10)
        
        exit_btn = ctk.CTkButton(
            button_frame,
            text="❌ Exit",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=200,
            height=50,
            command=self.root.quit
        )
        exit_btn.pack(pady=10)
    
    def new_game_setup(self):
        """Setup new game with player input."""
        setup_window = ctk.CTkToplevel(self.root)
        setup_window.title("New Game Setup")
        setup_window.geometry("400x300")
        setup_window.transient(self.root)
        setup_window.grab_set()
        
        # Center the window
        setup_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 400, self.root.winfo_rooty() + 250))
        
        title_label = ctk.CTkLabel(
            setup_window,
            text="🆕 NEW GAME SETUP",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Player name
        ctk.CTkLabel(setup_window, text="👤 Enter your name:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        player_entry = ctk.CTkEntry(setup_window, width=300, placeholder_text="President Name")
        player_entry.pack(pady=5)
        
        # Country name
        ctk.CTkLabel(setup_window, text="🏛️ Enter your country name:", font=ctk.CTkFont(size=14)).pack(pady=(10, 5))
        country_entry = ctk.CTkEntry(setup_window, width=300, placeholder_text="Country Name")
        country_entry.pack(pady=5)
        
        def start_game():
            self.player_name = player_entry.get().strip() or "President"
            self.country_name = country_entry.get().strip() or "United Republic"
            
            # Reset game state
            self.stats = {
                "economy": 50,
                "happiness": 50,
                "stability": 50,
                "relations": 50,
                "military_power": 50,
                "environment": 50
            }
            self.current_year = 2024
            self.current_turn = 0
            
            setup_window.destroy()
            self.setup_game_interface()
        
        start_btn = ctk.CTkButton(
            setup_window,
            text="🎊 Start Game",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=start_game
        )
        start_btn.pack(pady=20)
    
    def setup_game_interface(self):
        """Setup the main game interface."""
        # Clear existing frames
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main game frame
        self.game_frame = ctk.CTkFrame(self.root)
        self.game_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top bar with country info and menu
        top_frame = ctk.CTkFrame(self.game_frame)
        top_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        country_label = ctk.CTkLabel(
            top_frame,
            text=f"🏛️ {self.country_name} | President {self.player_name}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        country_label.pack(side="left", padx=10, pady=10)
        
        year_label = ctk.CTkLabel(
            top_frame,
            text=f"📅 Year: {self.current_year} | Turn: {self.current_turn}",
            font=ctk.CTkFont(size=16)
        )
        year_label.pack(side="left", padx=20, pady=10)
        
        # Menu buttons
        menu_frame = ctk.CTkFrame(top_frame)
        menu_frame.pack(side="right", padx=10, pady=5)
        
        save_btn = ctk.CTkButton(menu_frame, text="💾 Save", width=80, command=self.save_game_dialog)
        save_btn.pack(side="left", padx=5)
        
        menu_btn = ctk.CTkButton(menu_frame, text="🏠 Menu", width=80, command=self.setup_main_menu)
        menu_btn.pack(side="left", padx=5)
        
        # Stats panel
        self.setup_stats_panel()
        
        # Event panel
        self.setup_event_panel()
        
        # Load first event
        self.load_next_event()
    
    def setup_stats_panel(self):
        """Setup the statistics display panel."""
        self.stats_frame = ctk.CTkFrame(self.game_frame)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_title = ctk.CTkLabel(
            self.stats_frame,
            text="📊 PRESIDENTIAL DASHBOARD",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        stats_title.pack(pady=(10, 20))
        
        # Create stats bars in a grid
        stats_grid = ctk.CTkFrame(self.stats_frame)
        stats_grid.pack(pady=(0, 10), padx=20, fill="x")
        
        row = 0
        col = 0
        for stat_name, value in self.stats.items():
            # Stat container
            stat_container = ctk.CTkFrame(stats_grid)
            stat_container.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
            
            # Stat name
            stat_label = ctk.CTkLabel(
                stat_container,
                text=stat_name.upper().replace('_', ' '),
                font=ctk.CTkFont(size=12, weight="bold")
            )
            stat_label.pack(pady=(5, 0))
            
            # Progress bar
            progress_bar = ctk.CTkProgressBar(stat_container, width=150)
            progress_bar.pack(pady=5)
            progress_bar.set(value / 100)
            
            # Value label
            value_label = ctk.CTkLabel(
                stat_container,
                text=f"{value}%",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            value_label.pack(pady=(0, 5))
            
            # Store references
            self.stats_bars[stat_name] = progress_bar
            self.stats_labels[stat_name] = value_label
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(3):
            stats_grid.grid_columnconfigure(i, weight=1)
    
    def setup_event_panel(self):
        """Setup the event display and decision panel."""
        self.event_frame = ctk.CTkFrame(self.game_frame)
        self.event_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Event will be loaded here
    
    def update_stats_display(self):
        """Update the statistics display."""
        for stat_name, value in self.stats.items():
            self.stats_bars[stat_name].set(value / 100)
            self.stats_labels[stat_name].configure(text=f"{value}%")
            
            # Update color based on value
            if value > 70:
                color = "green"
            elif value > 30:
                color = "orange"
            else:
                color = "red"
    
    def load_next_event(self):
        """Load and display the next event."""
        self.current_event = self.db.get_random_event()
        
        if not self.current_event:
            messagebox.showerror("Error", "No events available!")
            return
        
        # Clear event frame
        for widget in self.event_frame.winfo_children():
            widget.destroy()
        
        # Event title
        event_title = ctk.CTkLabel(
            self.event_frame,
            text=f"🚨 CRISIS: {self.current_event['title']}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="red"
        )
        event_title.pack(pady=(20, 10))
        
        # Event description
        desc_frame = ctk.CTkFrame(self.event_frame)
        desc_frame.pack(fill="x", padx=20, pady=10)
        
        desc_text = ctk.CTkTextbox(desc_frame, height=100, wrap="word")
        desc_text.pack(fill="x", padx=10, pady=10)
        desc_text.insert("1.0", self.current_event['description'])
        desc_text.configure(state="disabled")
        
        # Options title
        options_title = ctk.CTkLabel(
            self.event_frame,
            text="💭 Your Decision Options:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        options_title.pack(pady=(20, 10))
        
        # Options buttons
        options_frame = ctk.CTkFrame(self.event_frame)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        for i, option in enumerate(self.current_event['options']):
            btn = ctk.CTkButton(
                options_frame,
                text=f"{i + 1}. {option['text']}",
                font=ctk.CTkFont(size=14),
                height=40,
                command=lambda idx=i: self.make_decision(idx)
            )
            btn.pack(fill="x", padx=10, pady=5)
    
    def make_decision(self, choice_index):
        """Handle player's decision and show effects."""
        chosen_option = self.current_event['options'][choice_index]
        
        # Show decision impact dialog
        self.show_decision_impact(chosen_option)
        
        # Apply effects
        self.apply_effects(chosen_option['effects'])
        
        # Update turn and year
        self.current_turn += 1
        if self.current_turn % 4 == 0:  # New year every 4 turns
            self.current_year += 1
        
        # Update stats display
        self.update_stats_display()
        
        # Check for game over
        game_over, cause = self.check_game_over()
        if game_over:
            self.game_over_screen(cause)
            return
        
        # Update year display
        self.update_year_display()
        
        # Load next event after a brief delay
        self.root.after(1000, self.load_next_event)
    
    def show_decision_impact(self, chosen_option):
        """Show the impact and reasoning for the decision."""
        impact_window = ctk.CTkToplevel(self.root)
        impact_window.title("Decision Impact")
        impact_window.geometry("600x500")
        impact_window.transient(self.root)
        impact_window.grab_set()
        
        # Center the window
        impact_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 300, self.root.winfo_rooty() + 150))
        
        # Title
        title_label = ctk.CTkLabel(
            impact_window,
            text="📢 DECISION IMPACT",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Decision made
        decision_frame = ctk.CTkFrame(impact_window)
        decision_frame.pack(fill="x", padx=20, pady=10)
        
        decision_label = ctk.CTkLabel(
            decision_frame,
            text="✅ Your Decision:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        decision_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        decision_text = ctk.CTkTextbox(decision_frame, height=60, wrap="word")
        decision_text.pack(fill="x", padx=10, pady=(0, 10))
        decision_text.insert("1.0", chosen_option['text'])
        decision_text.configure(state="disabled")
        
        # Effects
        effects_frame = ctk.CTkFrame(impact_window)
        effects_frame.pack(fill="x", padx=20, pady=10)
        
        effects_label = ctk.CTkLabel(
            effects_frame,
            text="📈 Impact on Nation:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        effects_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        for stat, change in chosen_option['effects'].items():
            if stat in self.stats:
                color = "green" if change > 0 else "red"
                direction = "📈" if change > 0 else "📉"
                effect_text = ctk.CTkLabel(
                    effects_frame,
                    text=f"   {direction} {stat.upper().replace('_', ' ')}: {change:+d}",
                    font=ctk.CTkFont(size=12),
                    text_color=color
                )
                effect_text.pack(anchor="w", padx=20, pady=2)
        
        # Reasoning
        reasoning_frame = ctk.CTkFrame(impact_window)
        reasoning_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        reasoning_label = ctk.CTkLabel(
            reasoning_frame,
            text="🤔 Why This Happened:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        reasoning_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        reasoning_text = ctk.CTkTextbox(reasoning_frame, wrap="word")
        reasoning_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        reasoning_text.insert("1.0", chosen_option['reason'])
        reasoning_text.configure(state="disabled")
        
        # Continue button
        continue_btn = ctk.CTkButton(
            impact_window,
            text="⏳ Continue",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=impact_window.destroy
        )
        continue_btn.pack(pady=20)
    
    def apply_effects(self, effects: Dict):
        """Apply decision effects to game stats."""
        for stat, change in effects.items():
            if stat in self.stats:
                self.stats[stat] = max(0, min(100, self.stats[stat] + change))
    
    def check_game_over(self) -> Tuple[bool, str]:
        """Check if game over conditions are met."""
        for stat, value in self.stats.items():
            if value <= 0:
                causes = {
                    "economy": "💸 Economic Collapse! Your nation's economy has completely failed, leading to widespread poverty and chaos.",
                    "happiness": "🔥 Revolution! The people have risen against your government in a massive uprising.",
                    "stability": "⚔️ Military Coup! Army generals have seized power and removed you from office.",
                    "relations": "🌍 International Isolation! Your country has become a pariah state with no allies.",
                    "military_power": "🏴 Invasion! Enemy forces have conquered your nation due to weak defenses.",
                    "environment": "☢️ Environmental Catastrophe! The nation has become uninhabitable due to ecological collapse."
                }
                return True, causes[stat]
        return False, ""
    
    def update_year_display(self):
        """Update the year display in the top bar."""
        # Find and update year label (this is a simplified approach)
        # In a more complex implementation, you'd store a reference to the label
        pass
    
    def save_game_dialog(self):
        """Show save game dialog."""
        save_window = ctk.CTkToplevel(self.root)
        save_window.title("Save Game")
        save_window.geometry("300x200")
        save_window.transient(self.root)
        save_window.grab_set()
        
        # Center the window
        save_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 450, self.root.winfo_rooty() + 300))
        
        title_label = ctk.CTkLabel(
            save_window,
            text="💾 SAVE GAME",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        ctk.CTkLabel(save_window, text="📝 Enter save name:", font=ctk.CTkFont(size=14)).pack(pady=5)
        
        save_entry = ctk.CTkEntry(save_window, width=200, placeholder_text="Save Name")
        save_entry.pack(pady=10)
        
        def save_game():
            save_name = save_entry.get().strip()
            if not save_name:
                messagebox.showerror("Error", "Save name cannot be empty!")
                return
            
            game_state = {
                "country_name": self.country_name,
                "current_year": self.current_year,
                "current_turn": self.current_turn,
                "stats": self.stats
            }
            
            try:
                self.db.save_game(save_name, game_state)
                messagebox.showinfo("Success", f"Game saved as '{save_name}'!")
                save_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save game: {e}")
        
        save_btn = ctk.CTkButton(
            save_window,
            text="✅ Save",
            command=save_game
        )
        save_btn.pack(pady=20)
    
    def load_game_menu(self):
        """Show load game menu."""
        saved_games = self.db.get_saved_games()
        
        if not saved_games:
            messagebox.showinfo("No Saves", "No saved games found!")
            return
        
        load_window = ctk.CTkToplevel(self.root)
        load_window.title("Load Game")
        load_window.geometry("600x400")
        load_window.transient(self.root)
        load_window.grab_set()
        
        # Center the window
        load_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 300, self.root.winfo_rooty() + 200))
        
        title_label = ctk.CTkLabel(
            load_window,
            text="💾 SAVED GAMES",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Scrollable frame for saved games
        scrollable_frame = ctk.CTkScrollableFrame(load_window, width=550, height=250)
        scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        for save_name, country, year, date in saved_games:
            game_frame = ctk.CTkFrame(scrollable_frame)
            game_frame.pack(fill="x", pady=5)
            
            info_text = f"📁 {save_name} - {country} (Year {year})\n📅 {date[:16]}"
            info_label = ctk.CTkLabel(game_frame, text=info_text, justify="left")
            info_label.pack(side="left", padx=10, pady=10)
            
            load_btn = ctk.CTkButton(
                game_frame,
                text="Load",
                width=80,
                command=lambda name=save_name: self.load_selected_game(name, load_window)
            )
            load_btn.pack(side="right", padx=10, pady=10)
    
    def load_selected_game(self, save_name, load_window):
        """Load the selected game."""
        game_state = self.db.load_game(save_name)
        
        if game_state:
            self.country_name = game_state["country_name"]
            self.current_year = game_state["current_year"]
            self.current_turn = game_state["current_turn"]
            self.stats = game_state["stats"]
            
            load_window.destroy()
            self.setup_game_interface()
            messagebox.showinfo("Success", f"Game '{save_name}' loaded successfully!")
        else:
            messagebox.showerror("Error", "Failed to load game!")
    
    def show_leaderboard(self):
        """Display the leaderboard."""
        scores = self.db.get_leaderboard()
        
        leaderboard_window = ctk.CTkToplevel(self.root)
        leaderboard_window.title("Hall of Presidents")
        leaderboard_window.geometry("800x500")
        leaderboard_window.transient(self.root)
        leaderboard_window.grab_set()
        
        # Center the window
        leaderboard_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 200, self.root.winfo_rooty() + 150))
        
        title_label = ctk.CTkLabel(
            leaderboard_window,
            text="🏆 HALL OF PRESIDENTS",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=20)
        
        if not scores:
            no_scores_label = ctk.CTkLabel(
                leaderboard_window,
                text="📊 No scores yet! Be the first to make history!",
                font=ctk.CTkFont(size=16)
            )
            no_scores_label.pack(pady=50)
        else:
            # Headers
            headers_frame = ctk.CTkFrame(leaderboard_window)
            headers_frame.pack(fill="x", padx=20, pady=10)
            
            headers = ["Rank", "President", "Country", "Years", "Turns", "Downfall"]
            header_widths = [60, 120, 120, 80, 80, 200]
            
            for i, (header, width) in enumerate(zip(headers, header_widths)):
                label = ctk.CTkLabel(
                    headers_frame,
                    text=header,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    width=width
                )
                label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
            
            # Scrollable frame for scores
            scrollable_frame = ctk.CTkScrollableFrame(leaderboard_window, width=750, height=300)
            scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)
            
            for i, (name, country, years, turns, cause, date) in enumerate(scores, 1):
                score_frame = ctk.CTkFrame(scrollable_frame)
                score_frame.pack(fill="x", pady=2)
                
                # Medal for top 3
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                data = [medal, name[:15], country[:15], str(years), str(turns), cause[:25]]
                
                for j, (datum, width) in enumerate(zip(data, header_widths)):
                    label = ctk.CTkLabel(
                        score_frame,
                        text=datum,
                        width=width,
                        font=ctk.CTkFont(size=12)
                    )
                    label.grid(row=0, column=j, padx=5, pady=5, sticky="w")
        
        close_btn = ctk.CTkButton(
            leaderboard_window,
            text="Close",
            command=leaderboard_window.destroy
        )
        close_btn.pack(pady=20)
    
    def game_over_screen(self, cause: str):
        """Display game over screen and save high score."""
        game_over_window = ctk.CTkToplevel(self.root)
        game_over_window.title("Game Over")
        game_over_window.geometry("600x600")
        game_over_window.transient(self.root)
        game_over_window.grab_set()
        
        # Center the window
        game_over_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 300, self.root.winfo_rooty() + 100))
        
        # Game Over title
        title_label = ctk.CTkLabel(
            game_over_window,
            text="💀 GAME OVER",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="red"
        )
        title_label.pack(pady=20)
        
        # Cause of downfall
        cause_frame = ctk.CTkFrame(game_over_window)
        cause_frame.pack(fill="x", padx=20, pady=10)
        
        cause_text = ctk.CTkTextbox(cause_frame, height=80, wrap="word")
        cause_text.pack(fill="x", padx=10, pady=10)
        cause_text.insert("1.0", cause)
        cause_text.configure(state="disabled")
        
        # Statistics
        stats_frame = ctk.CTkFrame(game_over_window)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text="📊 FINAL STATISTICS",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        stats_title.pack(pady=(10, 5))
        
        info_text = f"""
🏛️ Country: {self.country_name}
📅 Years Survived: {self.current_year - 2024}
🔄 Turns Survived: {self.current_turn}
        """
        
        info_label = ctk.CTkLabel(
            stats_frame,
            text=info_text,
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        info_label.pack(pady=5)
        
        # Final stats
        final_stats_frame = ctk.CTkFrame(stats_frame)
        final_stats_frame.pack(fill="x", padx=10, pady=10)
        
        final_stats_title = ctk.CTkLabel(
            final_stats_frame,
            text="📈 FINAL NATION STATUS:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        final_stats_title.pack(pady=(5, 10))
        
        for stat, value in self.stats.items():
            color = "green" if value > 50 else "orange" if value > 25 else "red"
            stat_label = ctk.CTkLabel(
                final_stats_frame,
                text=f"{stat.upper().replace('_', ' ')}: {value}%",
                font=ctk.CTkFont(size=12),
                text_color=color
            )
            stat_label.pack(anchor="w", padx=20, pady=2)
        
        # Save high score
        score_data = {
            "player_name": self.player_name,
            "country_name": self.country_name,
            "years_survived": self.current_year - 2024,
            "turns_survived": self.current_turn,
            "final_stats": self.stats,
            "cause_of_downfall": cause
        }
        
        try:
            self.db.save_high_score(score_data)
            success_label = ctk.CTkLabel(
                game_over_window,
                text="✅ Your score has been recorded in the Hall of Presidents!",
                font=ctk.CTkFont(size=12),
                text_color="green"
            )
            success_label.pack(pady=10)
        except Exception as e:
            error_label = ctk.CTkLabel(
                game_over_window,
                text=f"❌ Failed to save score: {e}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.pack(pady=10)
        
        # Buttons
        button_frame = ctk.CTkFrame(game_over_window)
        button_frame.pack(pady=20)
        
        new_game_btn = ctk.CTkButton(
            button_frame,
            text="🆕 New Game",
            command=lambda: [game_over_window.destroy(), self.new_game_setup()]
        )
        new_game_btn.pack(side="left", padx=10)
        
        main_menu_btn = ctk.CTkButton(
            button_frame,
            text="🏠 Main Menu",
            command=lambda: [game_over_window.destroy(), self.setup_main_menu()]
        )
        main_menu_btn.pack(side="left", padx=10)
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        app = NationCraftGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Game interrupted. Thanks for playing!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please restart the game.")


if __name__ == "__main__":
    main()