#!/usr/bin/env python3
"""
User Interface Module
Handles user interaction and command processing
"""
import os
import base64
import mimetypes
import time
import time
import secrets

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
        print(f"Commands: POST, DM, DMLIST, PROFILE, LIST, FOLLOW, UNFOLLOW, FOLLOWING, FOLLOWERS, GAME, FILE, GROUPVIEW, FEED, LIKE, VERBOSE, QUIT")
        print(f"Verbose mode: {'ON' if self.message_handler.verbose_mode else 'OFF'}")
        
        self.running = True
        while self.running:
            try:
                original_cmd = input("\nCommand (POST/DM/DMLIST/PROFILE/LIST/FOLLOW/UNFOLLOW/FOLLOWING/FOLLOWERS/GAME/FILE/GROUPVIEW/FEED/LIKE/VERBOSE/QUIT): ").strip()
                cmd = original_cmd.upper()
                
                if cmd == "QUIT" or cmd == "Q":
                    print("Logging out and revoking all tokens...")
                    # Revoke all tokens before quitting
                    self.peer_manager.revoke_all_tokens()
                    
                    # Send token revocation messages to all peers
                    for user_id in self.peer_manager.get_peer_list():
                        peer_info = self.peer_manager.get_peer_info(user_id)
                        if peer_info:
                            # Create a message with the REVOKE type
                            message = {
                                'TYPE': 'REVOKE',
                                'USER_ID': self.peer_manager.user_id,
                                'TIMESTAMP': str(int(time.time())),
                                'MESSAGE_ID': secrets.token_hex(8)
                            }
                            self.message_handler.network_manager.send_to_address(message, peer_info['ip'], peer_info['port'])
                    
                    print("Goodbye!")
                    self.running = False
                elif cmd == "VERBOSE" or cmd == "V":
                    self._handle_verbose_command()
                elif cmd == "POST" or cmd == "P":
                    self._handle_post_command()
                elif cmd == "DM" or cmd == "D":
                    self._handle_dm_command()
                elif cmd == "DMLIST" or cmd == "DL":
                    self._handle_dmlist_command()
                elif cmd == "PROFILE" or cmd == "PROF":
                    self._handle_profile_command()
                elif cmd == "FEED" or cmd == "F":
                    self._handle_feed_command()
                elif cmd == "LIKE" or cmd == "L":
                    self._handle_like_command()
                elif cmd == "LIST" or cmd == "LS":
                    self._handle_list_command()
                elif cmd == "FOLLOW":
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
                elif cmd == "GROUPVIEW" or cmd == "GV":
                    self._handle_group_overview()
                elif cmd == "":
                    # Empty command, just continue
                    continue
                else:
                    print("Invalid command. Use POST, DM, DMLIST, PROFILE, LIST, FOLLOW, UNFOLLOW, FOLLOWING, FOLLOWERS, GAME, FILE, GROUPVIEW, FEED, LIKE, VERBOSE, or QUIT")
                    print("You can also use single letters: P, D, DL, PROF, LS, UF, G, GV, F, L, V, Q")
                    
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
            
        # Get TTL (Time To Live)
        ttl_input = input("Time To Live in seconds (default 3600 = 1 hour): ").strip()
        try:
            ttl = int(ttl_input) if ttl_input else 3600
            if ttl <= 0:
                print("TTL must be positive, using default 3600 seconds")
                ttl = 3600
        except ValueError:
            print("Invalid TTL value, using default 3600 seconds")
            ttl = 3600
        
        # Send the post with TTL
        sent_count = self.message_handler.send_post_message(message, ttl)
        
        if self.message_handler.verbose_mode:
            print(f"Message broadcasted to {sent_count} followers with TTL of {ttl} seconds")
    
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
    
    def _handle_dmlist_command(self):
        """Handle DMLIST command - show DMs from a specific peer"""
        peers = self.peer_manager.get_all_peers()
        if not peers:
            print("No peers available. Use LIST to discover peers first.")
            return
        
        # First, show peers with DM history
        peers_with_dms = [peer_id for peer_id in self.peer_manager.direct_messages.keys() 
                         if peer_id in peers or peer_id == self.peer_manager.user_id]
        
        if not peers_with_dms:
            print("You haven't exchanged DMs with any peers yet.")
            return
        
        print("\nPeers with DM history:")
        for idx, peer_id in enumerate(peers_with_dms, 1):
            display_name = self.peer_manager.get_display_name(peer_id)
            msg_count = len(self.peer_manager.direct_messages.get(peer_id, []))
            print(f"  {idx}. {peer_id} ({display_name}) - {msg_count} messages")
        
        selection = input("\nEnter peer number or user@ip to view DMs: ").strip()
        
        # Handle numeric selection
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(peers_with_dms):
                selected_peer = peers_with_dms[idx]
            else:
                print("Invalid selection")
                return
        except ValueError:
            # Handle direct peer_id input
            selected_peer = selection
        
        # Display the DMs for the selected peer
        success, message = self.message_handler.list_dms_from_peer(selected_peer)
        if not success:
            print(message)
    
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
            
        # Send message
        
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
    
    def _handle_group_list(self):
        """Handle listing all groups the user is a member of"""
        my_groups = self.peer_manager.get_my_groups()
        
        if not my_groups:
            print("You are not a member of any groups.")
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
            
        # Print groups for selection
        print("\nYour Groups:")
        for i, group_id in enumerate(my_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if not group:
                continue
            print(f"{i}. {group['name']} (ID: {group_id})")
            
        # Get group selection
        selection = input("\nEnter group number or ID: ").strip()
        
        # Handle numeric selection
        group_id = None
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(my_groups):
                group_id = my_groups[idx]
        except ValueError:
            # Try direct ID input
            group_id = selection
            
        if not group_id or group_id not in self.peer_manager.groups:
            print(f"Invalid group selection")
            return
            
        # Show group details
        self.message_handler.show_group_members(group_id)
    
    def _handle_group_view_messages(self):
        """Handle viewing messages in a specific group"""
        # Get group ID
        my_groups = self.peer_manager.get_my_groups()
        if not my_groups:
            print("You are not a member of any groups.")
            return
        
        if not os.path.isfile(file_path):
            print(f"Error: '{file_path}' is not a file")
            
        # Print groups for selection
        print("\nYour Groups:")
        for i, group_id in enumerate(my_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if not group:
                continue
            message_count = len(self.peer_manager.group_messages.get(group_id, []))
            print(f"{i}. {group['name']} (ID: {group_id}) - {message_count} messages")
            
        # Get group selection
        selection = input("\nEnter group number or ID: ").strip()
        
        # Handle numeric selection
        group_id = None
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(my_groups):
                group_id = my_groups[idx]
        except ValueError:
            # Try direct ID input
            group_id = selection
            
        if not group_id or group_id not in self.peer_manager.groups:
            print(f"Invalid group selection")
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
            
        # Get message limit
        limit_input = input("Number of messages to show (default 20): ").strip()
        try:
            limit = int(limit_input) if limit_input else 20
        except ValueError:
            limit = 20
            
        # Show group messages
        self.message_handler.show_group_messages(group_id, limit)
            
        # Print groups for selection
        print("\nYour Groups:")
        for i, group_id in enumerate(my_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if not group:
                continue
            message_count = len(self.peer_manager.group_messages.get(group_id, []))
            print(f"{i}. {group['name']} (ID: {group_id}) - {message_count} messages")
            
        # Get group selection
        selection = input("\nEnter group number or ID: ").strip()
        
        # Handle numeric selection
        group_id = None
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(my_groups):
                group_id = my_groups[idx]
        except ValueError:
            # Try direct ID input
            group_id = selection
            
        if not group_id or group_id not in self.peer_manager.groups:
            print(f"Invalid group selection")
            return
            
        # Get message limit
        limit_input = input("Number of messages to show (default 20): ").strip()
        try:
            limit = int(limit_input) if limit_input else 20
        except ValueError:
            limit = 20
            
        # Show group messages
        self.message_handler.show_group_messages(group_id, limit)
        
        # Format creation timestamp
        import datetime
        created_at = group['created_at']
        try:
            created_str = datetime.datetime.fromtimestamp(int(created_at)).strftime('%Y-%m-%d %H:%M:%S')
        except:
            created_str = str(created_at)
        
        print(f"Created on: {created_str}")
        print(f"Members ({len(group['members'])}):")
        
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
        # List all members
        for member_id in group['members']:
            display_name = self.peer_manager.get_display_name(member_id) or member_id
            you_marker = " (You)" if member_id == self.peer_manager.user_id else ""
            creator_marker = " (Creator)" if member_id == group['creator'] else ""
            print(f"  - {display_name} ({member_id}){you_marker}{creator_marker}")
            
    def _handle_group_leave(self):
        """Handle leaving a group"""
        # Get group ID
        group_id = input("Enter group ID to leave: ").strip()
        if not group_id:
            print("Group ID is required")
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
            
        # Leave the group
        success, message = self.peer_manager.leave_group(group_id)
        if success:
            print(f"You have left the group '{group['name']}'")
        else:
            print(f"Error: {message}")
            
    def _handle_group_overview(self):
        """Handle complete group overview"""
        # First, list all groups
        my_groups = self.peer_manager.get_my_groups()
        if not my_groups:
            print("You are not a member of any groups.")
            return
            
        print(f"\n===== GROUP OVERVIEW =====")
        print(f"You are a member of {len(my_groups)} groups:")
        
        # For each group, show basic info and recent messages
        for i, group_id in enumerate(my_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if not group:
                continue
                
            creator_status = " (Creator)" if group['creator'] == self.peer_manager.user_id else ""
            member_count = len(group['members'])
            message_count = len(self.peer_manager.group_messages.get(group_id, []))
            
            print(f"\n{i}. {group['name']} (ID: {group_id}){creator_status}")
            print(f"   Members: {member_count} | Messages: {message_count}")
            
            # Show members
            print(f"   Members:")
            for j, member_id in enumerate(list(group['members'])[:5], 1):
                display_name = self.peer_manager.get_display_name(member_id) or member_id
                you_marker = " (You)" if member_id == self.peer_manager.user_id else ""
                creator_marker = " (Creator)" if member_id == group['creator'] else ""
                print(f"     {j}. {display_name}{you_marker}{creator_marker}")
                
            # Show more members indicator if needed
            if len(group['members']) > 5:
                print(f"     ... and {len(group['members']) - 5} more members")
            
            # Show last 3 messages if any
            messages = self.peer_manager.get_group_messages(group_id)
            if messages:
                print(f"   Recent Messages:")
                # Get last 3 messages
                recent_msgs = sorted(messages, key=lambda x: x['timestamp'], reverse=True)[:3]
                for msg in reversed(recent_msgs):
                    from_user = msg['from_user']
                    display_name = self.peer_manager.get_display_name(from_user) or from_user
                    you_marker = " (You)" if from_user == self.peer_manager.user_id else ""
                    
                    # Format timestamp
                    import datetime
                    ts_str = datetime.datetime.fromtimestamp(msg['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Truncate content if too long
                    content = msg['content']
                    if len(content) > 50:
                        content = content[:47] + "..."
                        
                    print(f"     [{ts_str}] {display_name}{you_marker}: {content}")
                    
                if len(messages) > 3:
                    print(f"     ... and {len(messages) - 3} more messages")
            else:
                print(f"   No messages in this group yet")
                
        print(f"\n===== END OF GROUP OVERVIEW =====")
        
        # Ask if user wants to view details of a specific group
        choice = input("\nView details of a specific group? Enter group number or ID (or press Enter to skip): ").strip()
        if not choice:
            return
            
        # Handle numeric selection
        group_id = None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(my_groups):
                group_id = my_groups[idx]
        except ValueError:
            # Try direct ID input
            group_id = choice
            
        if not group_id or group_id not in self.peer_manager.groups:
            print(f"Invalid group selection")
            return
            
        # Show submenu for selected group
        self._handle_group_detail_submenu(group_id)
            
        # Leave group
        success, message = self.peer_manager.leave_group(group_id)
        print(message)
    
    def _handle_send_group_message(self):
        """Send a message to a group"""
        # List available groups
        my_groups = self.peer_manager.get_my_groups()
        if not my_groups:
            print("You are not a member of any groups.")
            return
            
        print("\nYour Groups:")
        for idx, group_id in enumerate(my_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if group:
                print(f"  {idx}. {group['name']} (ID: {group_id})")
        
        # Select group
        try:
            choice = int(input("\nSelect group number: ").strip())
            if choice < 1 or choice > len(my_groups):
                print("Invalid choice")
                return
                
            selected_group_id = my_groups[choice - 1]
            group = self.peer_manager.get_group(selected_group_id)
            
            # Get message content
            content = input(f"Message to {group['name']}: ").strip()
            if not content:
                print("Message cannot be empty")
                return
                
            # Send the message
            sent_count = self.message_handler.send_group_message(selected_group_id, content)
            
            # Also display the message locally
            display_name = self.peer_manager.get_display_name(self.peer_manager.user_id)
            avatar_info = self.peer_manager.get_avatar_info(self.peer_manager.user_id)
            print(f"\n[{group['name']}] {display_name}{avatar_info}: {content}")
            
            # Show result
            print(f"Message sent to {sent_count} group members")
            
        except ValueError:
            print("Please enter a valid number")
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
            print(f"Error: {e}")




    def _handle_group_command(self):
        """Handle GROUP command with submenu"""
        print("\nGroup Chat Operations:")
        print("  1. CREATE - Create a new group")
        print("  2. UPDATE - Add/remove members from a group")
        print("  3. MESSAGE - Send a message to a group")
        print("  4. LIST - List all your groups")
        print("  5. INFO - Show details about a specific group")
        print("  6. MESSAGES - View messages in a specific group")
        print("  7. LEAVE - Leave a group")
        print("  8. OVERVIEW - Complete group overview")
        print("  0. Back to main menu")
        
        try:
            choice = input("\nSelect option (0-8): ").strip()
            
            if choice == "1":
                self._handle_group_create()
            elif choice == "2":
                self._handle_group_update()
            elif choice == "3":
                self._handle_group_message()
            elif choice == "4":
                self._handle_group_list()
            elif choice == "5":
                self._handle_group_info()
            elif choice == "6":
                self._handle_group_view_messages()
            elif choice == "7":
                self._handle_group_leave()
            elif choice == "8":
                self._handle_group_overview()
            elif choice == "0":
                return
            else:
                print("Invalid choice")
        except Exception as e:
            print(f"Error: {e}")

