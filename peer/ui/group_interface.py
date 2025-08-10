#!/usr/bin/env python3
"""
Group User Interface Implementation
Implements UI methods for group chat operations
"""

def _handle_group_command(self):
    """Handle GROUP command with submenu"""
    print("\nGroup Chat Operations:")
    print("  1. CREATE - Create a new group")
    print("  2. UPDATE - Add/remove members from a group")
    print("  3. MESSAGE - Send a message to a group")
    print("  4. LIST - List all your groups")
    print("  5. INFO - Show details about a specific group")
    print("  6. LEAVE - Leave a group")
    print("  0. Back to main menu")
    
    try:
        choice = input("\nSelect option (0-6): ").strip()
        
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
            self._handle_group_leave()
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
    my_groups = self.peer_manager.get_my_groups()
    
    if not my_groups:
        print("You are not a member of any groups.")
        return
        
    print(f"\nYour Groups ({len(my_groups)}):")
    for i, group_id in enumerate(my_groups, 1):
        group = self.peer_manager.get_group(group_id)
        if not group:
            continue
            
        creator_status = " (Creator)" if group['creator'] == self.peer_manager.user_id else ""
        member_count = len(group['members'])
        print(f"{i}. {group['name']} (ID: {group_id}){creator_status}")
        print(f"   Members: {member_count}")
        
def _handle_group_info(self):
    """Handle showing details about a specific group"""
    # Get group ID
    group_id = input("Enter group ID: ").strip()
    if not group_id:
        print("Group ID is required")
        return
        
    # Check if group exists
    group = self.peer_manager.get_group(group_id)
    if not group:
        print(f"Group {group_id} not found")
        return
        
    # Show group details
    creator_id = group['creator']
    creator_name = self.peer_manager.get_display_name(creator_id) or creator_id
    
    print(f"\nGroup: {group['name']} (ID: {group_id})")
    print(f"Created by: {creator_name} ({creator_id})")
    
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
        creator_marker = " (Creator)" if member_id == creator_id else ""
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
        
    # Leave group
    success, message = self.peer_manager.leave_group(group_id)
    print(message)
