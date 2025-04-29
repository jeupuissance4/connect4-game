import pygame
import sys
import random
import socket
import threading
import numpy as np
from collections import deque
import time


pygame.init()


BLUE = (70, 130, 180)
LIGHT_BLUE = (173, 216, 230)
WHITE = (245, 245, 245)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLACK = (30, 30, 30)
RED = (220, 80, 80)
YELLOW = (240, 230, 140)
GREEN = (100, 180, 100)


ROW_COUNT = 6
COLUMN_COUNT = 7
SQUARESIZE = 100
RADIUS = int(SQUARESIZE/2 - 5)
width = COLUMN_COUNT * SQUARESIZE
height = (ROW_COUNT+1) * SQUARESIZE
size = (width, height)


font = pygame.font.SysFont("Arial", 30)
large_font = pygame.font.SysFont("Arial", 50)

class Connect4Game:
    def __init__(self):
        self.board = np.zeros((ROW_COUNT, COLUMN_COUNT))
        self.game_over = False
        self.turn = 0  # 0 for player 1, 1 for player 2
        self.winner = None
        self.mode = None  # Will be set to "1v1", "1vAI", or "online"
        self.ai_difficulty = "medium"  # easy, medium, hard
        self.opponent_move = None  # For online play
        self.server_socket = None
        self.client_socket = None
        self.is_host = False

    def reset(self):
        self.board = np.zeros((ROW_COUNT, COLUMN_COUNT))
        self.game_over = False
        self.turn = 0
        self.winner = None

    def drop_piece(self, row, col, piece):
        self.board[row][col] = piece

    def is_valid_location(self, col):
        return self.board[ROW_COUNT-1][col] == 0

    def get_next_open_row(self, col):
        for r in range(ROW_COUNT):
            if self.board[r][col] == 0:
                return r

    def winning_move(self, piece):
        # Check horizontal locations
        for c in range(COLUMN_COUNT-3):
            for r in range(ROW_COUNT):
                if self.board[r][c] == piece and self.board[r][c+1] == piece and self.board[r][c+2] == piece and self.board[r][c+3] == piece:
                    return True

      
        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT-3):
                if self.board[r][c] == piece and self.board[r+1][c] == piece and self.board[r+2][c] == piece and self.board[r+3][c] == piece:
                    return True

        
        for c in range(COLUMN_COUNT-3):
            for r in range(ROW_COUNT-3):
                if self.board[r][c] == piece and self.board[r+1][c+1] == piece and self.board[r+2][c+2] == piece and self.board[r+3][c+3] == piece:
                    return True

        
        for c in range(COLUMN_COUNT-3):
            for r in range(3, ROW_COUNT):
                if self.board[r][c] == piece and self.board[r-1][c+1] == piece and self.board[r-2][c+2] == piece and self.board[r-3][c+3] == piece:
                    return True
        return False

    def is_board_full(self):
        return all(self.board[ROW_COUNT-1][c] != 0 for c in range(COLUMN_COUNT))

    def make_move(self, col):
        if self.game_over or not self.is_valid_location(col):
            return False

        row = self.get_next_open_row(col)
        piece = self.turn + 1
        self.drop_piece(row, col, piece)

        if self.winning_move(piece):
            self.game_over = True
            self.winner = piece
        elif self.is_board_full():
            self.game_over = True
            self.winner = 0  # Draw

        self.turn = (self.turn + 1) % 2
        return True

    def ai_move(self):
        if self.game_over:
            return

        if self.ai_difficulty == "easy":
            return self.random_ai()
        elif self.ai_difficulty == "medium":
            return self.medium_ai()
        else:
            return self.hard_ai()

    def random_ai(self):
        valid_locations = [col for col in range(COLUMN_COUNT) if self.is_valid_location(col)]
        if valid_locations:
            col = random.choice(valid_locations)
            self.make_move(col)
            return col
        return None

    def medium_ai(self):
       
        for col in range(COLUMN_COUNT):
            if self.is_valid_location(col):
                temp_row = self.get_next_open_row(col)
                self.drop_piece(temp_row, col, 2)
                if self.winning_move(2):
                    self.board[temp_row][col] = 0  # Undo move
                    self.make_move(col)
                    return col
                self.board[temp_row][col] = 0  # Undo move

        
        for col in range(COLUMN_COUNT):
            if self.is_valid_location(col):
                temp_row = self.get_next_open_row(col)
                self.drop_piece(temp_row, col, 1)
                if self.winning_move(1):
                    self.board[temp_row][col] = 0  # Undo move
                    self.make_move(col)
                    return col
                self.board[temp_row][col] = 0  # Undo move

       
        return self.random_ai()

    def hard_ai(self):
        
        best_score = -float('inf')
        best_col = self.random_ai()  # Default to random if something goes wrong

        for col in range(COLUMN_COUNT):
            if self.is_valid_location(col):
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, 2)
                score = self.minimax(self.board, 3, -float('inf'), float('inf'), False)
                self.board[row][col] = 0  # Undo move
                if score > best_score:
                    best_score = score
                    best_col = col

        self.make_move(best_col)
        return best_col

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        valid_locations = [col for col in range(COLUMN_COUNT) if self.is_valid_location(col)]
        is_terminal = self.winning_move(1) or self.winning_move(2) or len(valid_locations) == 0

        if depth == 0 or is_terminal:
            if self.winning_move(2):
                return 100000
            elif self.winning_move(1):
                return -100000
            else:
                return 0

        if maximizing_player:
            value = -float('inf')
            for col in valid_locations:
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, 2)
                new_score = self.minimax(board, depth-1, alpha, beta, False)
                self.board[row][col] = 0
                value = max(value, new_score)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = float('inf')
            for col in valid_locations:
                row = self.get_next_open_row(col)
                self.drop_piece(row, col, 1)
                new_score = self.minimax(board, depth-1, alpha, beta, True)
                self.board[row][col] = 0
                value = min(value, new_score)
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    def start_server(self, port=5555):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(1)
        self.is_host = True
        
        def accept_connection():
            self.client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            
            while not self.game_over:
                try:
                    data = self.client_socket.recv(1024).decode()
                    if data:
                        col = int(data)
                        self.opponent_move = col
                except:
                    break
        
        threading.Thread(target=accept_connection, daemon=True).start()

    def connect_to_server(self, host, port=5555):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        
        def receive_moves():
            while not self.game_over:
                try:
                    data = self.client_socket.recv(1024).decode()
                    if data:
                        col = int(data)
                        self.opponent_move = col
                except:
                    break
        
        threading.Thread(target=receive_moves, daemon=True).start()

    def send_move(self, col):
        if self.client_socket:
            try:
                self.client_socket.send(str(col).encode())
            except:
                pass

