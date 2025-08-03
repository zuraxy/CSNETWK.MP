import logging
import time
import uuid
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger('lsnp.game')

class TicTacToe:
    """
    Implementation of Tic-Tac-Toe game for the LSNP protocol.
    Manages game state, moves, and win detection.
    """
    
    # Game status constants
    STATUS_WAITING = 'waiting'    # Waiting for opponent to accept
    STATUS_ACTIVE = 'active'      # Game in progress
    STATUS_COMPLETED = 'completed'  # Game finished
    STATUS_CANCELLED = 'cancelled'  # Game cancelled
    
    # Game result constants
    RESULT_WIN = 'win'
    RESULT_LOSS = 'loss'
    RESULT_DRAW = 'draw'
    RESULT_CANCELLED = 'cancelled'
    
    # Player symbols
    SYMBOL_X = 'X'
    SYMBOL_O = 'O'
    SYMBOL_EMPTY = ' '
    
    def __init__(self, game_id: str = None, initiator: str = None, opponent: str = None):
        """
        Initialize a new Tic-Tac-Toe game.
        
        Args:
            game_id: Unique game identifier (generated if None)
            initiator: User ID of the game initiator
            opponent: User ID of the opponent
        """
        self.game_id = game_id or f"game-{uuid.uuid4().hex[:8]}"
        self.initiator = initiator
        self.opponent = opponent
        self.created_at = int(time.time())
        self.status = self.STATUS_WAITING
        self.result = None
        self.winner = None
        
        # Initialize empty 3x3 board
        self.board = [[self.SYMBOL_EMPTY for _ in range(3)] for _ in range(3)]
        
        # Assign symbols (initiator is always X)
        self.initiator_symbol = self.SYMBOL_X
        self.opponent_symbol = self.SYMBOL_O
        
        # X always goes first
        self.current_turn = self.initiator
        
        logger.info(f"Game {self.game_id} created: {initiator} vs {opponent}")
    
    def accept_invitation(self) -> bool:
        """
        Accept game invitation and start the game.
        
        Returns:
            Success status
        """
        if self.status != self.STATUS_WAITING:
            logger.warning(f"Cannot accept game {self.game_id}: not in waiting status")
            return False
            
        self.status = self.STATUS_ACTIVE
        logger.info(f"Game {self.game_id} started")
        return True
    
    def cancel_game(self, user_id: str) -> bool:
        """
        Cancel a game.
        
        Args:
            user_id: User ID of the player cancelling
            
        Returns:
            Success status
        """
        if self.status in (self.STATUS_COMPLETED, self.STATUS_CANCELLED):
            logger.warning(f"Cannot cancel game {self.game_id}: already finished")
            return False
            
        if user_id not in (self.initiator, self.opponent):
            logger.warning(f"User {user_id} is not a participant in game {self.game_id}")
            return False
            
        self.status = self.STATUS_CANCELLED
        self.result = self.RESULT_CANCELLED
        logger.info(f"Game {self.game_id} cancelled by {user_id}")
        return True
    
    def make_move(self, user_id: str, row: int, col: int) -> Tuple[bool, Optional[str]]:
        """
        Make a move on the board.
        
        Args:
            user_id: User ID of the player making the move
            row: Row index (0-2)
            col: Column index (0-2)
            
        Returns:
            Tuple of (success, game_result)
        """
        # Validate game state
        if self.status != self.STATUS_ACTIVE:
            logger.warning(f"Cannot make move: game {self.game_id} is not active")
            return False, None
            
        # Validate turn
        if user_id != self.current_turn:
            logger.warning(f"Not {user_id}'s turn in game {self.game_id}")
            return False, None
            
        # Validate coordinates
        if not (0 <= row < 3 and 0 <= col < 3):
            logger.warning(f"Invalid move coordinates: ({row}, {col})")
            return False, None
            
        # Check if cell is empty
        if self.board[row][col] != self.SYMBOL_EMPTY:
            logger.warning(f"Cell ({row}, {col}) is already occupied")
            return False, None
            
        # Determine player symbol
        symbol = self.initiator_symbol if user_id == self.initiator else self.opponent_symbol
        
        # Make the move
        self.board[row][col] = symbol
        
        # Check for win or draw
        game_result = self._check_game_result()
        
        if game_result:
            self.status = self.STATUS_COMPLETED
            self.result = game_result
            
            if game_result == self.RESULT_WIN:
                self.winner = user_id
                logger.info(f"Game {self.game_id}: {user_id} wins")
            elif game_result == self.RESULT_DRAW:
                logger.info(f"Game {self.game_id}: Draw")
        else:
            # Switch turns
            self.current_turn = self.opponent if user_id == self.initiator else self.initiator
            logger.debug(f"Game {self.game_id}: Turn switches to {self.current_turn}")
        
        return True, game_result
    
    def _check_game_result(self) -> Optional[str]:
        """
        Check if the game has a winner or is a draw.
        
        Returns:
            Game result (win, draw) or None if game continues
        """
        # Check rows
        for row in self.board:
            if row[0] != self.SYMBOL_EMPTY and row[0] == row[1] == row[2]:
                return self.RESULT_WIN
        
        # Check columns
        for col in range(3):
            if (self.board[0][col] != self.SYMBOL_EMPTY and 
                self.board[0][col] == self.board[1][col] == self.board[2][col]):
                return self.RESULT_WIN
        
        # Check diagonals
        if (self.board[0][0] != self.SYMBOL_EMPTY and 
            self.board[0][0] == self.board[1][1] == self.board[2][2]):
            return self.RESULT_WIN
            
        if (self.board[0][2] != self.SYMBOL_EMPTY and 
            self.board[0][2] == self.board[1][1] == self.board[2][0]):
            return self.RESULT_WIN
        
        # Check for draw (board full)
        for row in self.board:
            if self.SYMBOL_EMPTY in row:
                return None  # Game continues
                
        return self.RESULT_DRAW
    
    def get_board_string(self) -> str:
        """
        Get a string representation of the current board.
        
        Returns:
            ASCII representation of the board
        """
        result = []
        for i, row in enumerate(self.board):
            result.append(" {} | {} | {} ".format(row[0], row[1], row[2]))
            if i < 2:
                result.append("-----------")
        return "\n".join(result)
    
    def serialize_state(self) -> Dict:
        """
        Serialize the game state for transmission.
        
        Returns:
            Dictionary with game state
        """
        # Flatten board for transmission
        flat_board = []
        for row in self.board:
            flat_board.extend(row)
            
        return {
            'game_id': self.game_id,
            'initiator': self.initiator,
            'opponent': self.opponent,
            'status': self.status,
            'turn': self.current_turn,
            'board': "".join(flat_board),
            'result': self.result,
            'winner': self.winner,
            'created_at': self.created_at
        }
    
    @classmethod
    def deserialize_state(cls, state: Dict) -> 'TicTacToe':
        """
        Create a game instance from serialized state.
        
        Args:
            state: Serialized game state
            
        Returns:
            TicTacToe instance with restored state
        """
        game = cls(
            game_id=state['game_id'],
            initiator=state['initiator'],
            opponent=state['opponent']
        )
        
        game.status = state['status']
        game.current_turn = state['turn']
        game.result = state['result']
        game.winner = state['winner']
        game.created_at = state.get('created_at', int(time.time()))
        
        # Restore board
        board_str = state['board']
        if len(board_str) == 9:
            for i in range(3):
                for j in range(3):
                    game.board[i][j] = board_str[i*3 + j]
        
        return game


