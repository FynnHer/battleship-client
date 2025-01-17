import tkinter as tk
import socket
from PIL import Image, ImageTk
import pygame
from tkinter import messagebox
import cv2
import threading
import time
import os
from ffpyplayer.player import MediaPlayer
#Importing various librarys
#tkinter = window and gui generation
#Socket = server communication
#PIL = showing and editing images
#pygame = sound and music design 
#messagebox = mesage window
#cv2 = showing videos
#threading = multi threading
#time = time and time stopping
#os = edit and open files and folders
#ffpyplayer = play videos and reformat

# Color scheme
COLORS = {
    "background": "#2B303A",
    "board": "#92DCE5",
    "text": "#EEE5E9",
    "button": "#7C7C7C",
    "accent": "#D64933",
    "miss": "#FFFFFF",
    "hit": "#FFFF00"
}

# Asset paths
ASSETS = {
    "cursor": "assets/cursor.png",
    "siren": "assets/siren.wav",
    "videos": {
        "hit": "assets/hit.mp4",
        "miss": "assets/miss.mp4",
        "win": "assets/win.mp4",
        "lose": "assets/lose.mp4"
    }
}
# Video lengths to set the pause time depending on the video
VIDEOLENGTHS = {
    "hit": 15,
    "miss": 10,
    "win": 54,
    "lose": 54
}

class DraggableShip(tk.Label):
    def __init__(self, parent, length: int, game_instance, orientation="horizontal", **kwargs, ) -> None:
        '''
        Initialization of important game stats and inforamtion
        '''
        super().__init__(parent, **kwargs)
        self.length = length
        self.game = game_instance
        self.orientation = orientation
        self.bind('<Button-1>', self.start_drag)
        self.bind('<B1-Motion>', self.drag)
        self.bind('<ButtonRelease-1>', self.stop_drag)
        self._drag_data = {"x": 0, "y": 0}
        self._original_x = 0
        self._original_y = 0
        self._preview_cells = []

    def toggle_orientation(self, event=None) -> None:
        '''
        Method for toggling the orientation of the ships
        '''
        self.orientation = "vertical" if self.orientation == "horizontal" else "horizontal"
        if self.orientation == "horizontal":
            self.config(text="🔴" * self.length)
        else:
            self.configure(text="\n".join("🔴" for _ in range(self.length)))
        if self.game.current_placing_rotation != self.orientation:
            self.game.current_placing_rotation = self.orientation

    def start_drag(self, event: tk.Event) -> None:
        '''
        Method for getting coordinates at the start of dragging
        '''
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self.configure(bg=COLORS["accent"])

    def drag(self, event: tk.Event) -> None:
        '''
        Method for getting coordinates of dragging
        '''
        deltax = event.x - self._drag_data["x"]
        deltay = event.y - self._drag_data["y"]
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.place(x=x, y=y)

        # Calling for updated preview in window
        self.update_preview()
        
    def stop_drag(self, event: tk.Event) -> None:
        '''
        Method for dropping the at the end of the drag
        '''    
        try:
            # Calculate the position of the ship on the board
            self.update_preview()
            board_x = self.winfo_rootx() - self.game.board_frame.winfo_rootx()
            board_y = self.winfo_rooty() - self.game.board_frame.winfo_rooty()
            grid_x = board_x // 30
            grid_y = board_y // 30
            
            # Place the ship on the board if it fits
            if 0 <= grid_x < 10 and 0 <= grid_y < 10:
                if self.game.place_ship(grid_y, grid_x, self.length, self.orientation):
                    self.game.finished_ships.remove(self)
                    self.destroy()
                else:
                    # Reset ship position if it doesn't fit
                    self.place_forget()
                    self.pack(side=tk.LEFT, padx=5, pady=5)
                    self.clear_preview()
            else:
                # Reset ship position if it doesn't fit
                self.place_forget()
                self.pack(side=tk.LEFT, padx=5, pady=5)
                self.clear_preview()
        except Exception as e:
            print(f"Error in ship placement: {e}")
            self.place(x=self._original_x, y=self._original_y)
            
    def update_preview(self) -> None:
        '''
        Method for updating the preview of the ship
        '''
        board_x = self.winfo_rootx() - self.game.board_frame.winfo_rootx()
        board_y = self.winfo_rooty() - self.game.board_frame.winfo_rooty()
        grid_x = board_x // 30
        grid_y = board_y // 30

        self.clear_preview()

        # Check if ship fits on the board
        if 0 <= grid_x < 10 and 0 <= grid_y < 10:
            for i in range(self.length):
                r, c = (grid_y + i, grid_x) if self.orientation == "vertical" else (grid_y, grid_x + i)
                if 0 <= r < 10 and 0 <= c < 10:
                    # Check if no ship is already placed in the field
                    if self.game.field[r][c] == " ":
                        # Update the preview list
                        self._preview_cells.append((r, c))
                        # Change the color of the cell
                        self.game.cells[r][c].configure(bg=COLORS["accent"])
                    else:
                        self.clear_preview()
                        break
    
    def clear_preview(self) -> None:
        '''
        Method for clearing all previews and the list with previews
        '''
        for r, c in self._preview_cells:
            self.game.cells[r][c].configure(bg=COLORS["board"])
        self._preview_cells.clear()