def draw_board(screen, game):
    screen.fill(BLUE)
    
   
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            pygame.draw.rect(screen, LIGHT_BLUE, (c*SQUARESIZE, (r+1)*SQUARESIZE, SQUARESIZE, SQUARESIZE))
            pygame.draw.circle(screen, WHITE, (int(c*SQUARESIZE+SQUARESIZE/2), int((r+1)*SQUARESIZE+SQUARESIZE/2)), RADIUS)
    
   
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            if game.board[r][c] == 1:
                pygame.draw.circle(screen, RED, (int(c*SQUARESIZE+SQUARESIZE/2), height-int(r*SQUARESIZE+SQUARESIZE/2)), RADIUS)
            elif game.board[r][c] == 2:
                pygame.draw.circle(screen, YELLOW, (int(c*SQUARESIZE+SQUARESIZE/2), height-int(r*SQUARESIZE+SQUARESIZE/2)), RADIUS)
    
   
    posx = pygame.mouse.get_pos()[0]
    if game.turn == 0:
        pygame.draw.circle(screen, RED, (posx, int(SQUARESIZE/2)), RADIUS)
    else:
        if game.mode == "1v1":
            pygame.draw.circle(screen, YELLOW, (posx, int(SQUARESIZE/2)), RADIUS)
    
  
    if game.game_over:
        if game.winner == 1:
            text = large_font.render("Red wins!", True, RED)
        elif game.winner == 2:
            text = large_font.render("Yellow wins!", True, YELLOW)
        else:
            text = large_font.render("It's a draw!", True, WHITE)
        screen.blit(text, (width//2 - text.get_width()//2, 10))
    else:
        if game.mode == "online" and ((game.is_host and game.turn == 1) or (not game.is_host and game.turn == 0)):
            text = font.render("Waiting for opponent...", True, WHITE)
            screen.blit(text, (width//2 - text.get_width()//2, 10))
        else:
            if game.turn == 0:
                text = font.render("Red's turn", True, RED)
            else:
                if game.mode == "1v1":
                    text = font.render("Yellow's turn", True, YELLOW)
                else:
                    text = font.render("AI's turn", True, YELLOW)
            screen.blit(text, (width//2 - text.get_width()//2, 10))
    
    pygame.display.update()

def show_menu(screen):
    screen.fill(BLUE)
    
    title = large_font.render("Connect 4", True, WHITE)
    screen.blit(title, (width//2 - title.get_width()//2, 50))
    
    
    pygame.draw.rect(screen, GREEN, (width//2 - 150, 150, 300, 60))
    mode1 = font.render("1 vs 1 (Local)", True, BLACK)
    screen.blit(mode1, (width//2 - mode1.get_width()//2, 165))
    
    pygame.draw.rect(screen, GREEN, (width//2 - 150, 230, 300, 60))
    mode2 = font.render("1 vs Computer", True, BLACK)
    screen.blit(mode2, (width//2 - mode2.get_width()//2, 245))
    
    pygame.draw.rect(screen, GREEN, (width//2 - 150, 310, 300, 60))
    mode3 = font.render("Online Play", True, BLACK)
    screen.blit(mode3, (width//2 - mode3.get_width()//2, 325))
    
    
    pygame.draw.rect(screen, GRAY, (width//2 - 150, 400, 300, 40))
    difficulty_text = font.render(f"AI Difficulty: {game.ai_difficulty}", True, BLACK)
    screen.blit(difficulty_text, (width//2 - difficulty_text.get_width()//2, 410))
    
    pygame.display.update()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                
                if 150 <= pos[1] <= 210:  # 1v1
                    if width//2 - 150 <= pos[0] <= width//2 + 150:
                        game.mode = "1v1"
                        return
                
                elif 230 <= pos[1] <= 290:  # 1vAI
                    if width//2 - 150 <= pos[0] <= width//2 + 150:
                        game.mode = "1vAI"
                        return
                
                elif 310 <= pos[1] <= 370:  # Online
                    if width//2 - 150 <= pos[0] <= width//2 + 150:
                        show_online_menu(screen)
                        return
                
               
                elif 400 <= pos[1] <= 440:
                    if width//2 - 150 <= pos[0] <= width//2 + 150:
                        
                        if game.ai_difficulty == "easy":
                            game.ai_difficulty = "medium"
                        elif game.ai_difficulty == "medium":
                            game.ai_difficulty = "hard"
                        else:
                            game.ai_difficulty = "easy"
                        
                        
                        show_menu(screen)
                        return

def show_online_menu(screen):
    screen.fill(BLUE)
    
    title = large_font.render("Online Play", True, WHITE)
    screen.blit(title, (width//2 - title.get_width()//2, 50))
    
    
    pygame.draw.rect(screen, GREEN, (width//2 - 150, 150, 300, 60))
    host_text = font.render("Host Game", True, BLACK)
    screen.blit(host_text, (width//2 - host_text.get_width()//2, 165))
    
    
    pygame.draw.rect(screen, GREEN, (width//2 - 150, 230, 300, 60))
    join_text = font.render("Join Game", True, BLACK)
    screen.blit(join_text, (width//2 - join_text.get_width()//2, 245))
    
    
    pygame.draw.rect(screen, RED, (width//2 - 150, 310, 300, 60))
    back_text = font.render("Back", True, BLACK)
    screen.blit(back_text, (width//2 - back_text.get_width()//2, 325))
    
    pygame.display.update()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                if 150 <= pos[1] <= 210:  # Host game
                    if width//2 - 150 <= pos[0] <= width//2 + 150:
                        game.mode = "online"
                        game.start_server()
                        return
                
                elif 230 <= pos[1] <= 290:  # Join game
                    if width//2 - 150 <= pos[0] <= width//2 + 150:
                        show_join_menu(screen)
                        return
                
                elif 310 <= pos[1] <= 370:  # Back
                    show_menu(screen)
                    return

def show_join_menu(screen):
    screen.fill(BLUE)
    
    title = large_font.render("Join Game", True, WHITE)
    screen.blit(title, (width//2 - title.get_width()//2, 50))
    
   
    input_rect = pygame.Rect(width//2 - 150, 150, 300, 50)
    pygame.draw.rect(screen, WHITE, input_rect, 2)
    
    font_small = pygame.font.SysFont("Arial", 24)
    ip_text = font_small.render("Enter host IP:", True, WHITE)
    screen.blit(ip_text, (width//2 - ip_text.get_width()//2, 120))
    
    
    pygame.draw.rect(screen, GREEN, (width//2 - 150, 220, 300, 60))
    join_text = font.render("Join", True, BLACK)
    screen.blit(join_text, (width//2 - join_text.get_width()//2, 235))
    
    
    pygame.draw.rect(screen, RED, (width//2 - 150, 300, 300, 60))
    back_text = font.render("Back", True, BLACK)
    screen.blit(back_text, (width//2 - back_text.get_width()//2, 315))
    
    pygame.display.update()
    
    input_active = True
    ip_address = ""
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                if input_rect.collidepoint(pos):
                    input_active = True
                else:
                    input_active = False
                
                if 220 <= pos[1] <= 280:  # Join
                    if width//2 - 150 <= pos[0] <= width//2 + 150:
                        if ip_address:
                            game.mode = "online"
                            try:
                                game.connect_to_server(ip_address)
                                return
                            except:
                                error_text = font.render("Connection failed!", True, RED)
                                screen.blit(error_text, (width//2 - error_text.get_width()//2, 380))
                                pygame.display.update()
                                pygame.time.delay(2000)
                                show_join_menu(screen)
                                return
                
                elif 300 <= pos[1] <= 360:  # Back
                    show_online_menu(screen)
                    return
            
            if event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    ip_address = ip_address[:-1]
                else:
                    ip_address += event.unicode
        
        
        pygame.draw.rect(screen, BLUE, input_rect)
        pygame.draw.rect(screen, WHITE, input_rect, 2)
        ip_surface = font_small.render(ip_address, True, WHITE)
        screen.blit(ip_surface, (input_rect.x + 5, input_rect.y + 15))
        
        pygame.display.update()

def show_game_over(screen):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                return  # Return to main menu

def main():
    global game, screen
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Connect 4")
    
    game = Connect4Game()
    
    while True:
        show_menu(screen)
        game.reset()
        
        # Main game loop
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                    if game.mode == "online":
                        if (game.is_host and game.turn == 0) or (not game.is_host and game.turn == 1):
                            posx = event.pos[0]
                            col = int(posx // SQUARESIZE)
                            
                            if game.is_valid_location(col):
                                row = game.get_next_open_row(col)
                                game.drop_piece(row, col, game.turn + 1)
                                
                                if game.winning_move(game.turn + 1):
                                    game.game_over = True
                                    game.winner = game.turn + 1
                                elif game.is_board_full():
                                    game.game_over = True
                                    game.winner = 0
                                
                                game.send_move(col)
                                game.turn = (game.turn + 1) % 2
                    else:
                        if game.turn == 0 or game.mode == "1v1":
                            posx = event.pos[0]
                            col = int(posx // SQUARESIZE)
                            game.make_move(col)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r and game.game_over:
                        game.reset()
            
           
            if not game.game_over and game.mode == "1vAI" and game.turn == 1:
                pygame.time.delay(500)  # Small delay for better UX
                game.ai_move()
            
            
            if not game.game_over and game.mode == "online" and game.opponent_move is not None:
                col = game.opponent_move
                game.opponent_move = None
                game.make_move(col)
            
            draw_board(screen, game)
            clock.tick(60)
        
        
        draw_board(screen, game)
        show_game_over(screen)

if __name__ == "__main__":
    main()
