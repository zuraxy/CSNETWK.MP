#!/usr/bin/env python3
"""
User Interface Module
Handles user interaction and command processing
"""
import os
import base64
import mimetypes
import time

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
        print(f"Commands: POST, DM, PROFILE, LIST, FOLLOW, UNFOLLOW, FOLLOWING, FOLLOWERS, GAME, FILE, VERBOSE, QUIT")
        print(f"Verbose mode: {'ON' if self.message_handler.verbose_mode else 'OFF'}")
        
        self.running = True
        while self.running:
            try:
                original_cmd = input("\nCommand (POST/DM/PROFILE/LIST/FOLLOW/UNFOLLOW/FOLLOWING/FOLLOWERS/GAME/FILE/VERBOSE/QUIT): ").strip()
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
                elif cmd.startswith("FILE") or cmd == "FILE":
                    self._handle_file_command(original_cmd)
                elif cmd == "":
                    # Empty command, just continue
                    continue
                else:
                    print("Invalid command. Use POST, DM, PROFILE, LIST, FOLLOW, UNFOLLOW, FOLLOWING, FOLLOWERS, GAME, FILE, VERBOSE, or QUIT")
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
        
        # Filter out expired peers
        active_peers = {}
        for user_id, info in peers.items():
            # Get timestamp from peer info or use current time as fallback
            timestamp = info.get('timestamp', str(int(time.time())))
            # Use default TTL if not specified
            ttl = info.get('ttl', str(DEFAULT_PROFILE_TTL))
            
            # Only include peer if TTL is still valid
            if self.message_handler._is_message_valid(timestamp, ttl):
                active_peers[user_id] = info
        
        if self.message_handler.verbose_mode:
            peer_list = [f"{user_id} ({info['ip']}:{info['port']})" for user_id, info in active_peers.items()]
            print(f"\n[KNOWN PEERS] ({len(active_peers)} active of {len(peers)} total peers):")
            for peer_info in peer_list:
                print(f"  - {peer_info}")
        else:
            print(f"\nOnline ({len(active_peers)} active):")
            for user_id in active_peers.keys():
                display_name = self.peer_manager.get_display_name(user_id)
                avatar_info = self.peer_manager.get_avatar_info(user_id)
                following_status = " [Following]" if self.peer_manager.is_following(user_id) else ""
                follower_status = " [Follower]" if self.peer_manager.is_follower(user_id) else ""
                print(f"  - {display_name} ({user_id}){avatar_info}{following_status}{follower_status}")
        
        # Show expired peers count if any exist
        expired_count = len(peers) - len(active_peers)
        if expired_count > 0:
            print(f"\n{expired_count} expired peer profiles not shown")
    
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
            print("  GAME <user@ip> O         - Invite user to play (you are O)")
            print("  GAME <user@ip> X <pos>   - Invite and make first move")
            print("  GAME <game_id> <pos>     - Make a move (position 0-8)")
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
                    if position < 0 or position > 8:
                        print("Error: Position must be between 0 and 8")
                        return
                except ValueError:
                    print("Error: Position must be a number between 0 and 8")
                    return
                
                return self._make_game_move(game_id, position)
        
        elif len(cmd_parts) == 4:
            if '@' in cmd_parts[1] and cmd_parts[2].upper() == 'X':
                # Invite and make first move: GAME user@ip X <position>
                target_user = cmd_parts[1]
                try:
                    position = int(cmd_parts[3])
                    if position < 0 or position > 8:
                        print("Error: Position must be between 0 and 8")
                        return
                except ValueError:
                    print("Error: Position must be a number between 0 and 8")
                    return
                
                return self._send_game_invitation(target_user, 'X', position)
        
        # Invalid command format
        print("Invalid GAME command format.")
        print("Usage:")
        print("  GAME                      - Show help and active games")
        print("  GAME <user@ip> O          - Invite user (you are O)")
        print("  GAME <user@ip> X <pos>    - Invite and make first move")
        print("  GAME <game_id> <pos>      - Make a move (position 0-8)")
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

    def _handle_file_command(self, original_cmd):
        """Handle FILE command and its subcommands"""
        # Parse the command
        parts = original_cmd.split()
        
        if len(parts) == 1:  # Just "FILE"
            print("FILE command usage:")
            print("  FILE SEND <user@ip> <file_path> [description]  - Send a file to a peer")
            print("  FILE ACCEPT <transfer_id>                      - Accept an incoming file offer")
            print("  FILE REJECT <transfer_id>                      - Reject an incoming file offer")
            print("  FILE LIST                                      - List pending file offers")
            print("  FILE STATUS                                    - Show active file transfers")
            return
        
        subcommand = parts[1].upper()
        
        if subcommand == "SEND":
            self._handle_file_send_command(parts)
        elif subcommand == "ACCEPT":
            self._handle_file_accept_command(parts)
        elif subcommand == "REJECT":
            self._handle_file_reject_command(parts)
        elif subcommand == "LIST":
            self._handle_file_list_command()
        elif subcommand == "STATUS":
            self._handle_file_status_command()
        else:
            print("Invalid FILE subcommand. Use SEND, ACCEPT, REJECT, LIST, or STATUS")
    
    def _handle_file_send_command(self, parts):
        """Handle FILE SEND command"""
        if len(parts) < 4:
            print("Usage: FILE SEND <user@ip> <file_path> [description]")
            return
        
        target = parts[2]
        file_path = parts[3]
        description = " ".join(parts[4:]) if len(parts) > 4 else "No description"
        
        # Convert relative path to absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        print(f"Debug: Original file path: {parts[3]}")
        print(f"Debug: Resolved file path: {file_path}")
        print(f"Debug: Current working directory: {os.getcwd()}")
        print(f"Debug: File exists check: {os.path.exists(file_path)}")
        
        # Validate file path
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found")
            print(f"Tried looking in: {os.getcwd()}")
            return
        
        if not os.path.isfile(file_path):
            print(f"Error: '{file_path}' is not a file")
            return
        
        # Get file info
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        file_type, _ = mimetypes.guess_type(file_path)
        if not file_type:
            file_type = "application/octet-stream"
        
        print(f"Debug: File path: {file_path}")
        print(f"Debug: File size: {file_size} bytes")
        print(f"Debug: Filename: {filename}")
        print(f"Debug: File type: {file_type}")
        
        # Double-check by reading the file content
        try:
            with open(file_path, 'rb') as f:
                test_content = f.read()
            print(f"Debug: Actual file content length: {len(test_content)} bytes")
            print(f"Debug: File content preview: {test_content[:100]}")
        except Exception as e:
            print(f"Debug: Error reading file for test: {e}")
        
        # Check file size limit (50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            print(f"Error: File too large ({self._format_file_size(file_size)}). Maximum size is 50MB")
            return
        
        # Parse target
        try:
            target_peer = self.peer_manager.find_peer_by_handle(target)
            if target_peer:
                self._send_file_offer(target_peer, file_path, filename, file_size, file_type, description)
            else:
                print(f"Error: Peer '{target}' not found or not online")
        except Exception as e:
            print(f"Error sending file: {e}")
    
    def _handle_file_accept_command(self, parts):
        """Handle FILE ACCEPT command"""
        if len(parts) != 3:
            print("Usage: FILE ACCEPT <transfer_id>")
            return
        
        transfer_id = parts[2]
        
        if transfer_id not in self.message_handler.pending_file_offers:
            print(f"Error: No pending file offer with ID '{transfer_id}'")
            return
        
        offer_info = self.message_handler.pending_file_offers[transfer_id]
        print(f"Accepting file '{offer_info['filename']}' from {offer_info['sender_name']}")
        
        # Note: receiving_files structure will be initialized when first chunk arrives
        # Don't pre-initialize it here to avoid total_chunks=0 issue
        
        # Send acceptance message back to sender
        try:
            msg_dict = {
                'TYPE': 'FILE_ACCEPT',
                'transfer_id': transfer_id,
                'receiver_name': self.message_handler.peer_manager.get_self_info().get('name', 'Unknown')
            }
            
            print(f"Debug: Sending FILE_ACCEPT to {offer_info['sender_addr']}")
            print(f"Debug: Message: {msg_dict}")
            
            self.message_handler.network_manager.send_to_address(msg_dict, offer_info['sender_addr'][0], offer_info['sender_addr'][1])
            print(f"File acceptance sent. Waiting for file chunks...")
        except Exception as e:
            print(f"Error sending acceptance: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_file_reject_command(self, parts):
        """Handle FILE REJECT command"""
        if len(parts) != 3:
            print("Usage: FILE REJECT <transfer_id>")
            return
        
        transfer_id = parts[2]
        
        if transfer_id not in self.message_handler.pending_file_offers:
            print(f"Error: No pending file offer with ID '{transfer_id}'")
            return
        
        offer_info = self.message_handler.pending_file_offers[transfer_id]
        print(f"Rejecting file '{offer_info['filename']}' from {offer_info['sender_name']}")
        
        # Send rejection message back to sender
        try:
            msg_dict = {
                'TYPE': 'FILE_REJECT',
                'transfer_id': transfer_id,
                'receiver_name': self.message_handler.peer_manager.get_self_info().get('name', 'Unknown')
            }
            self.message_handler.network_manager.send_to_address(msg_dict, offer_info['sender_addr'][0], offer_info['sender_addr'][1])
            
            # Remove from pending offers
            del self.message_handler.pending_file_offers[transfer_id]
            print("File rejection sent.")
        except Exception as e:
            print(f"Error sending rejection: {e}")
    
    def _handle_file_list_command(self):
        """Handle FILE LIST command"""
        pending = self.message_handler.pending_file_offers
        
        if not pending:
            print("No pending file offers")
            return
        
        print(f"\nPending File Offers ({len(pending)}):")
        print("-" * 80)
        for transfer_id, offer in pending.items():
            print(f"ID: {transfer_id}")
            print(f"  From: {offer['sender_name']}")
            print(f"  File: {offer['filename']}")
            print(f"  Size: {self._format_file_size(offer['file_size'])}")
            print(f"  Type: {offer['file_type']}")
            print(f"  Description: {offer['description']}")
            print(f"  Time: {self._format_timestamp(offer['timestamp'])}")
            print()
    
    def _handle_file_status_command(self):
        """Handle FILE STATUS command"""
        active_transfers = self.message_handler.active_file_transfers
        receiving = self.message_handler.receiving_files
        
        if not active_transfers and not receiving:
            print("No active file transfers")
            return
        
        if active_transfers:
            print(f"\nOutgoing Transfers ({len(active_transfers)}):")
            print("-" * 50)
            for transfer_id, transfer in active_transfers.items():
                print(f"ID: {transfer_id}")
                print(f"  File: {transfer['filename']}")
                print(f"  To: {transfer.get('receiver_name', 'Unknown')}")
                print(f"  Status: {transfer.get('status', 'In progress')}")
                print()
        
        if receiving:
            print(f"\nIncoming Transfers ({len(receiving)}):")
            print("-" * 50)
            for transfer_id, transfer in receiving.items():
                total = transfer['total_chunks']
                received = transfer['received_count']
                progress = (received / total * 100) if total > 0 else 0
                print(f"ID: {transfer_id}")
                print(f"  Progress: {received}/{total} chunks ({progress:.1f}%)")
                print()
    
    def _send_file_offer(self, target_peer, file_path, filename, file_size, file_type, description):
        """Send a file offer to a peer"""
        try:
            # Generate transfer ID
            transfer_id = f"file_{self.message_handler.file_transfer_counter}_{int(time.time())}"
            self.message_handler.file_transfer_counter += 1
            
            print(f"Debug: Generated transfer ID: {transfer_id}")
            print(f"Debug: Active transfers before: {list(self.message_handler.active_file_transfers.keys())}")
            
            # Store transfer info
            self.message_handler.active_file_transfers[transfer_id] = {
                'filename': filename,
                'file_path': file_path,
                'file_size': file_size,
                'file_type': file_type,
                'description': description,
                'target_peer': target_peer,
                'status': 'offering'
            }
            
            print(f"Debug: Active transfers after: {list(self.message_handler.active_file_transfers.keys())}")
            
            # Send offer message
            msg_dict = {
                'TYPE': 'FILE_OFFER',
                'transfer_id': transfer_id,
                'filename': filename,
                'file_size': str(file_size),
                'file_type': file_type,
                'description': description,
                'sender_name': self.message_handler.peer_manager.get_self_info().get('name', 'Unknown')
            }
            
            self.message_handler.network_manager.send_to_address(msg_dict, target_peer['addr'][0], target_peer['addr'][1])
            print(f"📤 File offer sent to {target_peer.get('name', 'Unknown')} ({target_peer['addr'][0]})")
            print(f"File: {filename} ({self._format_file_size(file_size)})")
            print(f"Transfer ID: {transfer_id}")
            print("Waiting for response...")
            
        except Exception as e:
            print(f"Error sending file offer: {e}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def _format_timestamp(self, timestamp):
        """Format timestamp for display"""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def display_message_with_ttl(self, msg_dict):
        """Display a message with TTL information"""
        import datetime
        import time
        
        message_type = msg_dict.get('TYPE', 'Unknown')
        user_id = msg_dict.get('USER_ID', msg_dict.get('FROM', 'Unknown'))
        content = msg_dict.get('CONTENT', '')
        timestamp = msg_dict.get('TIMESTAMP', '')
        ttl = msg_dict.get('TTL', '')
        message_id = msg_dict.get('MESSAGE_ID', '')
        
        # Skip expired messages
        if not self.message_handler._is_message_valid(timestamp, ttl):
            return False
        
        if timestamp and ttl:
            try:
                # Calculate expiry time
                creation_time = int(timestamp)
                ttl_seconds = int(ttl)
                expiry_time = creation_time + ttl_seconds
                current_time = int(time.time())
                
                # Format times
                created_str = datetime.datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
                expires_str = datetime.datetime.fromtimestamp(expiry_time).strftime('%Y-%m-%d %H:%M:%S')
                
                # Calculate time remaining
                remaining = expiry_time - current_time
                if remaining > 0:
                    if remaining < 60:
                        remaining_str = f"{remaining}s"
                    elif remaining < 3600:
                        remaining_str = f"{remaining // 60}m"
                    elif remaining < 86400:
                        remaining_str = f"{remaining // 3600}h"
                    else:
                        remaining_str = f"{remaining // 86400}d"
                    
                    # Display message based on type
                    if message_type == 'POST':
                        display_name = self.peer_manager.get_display_name(user_id)
                        avatar_info = self.peer_manager.get_avatar_info(user_id)
                        print(f"\n{display_name}{avatar_info} ({message_id}): {content}")
                        print(f"  ⏱️ Expires in: {remaining_str}")
                    elif message_type == 'DM':
                        from_user = user_id
                        display_name = self.peer_manager.get_display_name(from_user)
                        avatar_info = self.peer_manager.get_avatar_info(from_user)
                        print(f"\n[MSG] {display_name}{avatar_info} ({message_id}): {content}")
                        print(f"  ⏱️ Expires in: {remaining_str}")
                    else:
                        print(f"[{message_type}] {user_id}: {content}")
                        print(f"  ⏱️ Expires in: {remaining_str}")
                    
                    return True
                else:
                    # This shouldn't happen since we check validity above, but just in case
                    return False
                    
            except (ValueError, TypeError) as e:
                print(f"[{message_type}] {user_id}: {content}")
                if self.message_handler.verbose_mode:
                    print(f"  ⚠️ Invalid TTL format: {e}")
                return True
        else:
            print(f"[{message_type}] {user_id}: {content}")
            if self.message_handler.verbose_mode:
                print(f"  ⚠️ Missing TTL information")
            return True