class BattleshipGame(tk.Tk):
    '''
    Class for a game including gameloop, screen for selecting username etc
    '''
    def __init__(self, specialmode: bool) -> None:
        '''
        Initializing important attributes of the class, specialmode selecting wheter there should be special effects or not
        '''
        super().__init__()
        self.specialmode = specialmode # Special mode for special effects, bool
        self.player = None
        self.testcell = None
        self.playing = False
        self.current_video = None
        self.cap = None
        self.placed_ships = []
        self.current_placing_rotation = "horizontal"
        self.field = [[" " for _ in range(10)] for _ in range(10)]
        self.title("Battleship")
        self.geometry("1200x800")
        self.configure(bg=COLORS["background"])
        if self.specialmode:
            # Initialize pygame mixer for sound effects
            pygame.mixer.init()
            
            # Load custom cursor
            # Only functional in some python versions - work in progress
        try:
            cursor_image = Image.open(ASSETS["cursor"])
            cursor_image = cursor_image.resize((32, 32), Image.Resampling.LANCZOS)
            self.target_cursor = ImageTk.PhotoImage(cursor_image)
        # Error handling
        except Exception as e:
            print(f"Could not load cursor image: {e}")
            self.target_cursor = None
        # Calling for UI setup
        self.setup_ui()
        self.selected_cell = None
        self.game_active = False

    def setup_ui(self) -> None:
        '''
        Setup main ui elements of the gui
        '''
        self.main_container = tk.Frame(self, bg=COLORS["background"])
        self.main_container.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Left frame for game board
        self.left_frame = tk.Frame(self.main_container, bg=COLORS["background"], width=700)
        self.left_frame.pack(side=tk.LEFT, expand=False, fill="both")
        self.left_frame.pack_propagate(False)
        self.board_frame = tk.Frame(self.left_frame, bg=COLORS["background"])
        self.board_frame.pack(pady=20)
        
        # Create board cells
        self.cells = [[self.create_cell(i, j) for j in range(10)] for i in range(10)]
        
        # Ships frame
        self.ships_frame = tk.Frame(self.left_frame, bg=COLORS["background"])
        self.ships_frame.pack(pady=20)
        self.create_ship_buttons()
        
        # Right frame for controls
        self.right_frame = tk.Frame(self.main_container, bg=COLORS["background"])
        self.right_frame.pack(side=tk.RIGHT, expand=True, fill="both", padx=20)
        
        # Username entry
        tk.Label(self.right_frame, text="Username", font=("Arial", 14), 
                bg=COLORS["background"], fg=COLORS["text"]).pack(pady=(0, 10))
        self.username_entry = tk.Entry(self.right_frame, font=("Arial", 12),
                                     bg=COLORS["button"], fg=COLORS["text"])
        self.username_entry.pack()
        # Middle line
        middleline = tk.Frame(self.main_container, bg=COLORS["accent"])
        middleline.pack(side=tk.TOP, expand=True, fill="both", padx=20)

        # Start button
        self.start_button = tk.Button(self.right_frame, text="Find Game",
                                    font=("Arial", 14), bg=COLORS["accent"],
                                    fg=COLORS["text"], command=self.start_game)
        self.start_button["state"] = "disabled"
        self.start_button.pack(pady=20)
        # Orientation button
        self.orientation_button = tk.Button(self.left_frame, text="Rotate",
                                    font=("Arial", 14), bg=COLORS["accent"], width=10,
                                    fg=COLORS["text"], command=self.rotate_ships)
        self.orientation_button.place(x=290, y=550)

        # Optional label which displays wrong placement
        #self.place_ship_label = tk.Label(self.left_frame, text="",
                                         #font=("Arial", 14), fg=COLORS["accent"],
                                         #anchor="center")
        #self.place_ship_label.place(x=290, y=600)

    def create_cell(self, i: int, j: int) -> tk.Label:
        '''
        Method to create each cell
        '''
        cell = tk.Label(self.board_frame, width=4, height=2,
                       bg=COLORS["board"], relief="solid", borderwidth=1)
        cell.grid(row=i, column=j, padx=1, pady=1)
        cell.bind('<Button-1>', lambda e, x=i, y=j: self.cell_clicked(x, y))
        return cell

    def create_ship_buttons(self) -> None:
        '''
        Method to crete ship buttons in pregame screen
        '''
        # List of all available ships, easy to add or remove
        ships = [(2, "🔴🔴"), (2, "🔴🔴"), (3, "🔴🔴🔴"), (3, "🔴🔴🔴"), (4, "🔴🔴🔴🔴")]
        self.finished_ships = []
        for length, symbol in ships:
            ship = DraggableShip(self.ships_frame, length, self,
                               text=symbol, font=("Arial", 14),
                               bg=COLORS["button"], fg=COLORS["text"],
                               padx=10, pady=5)
            ship.pack(side=tk.LEFT, padx=5)
            ship._original_x = ship.winfo_x()
            ship._original_y = ship.winfo_y()
            self.finished_ships.append(ship)


    def rotate_ships(self) -> None:
        '''
        Method for all ships to rotate
        '''
        for s in self.finished_ships:
            s.toggle_orientation()

    def place_ship(self, row: int, col: int, length: int, orientation="horizontal") -> bool:
        '''
        Method to place a ship on the board
        '''
        
        def are_cells_around_free(r: int, c: int, l: int, orient: str) -> bool:
            '''
            Function to check adjacent cells for ships
            '''
            adjacent_offsets = [(-1, -1), (-1, 0), (-1, 1),
                                (0, -1),           (0, 1),
                                (1, -1), (1, 0), (1, 1)]
            for i in range(l):
                check_row = r + (i if orient == "vertical" else 0)
                check_col = c + (i if orient == "horizontal" else 0)

                if not (0 <= check_row < 10 and 0 <= check_col < 10) or self.field[check_row][check_col] != " ":
                    #self.place_ship_label.configure(text="Wrong placement...")
                    return False

                for dr, dc in adjacent_offsets:
                    nr, nc = check_row + dr, check_col + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and self.field[nr][nc] != " ":
                        #self.place_ship_label.configure(text="Wrong placement...")
                        return False
            return True

        ship_cells = []

        # Check board for horizontal mode
        if orientation == "horizontal":
            if col + length > 10 or any(self.field[row][col + i] != " "  or not are_cells_around_free(row, col, length, "horizontal") for i in range(length)):
                return False
            # Placing horizontal ship
            for i in range(length):
                self.field[row][col + i] = "o"
                self.cells[row][col + i].configure(bg=COLORS["accent"])
                ship_cells.append((row, col + i))

        # Check board for vertical mode
        elif orientation == "vertical":
            if row + length > 10 or any(self.field[row + i][col] != " " or not are_cells_around_free(row, col, length, "vertical") for i in range(length)):
                return False
            # Placing vertical ship
            for i in range(length):
                self.field[row + i][col] = "o"
                self.cells[row + i][col].configure(bg=COLORS["accent"])
                ship_cells.append((row + i, col))

        self.placed_ships.append({"cells": ship_cells, "length": length, "orientation": orientation})

        # Activate start_button if enough ships are placed
        if sum(row.count("o") for row in self.field) >= 10:
            self.start_button.configure(state="normal")
        return True

    def cell_clicked(self, row: int, col: int) -> None:
        '''
        Method for handling clicks on the board to remove a ship
        '''
        # Check if cell is occupied by ship and calling for remove if true
        for ship in self.placed_ships:
            if (row, col) in ship["cells"]:
                self.remove_ship(ship)
                break

    def remove_ship(self, ship: dict) -> None:
        '''
        Method for removing a ship from the board
        '''

        # Resetting the cells of the ship
        for row, col in ship["cells"]:
            self.field[row][col] = " "
            self.cells[row][col].configure(bg=COLORS["board"])

        # Creating a new ship with the same data as the removed ship
        draggable_ship = DraggableShip(
            self.ships_frame, ship["length"], self, orientation=self.current_placing_rotation,
            text="🔴" * ship["length"] if self.current_placing_rotation == "horizontal" else "\n".join("🔴" for _ in range(ship["length"])),
            font=("Arial", 14),
            bg=COLORS["button"], fg=COLORS["text"],
            padx=10, pady=5
        )
        # Placing the new ship and adding it to the list of placeable ships
        draggable_ship.pack(side=tk.LEFT, padx=5, pady=5)
        self.placed_ships.remove(ship)
        self.finished_ships.append(draggable_ship)

    def start_game(self) -> None:
        '''
        Method for getting the username and then initializing a thread for the server connection
        '''
        username = self.username_entry.get()
        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return
        # A thread is used so the gui is still available while the other thread awaits an answer from the server
        threading.Thread(target=self.connect_to_server, args=(username,), daemon=True).start()

    def connect_to_server(self, username: str) -> None:
        '''
        Method for a first connection to the server, adress: 127.0.0.1, port: 5000
        '''
        # Creating socket for server interaction
        self.komm_s = socket.socket()
        try:
            # Connecting to server and sending the username
            self.komm_s.connect(('127.0.0.1', 5000))
            self.send_str(username)
            # Changing the UI to display the current phase of game finding
            self.start_button.configure(text="Finding game...")
            self.start_button["state"] = "disabled"
            # Waiting for server response and game start
            response = self.receive_str()
            if response == "game start":
                # Updating stage and communication with server
                self.game_active = True
                opponent_name = self.receive_str()
                self.send_str(str(self.field))
                self.setup_game_screen(opponent_name)
                threading.Thread(target=self.game_loop, daemon=True).start()
            # Error handling
            else:
                messagebox.showerror("Error", f"Unexpected response: {response}")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def setup_game_screen(self, opponent_name: str) -> None:
        '''
        Setting up the gui for the game and deleting previous lobby elements
        '''
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()
            
        # Create game container
        self.game_container = tk.Frame(self, bg=COLORS["background"])
        self.game_container.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Header with turn indicator
        self.header_frame = tk.Frame(self.game_container, bg=COLORS["background"])
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.turn_label = tk.Label(self.header_frame, text="Waiting for opponent...",
                                 font=("Arial", 20, "bold"),
                                 bg=COLORS["background"], fg=COLORS["accent"])
        self.turn_label.pack()
        
        # Game boards
        self.boards_frame = tk.Frame(self.game_container, bg=COLORS["background"])
        self.boards_frame.pack(expand=True, fill="both")
        
        # Your board
        your_board_frame = tk.Frame(self.boards_frame, bg=COLORS["background"])
        your_board_frame.pack(side=tk.LEFT, expand=True, padx=20)
        tk.Label(your_board_frame, text="Your Fleet",
                font=("Arial", 16), bg=COLORS["background"],
                fg=COLORS["text"]).pack(pady=(0, 10))
        self.your_board = self.create_board(your_board_frame, is_opponent=False)
        # Loading the ships on the board, so the player can see his own placed ships
        for i in range(10):
            for j in range(10):
                if self.field[i][j] == "o":
                    self.your_board[i][j].configure(bg=COLORS["accent"])
        
        
        # Opponent's board
        opponent_board_frame = tk.Frame(self.boards_frame, bg=COLORS["background"])
        opponent_board_frame.pack(side=tk.RIGHT, expand=True, padx=20)
        tk.Label(opponent_board_frame, text=f"{opponent_name}'s Fleet",
                font=("Arial", 16), bg=COLORS["background"],
                fg=COLORS["text"]).pack(pady=(0, 10))
        self.opponent_board = self.create_board(opponent_board_frame, is_opponent=True)
        
        # Launch button
        self.launch_button = tk.Button(self.game_container, text="LAUNCH",
                                     font=("Arial", 20, "bold"),
                                     bg=COLORS["accent"], fg=COLORS["text"],
                                     command=self.make_move,
                                     state="disabled",
                                     relief="raised",
                                     borderwidth=5,
                                     width=15, height=2)
        self.launch_button.pack(pady=20)

    def create_board(self, parent: tk.Label, is_opponent=False) -> list:
        '''
        Creating board based on received message from server
        '''
        # Creating frame for board
        board_frame = tk.Frame(parent, bg=COLORS["background"])
        board_frame.pack()
        # Creating cells from the board
        cells = []
        for i in range(10):
            row = []
            for j in range(10):
                cell = tk.Label(board_frame, width=4, height=2,
                              bg=COLORS["board"], relief="solid", borderwidth=1)
                cell.grid(row=i, column=j, padx=1, pady=1)
                if is_opponent:
                    cell.bind('<Button-1>', lambda e, x=i, y=j: self.target_cell(x, y))
                row.append(cell)
            cells.append(row)
        return cells

    def target_cell(self, row: int, col: int) -> None:
        '''
        target selection method
        '''
        # Only possible if it is your turn
        if not self.game_active or self.launch_button["state"] == "disabled":
            return
            
        # Reset previous selection
        if hasattr(self, 'selected_cell'):
            if self.selected_cell:
                old_row, old_col = self.selected_cell
                self.opponent_board[old_row][old_col].configure(
                    bg=COLORS["board"])
                
                # Reset cursor for all cells
                for r in self.opponent_board:
                    for cell in r:
                        cell.configure(cursor="")
        
        # Set new selection
        self.selected_cell = (row, col)
        self.opponent_board[row][col].configure(bg=COLORS["accent"])
        self.launch_button.configure(state="normal")
        
        # Change cursor for opponent's board cells when it's player's turn
        if self.launch_button["state"] != "disabled":
            for r in self.opponent_board:
                for cell in r:
                    if self.target_cursor:
                        cell.configure(cursor="crosshair")
                    else:
                        cell.configure(cursor="target")

    def play_alert(self) -> None:
        '''
        Method for playing alerts and visiual effects at start of players turn
        '''
        if self.specialmode:
            try:
                # Pygame for playing sounds
                pygame.mixer.music.load(ASSETS["siren"])
                pygame.mixer.music.play()
                
                # Enhanced flash effect
                def flash():
                    flash_colors = ["#0000FF", "#000080", "#0000FF", "#000080"]
                    flash_durations = [0.3, 0.2, 0.3, 0.2]
                    
                    for color, duration in zip(flash_colors, flash_durations):
                        # Flash the main window
                        self.configure(bg=color)
                        
                        # Flash the board frames
                        for frame in [self.game_container, self.boards_frame]:
                            frame.configure(bg=color)
                        
                        # Method intigrated in tkinter
                        self.update()
                        time.sleep(duration)
                        
                        # Reset colors
                        self.configure(bg=COLORS["background"])
                        for frame in [self.game_container, self.boards_frame]:
                            frame.configure(bg=COLORS["background"])
                        
                        self.update()
                        time.sleep(duration)
                # Thread for flashing, therefore not affecting the rest of the game
                threading.Thread(target=flash, daemon=True).start()
            # Error handling
            except Exception as e:
                print(f"Error playing alert: {e}")

    def play_video(self, video_type: str) -> None:
        '''
        Method for playing videos if special mode is activated
        '''
        if self.specialmode:
            try:
                # Stop any existing playback first
                self.stop_current_playback()
                
                # Wait a brief moment to ensure cleanup is complete
                self.after(100)  # small delay for cleanup
                
                # Paths for video and duration in milliseconds
                video_path = ASSETS["videos"][video_type]
                duration = VIDEOLENGTHS[video_type] * 1000 

                # Store current video type
                self.current_video = video_type
                    
                # Create a new fullscreen window for the video
                video_window = tk.Toplevel(self)
                video_window.attributes("-fullscreen", True)
                video_window.title(video_type.capitalize())
                
                # Create a label to display the video
                video_label = tk.Label(video_window)
                video_label.pack(expand=True, fill="both")

                # Initialize MediaPlayer and video capture
                self.player = MediaPlayer(video_path)
                self.cap = cv2.VideoCapture(video_path)
                
                if not self.cap.isOpened():
                    raise Exception(f"Failed to open video file: {video_path}")

                # Get video properties
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                frame_delay = int(1000 / fps)  # Convert fps to milliseconds delay
                
                self.playing = True

                def update_frame():
                    '''
                    Function for updating frames
                    '''
                    if not self.playing or not self.cap or not self.cap.isOpened():
                        on_close()
                        return

                    ret, frame = self.cap.read()
                    if not ret:
                        on_close()
                        return

                    # Resize frame to fit the screen while maintaining aspect ratio
                    screen_width = video_window.winfo_screenwidth()
                    screen_height = video_window.winfo_screenheight()
                    
                    # Calculate aspect ratio
                    height, width = frame.shape[:2]
                    aspect_ratio = width / height
                    
                    # Calculate new dimensions
                    if screen_width / screen_height > aspect_ratio:
                        new_width = int(screen_height * aspect_ratio)
                        new_height = screen_height
                    else:
                        new_width = screen_width
                        new_height = int(screen_width / aspect_ratio)
                    
                    # Apply changes to the video/frame
                    frame = cv2.resize(frame, (new_width, new_height))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = Image.fromarray(frame)
                    frame = ImageTk.PhotoImage(frame)

                    # Only update if window still exists
                    if video_window.winfo_exists():
                        video_label.configure(image=frame)
                        video_label.image = frame  # Keep a reference

                        if self.playing:
                            video_window.after(frame_delay, update_frame)

                def on_close():
                    '''
                    Function for stopping playback
                    '''
                    self.stop_current_playback()
                    if video_window.winfo_exists():
                        video_window.destroy()

                # Handle window closing
                video_window.protocol("WM_DELETE_WINDOW", on_close)

                # Start playback
                if self.player:
                    self.player.set_pause(False)
                update_frame()

                # Auto-close after duration
                video_window.after(duration, on_close)

            # Error handling
            except Exception as e:
                print(f"Error playing video: {e}")
                self.stop_current_playback()
                if 'video_window' in locals() and video_window.winfo_exists():
                    video_window.destroy()

    def stop_current_playback(self) -> None:
        """Safely stop current playback and cleanup resources."""
        if self.specialmode:
            self.playing = False
            
            # Cleanup MediaPlayer
            if self.player:
                try:
                    self.player.set_pause(True)
                    self.player.close_player()
                    self.player = None
                except Exception as e:
                    print(f"Error cleaning up player: {e}")

            # Cleanup Video Capture
            if self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                except Exception as e:
                    print(f"Error cleaning up video capture: {e}")
            
            self.current_video = None


    def game_loop(self) -> None:
        '''
        Main game loop
        '''
        while self.game_active:
            try:
                message = self.receive_str()
                print(f"Received message: {message}")  # Debug print
                
                # Handling of different server responses
                # Player turn
                if message == "your turn":
                    self.turn_label.configure(text="Your Turn!")
                    self.launch_button.configure(state="normal")
                    self.play_alert()
                    for row in self.opponent_board:
                        for cell in row:
                            if self.target_cursor:
                                cell.configure(cursor="crosshair")
                            else:
                                cell.configure(cursor="target")
                # Opponent turn
                elif message == "opponent turn":
                    self.turn_label.configure(text="Opponent's Turn...")
                    self.launch_button.configure(state="disabled")
                    for row in self.opponent_board:
                        for cell in row:
                            cell.configure(cursor="")

                # Continue message
                elif message == "continue":
                    pass

                # Game end - win
                elif message == "winner":
                    self.game_active = False
                    
                    self.turn_label.configure(text="Victory!")
                    if self.specialmode:
                        self.play_video("win")
                        self.after(60000, self.reset_game)
                    self.after(500, self.reset_game)

                # Game end - loss
                elif message == "looser":
                    self.game_active = False
                    self.turn_label.configure(text="Defeat!")
                    if self.specialmode:
                        self.play_video("lose")
                        self.after(60000, self.reset_game)  
                    self.after(500, self.reset_game)

                # Handle the field updates
                elif isinstance(eval(message), dict):
                    fields = eval(message)
                    # Update own field
                    for i in range(10):
                        for j in range(10):
                            value = fields['own'][i][j]
                            if value == "s":
                                self.your_board[i][j].configure(bg=COLORS["hit"])
                            elif value == "x":
                                self.your_board[i][j].configure(bg=COLORS["miss"])
                            elif value == "o":
                                self.your_board[i][j].configure(bg=COLORS["accent"])
                    
                    # Update opponent field
                    for i in range(10):
                        for j in range(10):
                            value = fields['opponent'][i][j]
                            if value == "s":
                                self.opponent_board[i][j].configure(bg=COLORS["hit"])
                                if self.testcell == (i, j) and self.game_active and self.specialmode:
                                    self.play_video("hit")
                                    #only waiting for the video to end before the next move happens if special mode is activated
                                    time.sleep(VIDEOLENGTHS["hit"])
                            elif value == "x":
                                self.opponent_board[i][j].configure(bg=COLORS["miss"])
                                if self.testcell == (i, j) and self.game_active and self.specialmode:
                                    self.play_video("miss")
                                    #only waiting for the video to end before the next move happens if specialmode is activate
                                    time.sleep(VIDEOLENGTHS["miss"])


                
            # Error handling    
            except Exception as e:
                print(f"Error in game loop: {e}")
                self.game_active = False
                break

    def make_move(self) -> None:
        '''
        Method for player turn
        '''

        # Error if no cell is selected as target
        if not hasattr(self, 'selected_cell') or not self.selected_cell:
            messagebox.showinfo("Select Target", "Please select a target cell first!")
            return
            
        row, col = self.selected_cell
        try:
            # Format move command to match server expectations
            # Server expects a tuple string like "(row,column)"
            move_cmd = str((row, col))
            self.send_str(move_cmd)
            
            # Disable launch button and reset selection
            self.launch_button.configure(state="disabled")
            self.opponent_board[row][col].configure(bg=COLORS["board"])
            
            # Reset cursor
            for r in self.opponent_board:
                for cell in r:
                    cell.configure(cursor="")
            
            self.testcell = self.selected_cell

            self.selected_cell = None
            
        # Error handling    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send move: {e}")

    def reset_game(self) -> None:
        '''
        Method for resetting game after finished round
        '''
        try:
            # Closing socket
            self.komm_s.close()
        except:
            pass
        # Destroy method, included in tkinter library
        self.destroy()
        # Restart in homescreen, not changing the selected mode
        BattleshipGame(self.specialmode).mainloop()

    def send_str(self, data: str) -> None:
        '''
        Basic method for server integration / sending messages
        '''
        try:
            self.komm_s.sendall(bytes(data, 'utf-8'))
            self.komm_s.sendall(bytes([0]))
        except Exception as e:
            raise Exception(f"Failed to send data: {e}")

    def receive_str(self) -> str:
        '''
        Basic method for server integration / receiving messages
        '''
        try:
            data_bytes = bytes()
            end_byte = bytes([0])
            
            while True:
                chunk = self.komm_s.recv(1)
                if chunk == end_byte or chunk == bytes([]):
                    break
                data_bytes += chunk
            
            return str(data_bytes, 'utf-8')
        except Exception as e:
            raise Exception(f"Failed to receive data: {e}")

    def __del__(self) -> None:
        '''
        Method for deleting connection towards server
        '''
        try:
            self.komm_s.close()
        except:
            pass