class GameManager:
    """
    Manages all active games for the local peer.
    """
    
    def __init__(self, local_user_id: str):
        """
        Initialize the game manager.
        
        Args:
            local_user_id: User ID of the local peer
        """
        self.local_user_id = local_user_id
        self.games: Dict[str, TicTacToe] = {}
        self.pending_invites: Dict[str, Dict] = {}  # game_id -> {from, timestamp}
        
        logger.info("Game manager initialized")
    
    def create_game(self, opponent_id: str) -> TicTacToe:
        """
        Create a new Tic-Tac-Toe game.
        
        Args:
            opponent_id: User ID of the opponent
            
        Returns:
            New TicTacToe instance
        """
        game = TicTacToe(initiator=self.local_user_id, opponent=opponent_id)
        self.games[game.game_id] = game
        logger.info(f"Created game {game.game_id} with {opponent_id}")
        return game
    
    def receive_invitation(self, game_id: str, from_user: str) -> bool:
        """
        Process a game invitation from another user.
        
        Args:
            game_id: Game ID from invitation
            from_user: User ID of the inviter
            
        Returns:
            Success status
        """
        # Don't accept duplicate invites
        if game_id in self.pending_invites or game_id in self.games:
            logger.warning(f"Duplicate game invitation: {game_id}")
            return False
            
        self.pending_invites[game_id] = {
            'from': from_user,
            'timestamp': int(time.time())
        }
        
        logger.info(f"Received game invitation {game_id} from {from_user}")
        return True
    
    def accept_invitation(self, game_id: str) -> Optional[TicTacToe]:
        """
        Accept a pending game invitation.
        
        Args:
            game_id: Game ID to accept
            
        Returns:
            The accepted game or None if not found
        """
        if game_id not in self.pending_invites:
            logger.warning(f"No pending invitation with ID {game_id}")
            return None
            
        invite = self.pending_invites.pop(game_id)
        from_user = invite['from']
        
        # Create game instance (as opponent)
        game = TicTacToe(
            game_id=game_id,
            initiator=from_user,
            opponent=self.local_user_id
        )
        
        # Accept the invitation
        game.accept_invitation()
        
        # Store the game
        self.games[game_id] = game
        
        logger.info(f"Accepted game invitation {game_id} from {from_user}")
        return game
    
    def reject_invitation(self, game_id: str) -> bool:
        """
        Reject a pending game invitation.
        
        Args:
            game_id: Game ID to reject
            
        Returns:
            Success status
        """
        if game_id not in self.pending_invites:
            logger.warning(f"No pending invitation with ID {game_id}")
            return False
            
        invite = self.pending_invites.pop(game_id)
        logger.info(f"Rejected game invitation {game_id} from {invite['from']}")
        return True
    
    def process_move(self, game_id: str, user_id: str, row: int, col: int) -> Tuple[bool, Optional[str]]:
        """
        Process a move in a game.
        
        Args:
            game_id: Game ID
            user_id: User ID making the move
            row: Row index (0-2)
            col: Column index (0-2)
            
        Returns:
            Tuple of (success, game_result)
        """
        if game_id not in self.games:
            logger.warning(f"Game {game_id} not found")
            return False, None
            
        game = self.games[game_id]
        return game.make_move(user_id, row, col)
    
    def get_game(self, game_id: str) -> Optional[TicTacToe]:
        """
        Get a game by ID.
        
        Args:
            game_id: Game ID to retrieve
            
        Returns:
            TicTacToe instance or None if not found
        """
        return self.games.get(game_id)
    
    def get_active_games(self) -> List[TicTacToe]:
        """
        Get all active games.
        
        Returns:
            List of active TicTacToe instances
        """
        return [game for game in self.games.values() 
                if game.status == TicTacToe.STATUS_ACTIVE]
    
    def get_pending_invites(self) -> List[Dict]:
        """
        Get all pending game invitations.
        
        Returns:
            List of invitation details
        """
        return [{'game_id': game_id, **details} 
                for game_id, details in self.pending_invites.items()]
    
    def cleanup_old_games(self, max_age_seconds: int = 86400) -> int:
        """
        Remove completed/cancelled games older than specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 24 hours)
            
        Returns:
            Number of games removed
        """
        current_time = int(time.time())
        games_to_remove = []
        
        for game_id, game in self.games.items():
            if (game.status in (TicTacToe.STATUS_COMPLETED, TicTacToe.STATUS_CANCELLED) and
                current_time - game.created_at > max_age_seconds):
                games_to_remove.append(game_id)
        
        # Remove old games
        for game_id in games_to_remove:
            del self.games[game_id]
            
        if games_to_remove:
            logger.info(f"Cleaned up {len(games_to_remove)} old games")
            
        return len(games_to_remove)
    
    def cleanup_old_invites(self, max_age_seconds: int = 3600) -> int:
        """
        Remove pending invitations older than specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)
            
        Returns:
            Number of invitations removed
        """
        current_time = int(time.time())
        invites_to_remove = []
        
        for game_id, invite in self.pending_invites.items():
            if current_time - invite['timestamp'] > max_age_seconds:
                invites_to_remove.append(game_id)
        
        # Remove old invites
        for game_id in invites_to_remove:
            del self.pending_invites[game_id]
            
        if invites_to_remove:
            logger.info(f"Cleaned up {len(invites_to_remove)} old invitations")
            
        return len(invites_to_remove)