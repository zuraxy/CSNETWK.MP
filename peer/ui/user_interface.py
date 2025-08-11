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
        print(f"Commands: POST, DM, DMLIST, PROFILE, LIST, FOLLOW, UNFOLLOW, FOLLOWING, FOLLOWERS, GROUP, GROUPVIEW, FEED, LIKE, VERBOSE, QUIT")
        print(f"Verbose mode: {'ON' if self.message_handler.verbose_mode else 'OFF'}")
        
        self.running = True
        while self.running:
            try:
                cmd = input("\nCommand (POST/DM/DMLIST/PROFILE/LIST/FOLLOW/UNFOLLOW/GROUP/GROUPVIEW/FEED/LIKE/VERBOSE/QUIT): ").strip().upper()
                
                if cmd == "QUIT" or cmd == "Q":
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
                elif cmd == "GROUP" or cmd == "G":
                    self._handle_group_command()
                elif cmd == "GROUPVIEW" or cmd == "GV":
                    self._handle_group_overview()
                elif cmd == "":
                    # Empty command, just continue
                    continue
                else:
                    print("Invalid command. Use POST, DM, DMLIST, PROFILE, LIST, FOLLOW, UNFOLLOW, GROUP, GROUPVIEW, FEED, LIKE, VERBOSE, or QUIT")
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
        
        # Also show groups if verbose mode is on
        if self.message_handler.verbose_mode:
            my_groups = self.peer_manager.get_my_groups()
            if my_groups:
                print(f"\n[MY GROUPS] ({len(my_groups)} groups):")
                for group_id in my_groups:
                    group = self.peer_manager.get_group(group_id)
                    if group:
                        creator_tag = " [Creator]" if group['creator'] == self.peer_manager.user_id else ""
                        print(f"  - {group['name']} (ID: {group_id}){creator_tag}")
                        print(f"    Members: {', '.join([self.peer_manager.get_display_name(m) for m in group['members']])}")
    
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
    
    def _handle_group_create(self):
        """Handle creating a new group"""
        group_id = input("Enter a unique group ID: ").strip()
        if not group_id:
            print("Group ID is required")
            return
            
        group_name = input("Enter a group name: ").strip()
        if not group_name:
            print("Group name is required")
            return
            
        members_input = input("Enter members (comma-separated user IDs): ").strip()
        members = []
        if members_input:
            members = [member.strip() for member in members_input.split(',') if member.strip()]
            
        # Check if members exist
        peers = self.peer_manager.get_all_peers()
        unknown_members = [member for member in members if member not in peers]
        if unknown_members:
            print(f"Warning: Some members are not in your peer list: {', '.join(unknown_members)}")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Group creation cancelled")
                return
                
        # Create group
        sent_count = self.message_handler.send_group_create(group_id, group_name, members)
        print(f"Group created. Invitation sent to {sent_count} members.")
    
    def _handle_group_update(self):
        """Handle updating group membership"""
        # Get group ID
        group_id = input("Enter group ID to update: ").strip()
        if not group_id:
            print("Group ID is required")
            return
            
        # Check if group exists and user is creator
        group = self.peer_manager.get_group(group_id)
        if not group:
            print(f"Group {group_id} not found")
            return
            
        if group['creator'] != self.peer_manager.user_id:
            print("Only the group creator can update members")
            return
            
        # Handle adding members
        add_members = []
        add_input = input("Enter members to add (comma-separated, press Enter to skip): ").strip()
        if add_input:
            add_members = [member.strip() for member in add_input.split(',') if member.strip()]
            
        # Handle removing members
        remove_members = []
        remove_input = input("Enter members to remove (comma-separated, press Enter to skip): ").strip()
        if remove_input:
            remove_members = [member.strip() for member in remove_input.split(',') if member.strip()]
            
        # Update group
        if not add_members and not remove_members:
            print("No changes specified")
            return
            
        sent_count = self.message_handler.send_group_update(group_id, add_members, remove_members)
        print(f"Group update sent to {sent_count} members.")
    
    def _handle_group_message(self):
        """Handle sending a message to a group"""
        # Get group ID
        group_id = input("Enter group ID to message: ").strip()
        if not group_id:
            print("Group ID is required")
            return
            
        # Check if group exists and user is a member
        if not self.peer_manager.is_in_group(group_id):
            print(f"You are not a member of group {group_id}")
            return
            
        # Get message content
        content = input("Enter your message: ").strip()
        if not content:
            print("Message content is required")
            return
            
        # Send message
        sent_count = self.message_handler.send_group_message(group_id, content)
        print(f"Message sent to {sent_count} group members.")
    
    def _handle_group_list(self):
        """Handle listing all groups the user is a member of"""
        self.message_handler.list_my_groups()
            
    def _handle_group_info(self):
        """Handle showing details about a specific group"""
        # Get group ID
        my_groups = self.peer_manager.get_my_groups()
        if not my_groups:
            print("You are not a member of any groups.")
            return
            
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
            
        # Check if group exists
        group = self.peer_manager.get_group(group_id)
        if not group:
            print(f"Group {group_id} not found")
            return
            
        # Check if user is the creator
        if group['creator'] == self.peer_manager.user_id:
            print("As the creator, you cannot leave the group. You would need to delete it instead.")
            return
            
        # Confirm leaving
        confirm = input(f"Are you sure you want to leave the group '{group['name']}'? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled")
            return
            
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
            print(f"Error: {e}")
    
    def _handle_update_group(self):
        """Update group membership"""
        # List groups where user is creator
        creator_groups = [
            group_id for group_id in self.peer_manager.get_my_groups()
            if self.peer_manager.is_group_creator(group_id)
        ]
        
        if not creator_groups:
            print("You are not the creator of any groups.")
            return
            
        print("\nGroups you created:")
        for idx, group_id in enumerate(creator_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if group:
                print(f"  {idx}. {group['name']} (ID: {group_id})")
        
        # Select group
        try:
            choice = int(input("\nSelect group number: ").strip())
            if choice < 1 or choice > len(creator_groups):
                print("Invalid choice")
                return
                
            selected_group_id = creator_groups[choice - 1]
            group = self.peer_manager.get_group(selected_group_id)
            
            # Show current members
            print(f"\nCurrent members of {group['name']} ({len(group['members'])}):")
            for member_id in group['members']:
                display_name = self.peer_manager.get_display_name(member_id)
                print(f"  - {display_name} ({member_id})")
            
            # Add members
            print("\nAvailable peers to add:")
            peers = self.peer_manager.get_all_peers()
            non_members = []
            
            for user_id, info in peers.items():
                if user_id not in group['members']:
                    display_name = self.peer_manager.get_display_name(user_id)
                    print(f"  - {display_name} ({user_id})")
                    non_members.append(user_id)
            
            add_members = []
            if non_members:
                add_input = input("\nAdd members (comma-separated, leave empty to skip): ").strip()
                if add_input:
                    for member_id in add_input.split(','):
                        member_id = member_id.strip()
                        if member_id and self.peer_manager.is_peer_known(member_id) and member_id not in group['members']:
                            add_members.append(member_id)
            
            # Remove members
            remove_members = []
            removable_members = [m for m in group['members'] if m != self.peer_manager.user_id]
            
            if removable_members:
                print("\nMembers available for removal:")
                for member_id in removable_members:
                    display_name = self.peer_manager.get_display_name(member_id)
                    print(f"  - {display_name} ({member_id})")
                    
                remove_input = input("\nRemove members (comma-separated, leave empty to skip): ").strip()
                if remove_input:
                    for member_id in remove_input.split(','):
                        member_id = member_id.strip()
                        if member_id and member_id in group['members'] and member_id != self.peer_manager.user_id:
                            remove_members.append(member_id)
            
            # Confirm updates
            if not add_members and not remove_members:
                print("No changes requested")
                return
                
            print("\nRequested changes:")
            if add_members:
                print(f"  Add: {', '.join(add_members)}")
            if remove_members:
                print(f"  Remove: {', '.join(remove_members)}")
                
            if input("Confirm these changes? (y/n): ").strip().lower() != 'y':
                print("Cancelled")
                return
                
            # Update the group
            sent_count = self.message_handler.send_group_update(selected_group_id, add_members, remove_members)
            print(f"Group updated and changes sent to {sent_count} peers")
            
        except ValueError:
            print("Please enter a valid number")
        except Exception as e:
            print(f"Error: {e}")
    
    def _handle_leave_group(self):
        """Leave a group"""
        # List groups where user is not creator
        member_groups = [
            group_id for group_id in self.peer_manager.get_my_groups()
            if not self.peer_manager.is_group_creator(group_id)
        ]
        
        if not member_groups:
            print("You are not a member of any groups you can leave.")
            print("Note: To delete a group you created, use the Delete Group option.")
            return
            
        print("\nGroups you can leave:")
        for idx, group_id in enumerate(member_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if group:
                print(f"  {idx}. {group['name']} (ID: {group_id})")
        
        # Select group
        try:
            choice = int(input("\nSelect group number: ").strip())
            if choice < 1 or choice > len(member_groups):
                print("Invalid choice")
                return
                
            selected_group_id = member_groups[choice - 1]
            group = self.peer_manager.get_group(selected_group_id)
            
            # Confirm
            if input(f"Confirm leaving the group '{group['name']}'? (y/n): ").strip().lower() != 'y':
                print("Cancelled")
                return
                
            # Leave the group
            success, message = self.peer_manager.leave_group(selected_group_id)
            if success:
                print(f"You have left the group '{group['name']}'")
            else:
                print(f"Error: {message}")
                
        except ValueError:
            print("Please enter a valid number")
        except Exception as e:
            print(f"Error: {e}")
    
    def _handle_delete_group(self):
        """Delete a group (creator only)"""
        # List groups where user is creator
        creator_groups = [
            group_id for group_id in self.peer_manager.get_my_groups()
            if self.peer_manager.is_group_creator(group_id)
        ]
        
        if not creator_groups:
            print("You are not the creator of any groups.")
            return
            
        print("\nGroups you can delete:")
        for idx, group_id in enumerate(creator_groups, 1):
            group = self.peer_manager.get_group(group_id)
            if group:
                print(f"  {idx}. {group['name']} (ID: {group_id})")
        
        # Select group
        try:
            choice = int(input("\nSelect group number: ").strip())
            if choice < 1 or choice > len(creator_groups):
                print("Invalid choice")
                return
                
            selected_group_id = creator_groups[choice - 1]
            group = self.peer_manager.get_group(selected_group_id)
            
            # Confirm
            print(f"WARNING: Deleting the group '{group['name']}' is permanent.")
            print(f"You will need to notify members manually that the group has been deleted.")
            if input(f"Type the group name to confirm deletion: ").strip() != group['name']:
                print("Confirmation failed. Group not deleted.")
                return
                
            # Delete the group
            success, message = self.peer_manager.delete_group(selected_group_id)
            if success:
                print(f"Group '{group['name']}' has been deleted")
            else:
                print(f"Error: {message}")
                
        except ValueError:
            print("Please enter a valid number")
        except Exception as e:
            print(f"Error: {e}")
    
    def _handle_group_detail_submenu(self, group_id):
        """Handle detailed actions for a specific group"""
        group = self.peer_manager.get_group(group_id)
        if not group:
            print(f"Group {group_id} not found")
            return
            
        print(f"\n===== {group['name']} (ID: {group_id}) =====")
        print("  1. View all members")
        print("  2. View all messages")
        print("  3. Send a message")
        print("  0. Back to group overview")
        
        choice = input("\nSelect option (0-3): ").strip()
        
        if choice == "1":
            self.message_handler.show_group_members(group_id)
        elif choice == "2":
            self.message_handler.show_group_messages(group_id)
        elif choice == "3":
            # Get message content
            content = input("Enter message: ").strip()
            if not content:
                print("Message content is required")
                return
                
            # Send the message
            sent_count = self.message_handler.send_group_message(group_id, content)
            print(f"Message sent to {sent_count} group members")
        elif choice == "0":
            return
        else:
            print("Invalid choice")
    
    def _handle_feed_command(self):
        """Display posts from users, with options to like/unlike"""
        import datetime
        
        print("\n=== Feed Options ===")
        print("1. View your posts")
        print("2. View posts from users you follow")
        print("3. View liked posts")
        print("4. Cancel")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            self._show_my_posts()
        elif choice == "2":
            self._show_following_posts()
        elif choice == "3":
            self._show_liked_posts()
        elif choice == "4":
            return
        else:
            print("Invalid choice. Please select 1-4.")
    
    def _show_my_posts(self):
        """Show posts created by the user"""
        import datetime
        import time
        
        # Get posts from the peer manager
        all_posts = self.peer_manager.get_user_posts(self.peer_manager.user_id)
        
        if not all_posts:
            print("You haven't posted anything yet.")
            return
            
        # Sort posts by timestamp (newest first)
        sorted_posts = sorted(all_posts.items(), key=lambda x: x[0], reverse=True)
        
        print("\n=== Your Posts ===")
        for idx, (timestamp, post_data) in enumerate(sorted_posts, 1):
            # Extract post data
            content = post_data['content']
            ttl = post_data['ttl']
            created_at = post_data['created_at']
            
            # Format timestamps
            try:
                ts_str = datetime.datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
                # Calculate expiration time
                expires_at = created_at + ttl
                expires_str = datetime.datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')
                # Calculate remaining time
                current_time = int(time.time())
                remaining_seconds = max(0, expires_at - current_time)
                remaining_str = self._format_time_remaining(remaining_seconds)
            except Exception:
                ts_str = str(timestamp)
                expires_str = "Unknown"
                remaining_str = "Unknown"
                
            # Get like count
            like_count = self.peer_manager.get_post_likes_count(timestamp)
            likes_label = f"{like_count} like{'s' if like_count != 1 else ''}"
            
            # Display post with index
            print(f"{idx}. [{ts_str}] {content} - {likes_label}")
            print(f"   Expires: {expires_str} ({remaining_str} remaining)")
            
        print("\nTo view who liked a post, use LIKE command option 3.")
    
    def _show_liked_posts(self):
        """Show posts liked by the user"""
        import datetime
        
        # Get liked posts
        liked_posts = self.peer_manager.liked_posts
        if not liked_posts:
            print("You haven't liked any posts yet.")
            return
        
        # Parse liked posts (format: "user_id:timestamp")
        liked_data = []
        for like_key in liked_posts:
            try:
                user_id, timestamp = like_key.split(':', 1)
                
                # Try to get actual content if available
                post_content = "Unknown content"
                user_posts = self.peer_manager.get_user_posts(user_id)
                if timestamp in user_posts:
                    post_content = user_posts[timestamp]
                    
                liked_data.append((user_id, timestamp, post_content))
            except ValueError:
                continue
                
        if not liked_data:
            print("No liked posts found.")
            return
                
        # Display liked posts
        print("\n=== Your Liked Posts ===")
        for idx, (user_id, timestamp, content) in enumerate(liked_data, 1):
            display_name = self.peer_manager.get_display_name(user_id) or user_id
            
            # Format timestamp
            try:
                ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = timestamp
                
            # Truncate content if available
            content_display = content[:30] + ("..." if len(content) > 30 else "")
            
            print(f"{idx}. [{ts_str}] {display_name}: {content_display} (ID: {timestamp})")
            
    def _show_following_posts(self):
        """Show posts from users you follow"""
        import datetime
        import time
        
        # Get list of users you follow
        following = self.peer_manager.following
        
        if not following:
            print("You're not following anyone.")
            return
            
        # Collect all posts from followed users
        all_posts = []
        for user_id in following:
            posts = self.peer_manager.get_user_posts(user_id)
            for timestamp, post_data in posts.items():
                all_posts.append((user_id, timestamp, post_data))
                
        if not all_posts:
            print("No posts from users you follow.")
            return
            
        # Sort posts by timestamp (newest first)
        sorted_posts = sorted(all_posts, key=lambda x: x[1], reverse=True)
        
        # Display posts
        print("\n=== Posts from Users You Follow ===")
        for idx, (user_id, timestamp, post_data) in enumerate(sorted_posts, 1):
            # Extract post data
            content = post_data['content']
            ttl = post_data['ttl']
            created_at = post_data['created_at']
            
            # Format timestamps
            try:
                ts_str = datetime.datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
                # Calculate expiration time
                expires_at = created_at + ttl
                expires_str = datetime.datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')
                # Calculate remaining time
                current_time = int(time.time())
                remaining_seconds = max(0, expires_at - current_time)
                remaining_str = self._format_time_remaining(remaining_seconds)
            except Exception:
                ts_str = str(timestamp)
                expires_str = "Unknown"
                remaining_str = "Unknown"
                
            # Get display name
            display_name = self.peer_manager.get_display_name(user_id) or user_id
            
            # Get like count
            like_count = self.peer_manager.get_post_likes_count(timestamp)
            likes_label = f"{like_count} like{'s' if like_count != 1 else ''}"
            
            # Check if user has liked this post
            liked_status = " ❤️" if self.peer_manager.has_liked_post(user_id, timestamp) else ""
            
            # Display post with index
            print(f"{idx}. [{ts_str}] {display_name}: {content} - {likes_label}{liked_status}")
            print(f"   Expires: {expires_str} ({remaining_str} remaining)")
    
    def _handle_like_command(self):
        """Handle liking/unliking posts"""
        print("\n=== Like/Unlike Posts ===")
        print("1. Like a post")
        print("2. Unlike a post")
        print("3. View post likes")
        print("4. Cancel")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            self._handle_like_post()
        elif choice == "2":
            self._handle_unlike_post()
        elif choice == "3":
            self._handle_view_likes()
        elif choice == "4":
            return
        else:
            print("Invalid choice. Please select 1-4.")
    
    def _handle_like_post(self):
        """Handle liking a post"""
        import datetime
        
        # Get list of peers
        peers = self.peer_manager.known_peers
        if not peers:
            print("You don't have any known peers.")
            return
            
        # Display list of peers
        print("\n=== Select a User ===")
        peer_ids = list(peers.keys())
        for idx, peer_id in enumerate(peer_ids, 1):
            display_name = self.peer_manager.get_display_name(peer_id) or peer_id
            print(f"{idx}. {display_name} ({peer_id})")
            
        # Get user selection
        try:
            user_idx = int(input("\nSelect user (0 to cancel): ").strip())
            if user_idx == 0:
                return
                
            if user_idx < 1 or user_idx > len(peer_ids):
                print("Invalid selection")
                return
                
            selected_user_id = peer_ids[user_idx - 1]
            
            # Get posts from the selected user
            user_posts = self.peer_manager.get_user_posts(selected_user_id)
            
            if not user_posts:
                print(f"No posts available from {selected_user_id}.")
                return
                
            # Sort posts by timestamp (newest first)
            sorted_posts = sorted(user_posts.items(), key=lambda x: x[0], reverse=True)
            
            # Display posts with formatting
            print(f"\n=== Posts from {selected_user_id} ===")
            for idx, (timestamp, post_data) in enumerate(sorted_posts, 1):
                # Extract post data
                content = post_data['content']
                ttl = post_data['ttl']
                created_at = post_data['created_at']
                
                # Format timestamp for display
                import time
                try:
                    ts_str = datetime.datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
                    # Calculate expiration time
                    expires_at = created_at + ttl
                    expires_str = datetime.datetime.fromtimestamp(expires_at).strftime('%Y-%m-%d %H:%M:%S')
                    # Calculate remaining time
                    current_time = int(time.time())
                    remaining_seconds = max(0, expires_at - current_time)
                    remaining_str = self._format_time_remaining(remaining_seconds)
                except Exception:
                    ts_str = timestamp
                    expires_str = "Unknown"
                    remaining_str = "Unknown"
                
                # Truncate long content
                truncated = content[:50] + ("..." if len(content) > 50 else "")
                
                # Check if already liked
                already_liked = self.peer_manager.has_liked_post(selected_user_id, timestamp)
                like_status = " (Already Liked ❤️)" if already_liked else ""
                
                print(f"{idx}. [{ts_str}] {truncated}{like_status}  (ID: {timestamp})")
                print(f"   Expires: {expires_str} ({remaining_str} remaining)")
                
            # Get post selection
            post_idx = int(input("\nSelect post to like (0 to cancel): ").strip())
            if post_idx == 0:
                return
                
            if post_idx < 1 or post_idx > len(sorted_posts):
                print("Invalid selection")
                return
                
            selected_timestamp = sorted_posts[post_idx - 1][0]
            selected_content = sorted_posts[post_idx - 1][1]['content']
            
            # Check if already liked
            if self.peer_manager.has_liked_post(selected_user_id, selected_timestamp):
                print("You already liked this post.")
                return
            
            # Send like message
            success = self.message_handler.send_like_message(selected_user_id, selected_timestamp, action='LIKE')
            if success:
                print(f"Liked post: \"{selected_content[:30]}...\"")
                
        except ValueError:
            print("Please enter a valid number")
    
    def _handle_unlike_post(self):
        """Handle unliking a post"""
        import datetime
        
        # Get liked posts
        liked_posts = self.peer_manager.liked_posts
        if not liked_posts:
            print("You haven't liked any posts yet.")
            return
        
        # Parse liked posts (format: "user_id:timestamp")
        liked_data = []
        for like_key in liked_posts:
            try:
                user_id, timestamp = like_key.split(':', 1)
                # Try to get actual content if available
                post_content = "Unknown content"
                user_posts = self.peer_manager.get_user_posts(user_id)
                if timestamp in user_posts:
                    post_content = user_posts[timestamp]
                
                liked_data.append((user_id, timestamp, post_content))
            except ValueError:
                continue
                
        if not liked_data:
            print("No liked posts found.")
            return
                
        # Display liked posts
        print("\n=== Your Liked Posts ===")
        for idx, (user_id, timestamp, content) in enumerate(liked_data, 1):
            display_name = self.peer_manager.get_display_name(user_id) or user_id
            
            # Format timestamp
            try:
                ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = timestamp
                
            # Truncate content if available
            content_display = content[:30] + ("..." if len(content) > 30 else "")
            
            print(f"{idx}. Post by {display_name} - \"{content_display}\" [{ts_str}] (ID: {timestamp})")
            
        # Get post selection
        try:
            post_idx = int(input("\nSelect post to unlike (0 to cancel): ").strip())
            if post_idx == 0:
                return
                
            if post_idx < 1 or post_idx > len(liked_data):
                print("Invalid selection")
                return
                
            selected_user_id = liked_data[post_idx - 1][0]
            selected_timestamp = liked_data[post_idx - 1][1]
            
            # Send unlike message
            success = self.message_handler.send_like_message(selected_user_id, selected_timestamp, action='UNLIKE')
            if success:
                print(f"Unliked post from {selected_user_id}")
                
        except ValueError:
            print("Please enter a valid number")
    
    def _handle_view_likes(self):
        """Handle viewing likes for a post"""
        # Show user posts
        all_posts = self.peer_manager.my_posts
        
        if not all_posts:
            print("You haven't posted anything yet.")
            return
            
        # Sort posts by timestamp (newest first)
        sorted_posts = sorted(all_posts.items(), key=lambda x: x[0], reverse=True)
        
        print("\n=== Your Posts ===")
        for idx, (timestamp, content) in enumerate(sorted_posts, 1):
            # Get like count
            like_count = self.peer_manager.get_post_likes_count(timestamp)
            likes_label = f"{like_count} like{'s' if like_count != 1 else ''}"
            
            # Display post with index
            print(f"{idx}. {content[:30]}... - {likes_label}")
            
        # Get post index
        try:
            post_idx = int(input("Enter post number to view likes (0 to cancel): ").strip())
            if post_idx == 0:
                return
                
            if post_idx < 1 or post_idx > len(sorted_posts):
                print("Invalid post number")
                return
                
            # Get post timestamp
            post_timestamp = sorted_posts[post_idx - 1][0]
            post_content = sorted_posts[post_idx - 1][1]
            
            # Get likes
            likers = self.peer_manager.get_post_likes(post_timestamp)
            if not likers:
                print(f"No likes for post: \"{post_content[:30]}...\"")
                return
                
            print(f"\nLikes for post \"{post_content[:30]}...\":")
            for liker_id in likers:
                display_name = self.peer_manager.get_display_name(liker_id) or liker_id
                print(f"- {display_name} ({liker_id})")
                
        except ValueError:
            print("Please enter a valid number")
            
    def _format_time_remaining(self, seconds):
        """Format seconds into a human-readable time string
        
        Args:
            seconds (int): Seconds to format
            
        Returns:
            str: Formatted time string
        """
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}"