class SelectorWindow(tk.Tk):
    '''
    Class for starting screen and selecting whether specialmode is enabled or not and then calling the BattleshipGame method
    '''
    def __init__(self) -> None:
        '''
        Initializing basic attributes used for this class
        '''
        super().__init__()
        self.title("Select your Client")
        self.geometry("1200x800")
        self.configure(bg=COLORS["background"])
        # Setting up UI
        self.setupUI()
    
    def setupUI(self) -> None:
        '''
        Method for setting up the UI
        '''
        # Frame 
        self.selector_frame = tk.Frame(self, bg=COLORS["background"])
        self.selector_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self.headingLabel = tk.Label(self.selector_frame, text="Choose your Client!", font=("Arial", 14), bg=COLORS["background"], fg=COLORS["text"]).pack(pady=(0,20))
        # Button for normal mode
        self.c1_button = tk.Button(self.selector_frame, text="Normal Client",
                                   font=("Arial", 20, "bold"),
                                   activebackground=COLORS["board"], activeforeground=COLORS["accent"],
                                   command=self.normalClient,
                                   state="active",
                                   relief="raised",
                                   borderwidth=5,
                                   width=15, height=2)
        self.c1_button.pack(padx=50, pady=50)
        self.c1_button.bind('<Enter>', lambda e: self.on_hover(self.c1_button))
        self.c1_button.bind('<Leave>', lambda e: self.on_leave(self.c1_button))

        # Button for special mode
        self.c2_button = tk.Button(self.selector_frame, text="Special Client",
                                   font=("Arial", 20, "bold"),
                                   activebackground=COLORS["board"], activeforeground=COLORS["accent"],
                                   command=self.specialClient,
                                   state="active",
                                   relief="raised",
                                   borderwidth=5,
                                   width=15, height=2)
        self.c2_button.pack(pady=50)
        self.c2_button.bind('<Enter>', lambda e: self.on_hover(self.c2_button))
        self.c2_button.bind('<Leave>', lambda e: self.on_leave(self.c2_button))

    def on_hover(self, button: tk.Button) -> None:
        '''
        Method for interaction on hover -> starting of hover
        '''
        button.config(bg=COLORS["accent"], fg=COLORS["board"])

    def on_leave(self, button: tk.Button) -> None:
        '''
        Method for interaction on hover -> leaving hover
        '''
        button.config(bg=COLORS["board"], fg=COLORS["accent"])

    def normalClient(self) -> None:
        '''
        Method for starting game in normal mode
        '''
        self.destroy()
        # Global function start_game
        start_game(specialmode=False)

    def specialClient(self) -> None:
        '''
        Method for starting game in special mode
        '''
        self.destroy()
        # Global function start_game
        start_game(specialmode=True)

def start_game(specialmode: bool) -> None:
    '''
    Basic function for creating game object and starting the game
    '''
    game = BattleshipGame(specialmode)
    game.mainloop()        


if __name__ == "__main__":
    # Create assets directory if it doesn't exist
    if not os.path.exists('assets'):
        os.makedirs('assets')
        print("Created assets directory. Please add the following files:")
        print("- assets/cursor.png (cursor image)")
        print("- assets/siren.wav (alert sound)")
        print("- assets/hit.mp4 (hit animation)")
        print("- assets/miss.mp4 (miss animation)")
        print("- assets/victory.mp4 (win animation)")
        print("- assets/defeat.mp4 (lose animation)")
    
    selctorWindow = SelectorWindow()
    selctorWindow.mainloop()

    #game = BattleshipGame(True)
    #game.mainloop()