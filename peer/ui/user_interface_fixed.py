#!/usr/bin/env python3
"""
User Interface Module
Handles user interaction and command processing
"""
import os
import base64
import mimetypes

# Add at top of file
from peer.config.settings import DEFAULT_VERBOSE_MODE

class UserInterface:
    """Handles user interaction and command processing"""
    
    def __init__(self, message_handler, peer_manager):
        self.message_handler = message_handler
        self.peer_manager = peer_manager
        self.running = False
        
        # Set default verbose mode from settings
        self.message_handler.set_verbose_mode(DEFAULT_VERBOSE_MODE)
    
    def start_command_loop(self):
        """Start the main command processing loop"""
        print(f"\nPeer-to-Peer Chat Ready!")
        print(f"Commands: POST, DM, PROFILE, LIST, FOLLOW, UNFOLLOW, FOLLOWING, FOLLOWERS, GAME, VERBOSE, QUIT")
        print(f"Verbose mode: {'ON' if self.message_handler.verbose_mode else 'OFF'}")
        
        self.running = True
        while self.running:
            try:
                original_cmd = input("\nCommand (POST/DM/PROFILE/LIST/FOLLOW/UNFOLLOW/FOLLOWING/FOLLOWERS/GAME/VERBOSE/QUIT): ").strip()
                cmd = original_cmd.upper()
                
                if cmd == "QUIT" or cmd == "Q":
                    print("Goodbye!")
                    self.running = False
                elif cmd == "VERBOSE" or cmd == "V":
                    self._handle_verbose_command()
                elif cmd == "POST" or cmd == "P":
                    self._handle_post_command()
                elif cmd == "DM" or cmd == "D":
                    self._handle_dm_command()
                elif cmd == "PROFILE" or cmd == "PROF":
                    self._handle_profile_command()
                elif cmd == "LIST" or cmd == "L":
                    self._handle_list_command()
                elif cmd == "FOLLOW" or cmd == "F":
                    self._handle_follow_command()
                elif cmd == "UNFOLLOW" or cmd == "UF":
                    self._handle_unfollow_command()
                elif cmd == "FOLLOWING":
                    self._handle_following_command()
                elif cmd == "FOLLOWERS":
                    self._handle_followers_command()
                elif cmd.startswith("GAME") or cmd == "G":
                    self._handle_game_command(original_cmd)
                elif cmd == "":
                    # Empty command, just continue
                    continue
                else:
                    print("Invalid command. Use POST, DM, PROFILE, LIST, FOLLOW, UNFOLLOW, FOLLOWING, FOLLOWERS, GAME, VERBOSE, or QUIT")
                    print("You can also use single letters: P, D, L, F, UF, G, V, Q")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                self.running = False
            except EOFError:
                print("\nGoodbye!")
                self.running = False
            except Exception as e:
                print(f"Command error: {e}")
                print("Please try again...")
    
    def stop(self):
        """Stop the command loop"""
        self.running = False
    
    def _handle_verbose_command(self):
        """Toggle verbose mode"""
        current_verbose = self.message_handler.verbose_mode
        self.message_handler.set_verbose_mode(not current_verbose)
        print(f"Verbose mode: {'ON' if self.message_handler.verbose_mode else 'OFF'}")
    
    def _handle_post_command(self):
        """Handle POST (broadcast message) command"""
        # Get follower count
        follower_count = len(self.peer_manager.get_followers())
        if follower_count == 0:
            print("You have no followers. Your message won't be received by anyone.")
            if not input("Continue anyway? (y/n): ").strip().lower().startswith('y'):
                return
        else:
            print(f"Your message will be sent to {follower_count} follower(s).")
        
        message = input("Message: ").strip()
        if not message:
            print("No message provided")
            return
        
        sent_count = self.message_handler.send_post_message(message)
        
        if self.message_handler.verbose_mode:
            print(f"Message broadcasted to {sent_count} followers")
    
    def _handle_dm_command(self):
        """Handle DM (direct message) command"""
        peers = self.peer_manager.get_all_peers()
        if not peers:
            print("No peers available. Use LIST to discover peers first.")
            return
        
        print("Available peers:")
        for user_id in peers.keys():
            display_name = self.peer_manager.get_display_name(user_id)
            print(f"  - {user_id} ({display_name})")
        
        recipient = input("Recipient (user@ip): ").strip()
        if not recipient:
            print("No recipient specified")
            return
        
        message = input("Message: ").strip()
        if not message:
            print("No message provided")
            return
        
        if self.message_handler.send_dm_message(recipient, message):
            if self.message_handler.verbose_mode:
                print(f"DM sent to {recipient}")
        else:
            print(f"Error: Peer {recipient} not found or unreachable")
    
    def _handle_profile_command(self):
        """Handle PROFILE command"""
        display_name = input("Display Name: ").strip()
        if not display_name:
            # Use username from user_id if available
            if '@' in self.peer_manager.user_id:
                display_name = self.peer_manager.user_id.split('@')[0]
            else:
                display_name = self.peer_manager.user_id
        
        status = input("Status message: ").strip()
        if not status:
            status = "Hello from P2P LSNP!"
        
        add_avatar = input("Add profile picture? (y/n): ").strip().lower() == 'y'
        
        avatar_data = None
        avatar_type = None
        
        if add_avatar:
            avatar_path = input("Enter path to image file (or press Enter to skip): ").strip()
            if avatar_path and os.path.exists(avatar_path):
                try:
                    file_size = os.path.getsize(avatar_path)
                    if file_size > 20480:  # 20KB
                        print(f"Warning: File is {file_size} bytes. Large files may cause issues.")
                        if input("Continue anyway? (y/n): ").strip().lower() != 'y':
                            avatar_path = None
                    
                    if avatar_path:
                        # Read and encode avatar
                        with open(avatar_path, 'rb') as f:
                            avatar_bytes = f.read()
                        
                        avatar_data = base64.b64encode(avatar_bytes).decode('utf-8')
                        avatar_type = mimetypes.guess_type(avatar_path)[0] or 'application/octet-stream'
                        
                        print(f"Avatar added: {avatar_type}, {len(avatar_data)} characters")
                        
                except Exception as e:
                    print(f"Error reading avatar file: {e}")
            elif avatar_path:
                print(f"File not found: {avatar_path}")
        
        sent_count = self.message_handler.send_profile_message(display_name, status, avatar_data, avatar_type)
        print(f"Profile updated and broadcasted to {sent_count} peers")
    
    def _handle_list_command(self):
        """Handle LIST command to show known peers"""
        peers = self.peer_manager.get_all_peers()
        if not peers:
            print("No peers discovered yet. Wait a moment for peer discovery.")
            return
        
        if self.message_handler.verbose_mode:
            peer_list = [f"{user_id} ({info['ip']}:{info['port']})" for user_id, info in peers.items()]
            print(f"\n[KNOWN PEERS] ({len(peers)} peers):")
            for peer_info in peer_list:
                print(f"  - {peer_info}")
        else:
            print(f"\nOnline ({len(peers)}):")
            for user_id in peers.keys():
                display_name = self.peer_manager.get_display_name(user_id)
                avatar_info = self.peer_manager.get_avatar_info(user_id)
                following_status = " [Following]" if self.peer_manager.is_following(user_id) else ""
                follower_status = " [Follower]" if self.peer_manager.is_follower(user_id) else ""
                print(f"  - {display_name} ({user_id}){avatar_info}{following_status}{follower_status}")
    
    def _handle_follow_command(self):
        """Handle FOLLOW command to follow a peer"""
        peers = self.peer_manager.get_all_peers()
        if not peers:
            print("No peers available. Use LIST to discover peers first.")
            return
        
        print("Available peers:")
        for user_id in peers.keys():
            display_name = self.peer_manager.get_display_name(user_id)
            following = " [Following]" if self.peer_manager.is_following(user_id) else ""
            print(f"  - {user_id} ({display_name}){following}")
        
        user_to_follow = input("User to follow (user@ip): ").strip()
        if not user_to_follow:
            print("No user specified")
            return
        
        # Check if already following
        if self.peer_manager.is_following(user_to_follow):
            print(f"You are already following {user_to_follow}")
            return
        
        # Send follow request
        if self.message_handler.send_follow_request(user_to_follow):
            print(f"Follow request sent to {user_to_follow}")
        else:
            print(f"Error: Could not send follow request to {user_to_follow}")
    
    def _handle_unfollow_command(self):
        """Handle UNFOLLOW command to unfollow a peer"""
        following = self.peer_manager.get_following()
        if not following:
            print("You are not following anyone.")
            return
        
        print("Users you are following:")
        for user_id in following:
            display_name = self.peer_manager.get_display_name(user_id)
            print(f"  - {user_id} ({display_name})")
        
        user_to_unfollow = input("User to unfollow (user@ip): ").strip()
        if not user_to_unfollow:
            print("No user specified")
            return
        
        # Check if actually following
        if not self.peer_manager.is_following(user_to_unfollow):
            print(f"You are not following {user_to_unfollow}")
            return
        
        # Send unfollow request
        if self.message_handler.send_unfollow_request(user_to_unfollow):
            print(f"Unfollow request sent to {user_to_unfollow}")
        else:
            print(f"Error: Could not send unfollow request to {user_to_unfollow}")
    
    def _handle_following_command(self):
        """Handle FOLLOWING command to list users you follow"""
        following = self.peer_manager.get_following()
        if not following:
            print("You are not following anyone.")
            return
        
        print(f"\nUsers you are following ({len(following)}):")
        for user_id in following:
            display_name = self.peer_manager.get_display_name(user_id)
            avatar_info = self.peer_manager.get_avatar_info(user_id)
            follower_status = " [Follower]" if self.peer_manager.is_follower(user_id) else ""
            print(f"  - {display_name} ({user_id}){avatar_info}{follower_status}")
    
    def _handle_followers_command(self):
        """Handle FOLLOWERS command to list users following you"""
        followers = self.peer_manager.get_followers()
        if not followers:
            print("You have no followers.")
            return
        
        print(f"\nUsers following you ({len(followers)}):")
        for user_id in followers:
            display_name = self.peer_manager.get_display_name(user_id)
            avatar_info = self.peer_manager.get_avatar_info(user_id)
            following_status = " [Following]" if self.peer_manager.is_following(user_id) else ""
            print(f"  - {display_name} ({user_id}){avatar_info}{following_status}")

    def _handle_game_command(self, full_cmd):
        """Handle GAME command for Tic-Tac-Toe"""
        cmd_parts = full_cmd.split()
        
        if len(cmd_parts) == 1:  # Just "GAME" command
            # Show game help and active games
            print("\n🎮 Tic-Tac-Toe Game Commands:")
            print("  GAME <user@ip>           - Invite user to play (you are X)")
            print("  GAME <user@ip> O         - Invite user to play (you are O)")
            print("  GAME <user@ip> X <pos>   - Invite and make first move")
            print("  GAME <game_id> <pos>     - Make a move (position 1-9)")
            print("  GAME LIST                - Show active games")
            
            active_games = self.message_handler.get_active_games()
            if active_games:
                print(f"\nActive games ({len(active_games)}):")
                for game_id in active_games:
                    game_info = self.message_handler.get_game_info(game_id)
                    if game_info:
                        player_x_name = self.peer_manager.get_display_name(game_info['player_x'])
                        player_o_name = self.peer_manager.get_display_name(game_info['player_o'])
                        current_turn = game_info['current_turn']
                        status = game_info['status']
                        print(f"  - {game_id}: {player_x_name} (X) vs {player_o_name} (O)")
                        print(f"    Turn: {current_turn}, Status: {status}")
            else:
                print("\nNo active games.")
            return
        
        elif len(cmd_parts) == 2:
            if cmd_parts[1].upper() == "LIST":
                # List active games
                active_games = self.message_handler.get_active_games()
                if active_games:
                    print(f"\nActive games ({len(active_games)}):")
                    for game_id in active_games:
                        game_info = self.message_handler.get_game_info(game_id)
                        if game_info:
                            player_x_name = self.peer_manager.get_display_name(game_info['player_x'])
                            player_o_name = self.peer_manager.get_display_name(game_info['player_o'])
                            current_turn = game_info['current_turn']
                            status = game_info['status']
                            print(f"  - {game_id}: {player_x_name} (X) vs {player_o_name} (O)")
                            print(f"    Turn: {current_turn}, Status: {status}")
                            if status == 'active':
                                self.message_handler._display_board(game_info['board'])
                else:
                    print("\nNo active games.")
                return
            
            elif '@' in cmd_parts[1]:
                # Invite user to game (default: inviter is X)
                target_user = cmd_parts[1]
                return self._send_game_invitation(target_user, 'X')
        
        elif len(cmd_parts) == 3:
            if '@' in cmd_parts[1] and cmd_parts[2].upper() in ['X', 'O']:
                # Invite user with symbol choice: GAME user@ip X/O
                target_user = cmd_parts[1]
                chosen_symbol = cmd_parts[2].upper()
                return self._send_game_invitation(target_user, chosen_symbol)
            
            else:
                # Make a move: GAME <game_id> <position>
                game_id = cmd_parts[1]
                try:
                    position = int(cmd_parts[2])
                    if position < 1 or position > 9:
                        print("Error: Position must be between 1 and 9")
                        return
                except ValueError:
                    print("Error: Position must be a number between 1 and 9")
                    return
                
                return self._make_game_move(game_id, position)
        
        elif len(cmd_parts) == 4:
            if '@' in cmd_parts[1] and cmd_parts[2].upper() == 'X':
                # Invite and make first move: GAME user@ip X <position>
                target_user = cmd_parts[1]
                try:
                    position = int(cmd_parts[3])
                    if position < 1 or position > 9:
                        print("Error: Position must be between 1 and 9")
                        return
                except ValueError:
                    print("Error: Position must be a number between 1 and 9")
                    return
                
                return self._send_game_invitation(target_user, 'X', position)
        
        # Invalid command format
        print("Invalid GAME command format.")
        print("Usage:")
        print("  GAME                      - Show help and active games")
        print("  GAME <user@ip>            - Invite user (you are X)")
        print("  GAME <user@ip> O          - Invite user (you are O)")
        print("  GAME <user@ip> X <pos>    - Invite and make first move")
        print("  GAME <game_id> <pos>      - Make a move (position 1-9)")
        print("  GAME LIST                 - Show active games")
    
    def _send_game_invitation(self, target_user, chosen_symbol='X', first_move_position=None):
        """Send a game invitation"""
        peers = self.peer_manager.get_all_peers()
        
        if not peers:
            print("No peers available. Use LIST to discover peers first.")
            return
        
        if target_user not in peers:
            print(f"Error: Peer {target_user} not found or unreachable")
            print("Available peers:")
            for user_id in peers.keys():
                display_name = self.peer_manager.get_display_name(user_id)
                print(f"  - {user_id} ({display_name})")
            return
        
        success = self.message_handler.send_tictactoe_invite(target_user, chosen_symbol, first_move_position)
        if success:
            display_name = self.peer_manager.get_display_name(target_user)
            print(f"🎮 Tic-Tac-Toe invitation sent to {display_name}!")
            print(f"You are '{chosen_symbol}', they are '{'O' if chosen_symbol == 'X' else 'X'}'")
            
            if first_move_position:
                print(f"You made the first move at position {first_move_position}")
            elif chosen_symbol == 'X':
                print("You play first as X.")
            else:
                print("They will play first as X.")
        else:
            print(f"Error: Could not send game invitation to {target_user}")
    
    def _make_game_move(self, game_id, position):
        """Make a move in an active game"""
        # Check if game exists
        game_info = self.message_handler.get_game_info(game_id)
        if not game_info:
            print(f"Error: Game {game_id} not found")
            print("Use 'GAME LIST' to see active games")
            return
        
        # Check if it's our turn
        current_player = self.peer_manager.user_id
        if current_player == game_info['player_x']:
            our_symbol = 'X'
        else:
            our_symbol = 'O'
        
        if game_info['current_turn'] != our_symbol:
            opponent_symbol = 'O' if our_symbol == 'X' else 'X'
            if game_info['player_x'] == current_player:
                opponent_name = self.peer_manager.get_display_name(game_info['player_o'])
            else:
                opponent_name = self.peer_manager.get_display_name(game_info['player_x'])
            print(f"Error: It's not your turn! Waiting for {opponent_name} ({opponent_symbol}) to play.")
            return
        
        # Check if position is available
        if not self.message_handler._is_valid_move(game_info['board'], position):
            print(f"Error: Position {position} is already taken")
            self.message_handler._display_board(game_info['board'])
            return
        
        # Make the move
        if self.message_handler.send_tictactoe_move(game_id, position):
            print(f"🎮 You played {our_symbol} at position {position}")
            # Display updated board
            game_info = self.message_handler.get_game_info(game_id)
            if game_info:
                self.message_handler._display_board(game_info['board'])
                
                # Check if game ended
                result = self.message_handler._check_game_result(game_info['board'])
                if result['finished']:
                    if result['winner']:
                        if result['winner'] == our_symbol:
                            print(f"🏆 Congratulations! You win!")
                        else:
                            if game_info['player_x'] == current_player:
                                opponent_name = self.peer_manager.get_display_name(game_info['player_o'])
                            else:
                                opponent_name = self.peer_manager.get_display_name(game_info['player_x'])
                            print(f"💔 {opponent_name} wins!")
                    else:
                        print("🤝 It's a draw!")
                else:
                    # Game continues
                    opponent_symbol = 'O' if our_symbol == 'X' else 'X'
                    if game_info['player_x'] == current_player:
                        opponent_name = self.peer_manager.get_display_name(game_info['player_o'])
                    else:
                        opponent_name = self.peer_manager.get_display_name(game_info['player_x'])
                    print(f"Waiting for {opponent_name} ({opponent_symbol}) to play...")
        else:
            print("Error: Could not send move")
