#!/usr/bin/env python3
"""
Group Message Handler Implementation
Implements methods for handling group message operations
"""
import time
import datetime

def send_group_create(self, group_id, group_name, members):
    """Send a group creation message to all members"""
    # Validate parameters
    if not group_id or not group_name:
        print("Group ID and name are required")
        return 0
        
    # Add current user to members if not already there
    member_set = set(members)
    member_set.add(self.peer_manager.user_id)
    members_str = ','.join(member_set)
    
    # Prepare message
    message = {
        'TYPE': 'GROUP_CREATE',
        'FROM': self.peer_manager.user_id,
        'GROUP_ID': group_id,
        'GROUP_NAME': group_name,
        'MEMBERS': members_str,
        'TIMESTAMP': str(int(time.time())),
        'MESSAGE_ID': self._generate_message_id()
    }
    
    # Process locally to create the group for the current user
    self.handle_group_create(message, ('127.0.0.1', 0))
    
    # Send to all specified members except self
    sent_count = 0
    for member_id in member_set:
        if member_id == self.peer_manager.user_id:
            continue
            
        peer_info = self.peer_manager.get_peer_info(member_id)
        if peer_info:
            if self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port']):
                sent_count += 1
                
    return sent_count
    
def handle_group_create(self, msg_dict, addr):
    """Handle group creation messages"""
    import datetime

    from_user = msg_dict.get('FROM', 'Unknown')
    group_id = msg_dict.get('GROUP_ID', '')
    group_name = msg_dict.get('GROUP_NAME', '')
    members_str = msg_dict.get('MEMBERS', '')
    timestamp = msg_dict.get('TIMESTAMP', int(time.time()))
    
    # Parse members list
    if members_str:
        members = set(member.strip() for member in members_str.split(',') if member.strip())
    else:
        members = set()
        
    # Always include creator
    members.add(from_user)
    
    if self.verbose_mode:
        # Format timestamp
        try:
            ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_str = str(timestamp)
            
        print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: GROUP_CREATE")
        print(f"FROM: {from_user}")
        print(f"GROUP_ID: {group_id}")
        print(f"GROUP_NAME: {group_name}")
        print(f"MEMBERS: {members_str}")
        print(f"TIMESTAMP: {timestamp}")
    else:
        print(f"\nYou've been added to {group_name}")
        
    # Add group to peer manager
    self.peer_manager.add_group(group_id, group_name, from_user, members, timestamp)
    
def send_group_update(self, group_id, add_members=None, remove_members=None):
    """Send a group update message to all members"""
    # Validate parameters
    if not group_id:
        print("Group ID is required")
        return 0
        
    # Verify the group exists and user is creator
    group = self.peer_manager.get_group(group_id)
    if not group:
        print(f"Group {group_id} not found")
        return 0
        
    if group['creator'] != self.peer_manager.user_id:
        print("Only the group creator can update members")
        return 0
        
    # Initialize member sets
    add_set = set() if add_members is None else set(add_members)
    remove_set = set() if remove_members is None else set(remove_members)
    
    # Prepare member strings
    add_str = ','.join(add_set) if add_set else ''
    remove_str = ','.join(remove_set) if remove_set else ''
    
    # Prepare message
    message = {
        'TYPE': 'GROUP_UPDATE',
        'FROM': self.peer_manager.user_id,
        'GROUP_ID': group_id,
        'ADD': add_str,
        'REMOVE': remove_str,
        'TIMESTAMP': str(int(time.time())),
        'MESSAGE_ID': self._generate_message_id()
    }
    
    # Process locally first
    self.handle_group_update(message, ('127.0.0.1', 0))
    
    # Send to all current members (including those being added, excluding those being removed)
    members = self.peer_manager.get_group_members(group_id).copy()
    
    # Add new members to recipient list
    members.update(add_set)
    
    # Send message
    sent_count = 0
    for member_id in members:
        if member_id == self.peer_manager.user_id:
            continue
            
        peer_info = self.peer_manager.get_peer_info(member_id)
        if peer_info:
            if self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port']):
                sent_count += 1
                
    return sent_count
    
def handle_group_update(self, msg_dict, addr):
    """Handle group update messages"""
    import datetime

    from_user = msg_dict.get('FROM', 'Unknown')
    group_id = msg_dict.get('GROUP_ID', '')
    add_members_str = msg_dict.get('ADD', '')
    remove_members_str = msg_dict.get('REMOVE', '')
    timestamp = msg_dict.get('TIMESTAMP', int(time.time()))
    
    # Parse add/remove lists
    add_members = set(member.strip() for member in add_members_str.split(',') if member.strip())
    remove_members = set(member.strip() for member in remove_members_str.split(',') if member.strip())
    
    if self.verbose_mode:
        # Format timestamp
        try:
            ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_str = str(timestamp)
            
        print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: GROUP_UPDATE")
        print(f"FROM: {from_user}")
        print(f"GROUP_ID: {group_id}")
        if add_members:
            print(f"ADD: {add_members_str}")
        if remove_members:
            print(f"REMOVE: {remove_members_str}")
        print(f"TIMESTAMP: {timestamp}")
    else:
        group_name = self.peer_manager.get_group_name(group_id) or group_id
        print(f"\nThe group \"{group_name}\" member list was updated.")
        
    # Update group in peer manager
    self.peer_manager.update_group(group_id, from_user, add_members, remove_members)
    
def send_group_message(self, group_id, content):
    """Send a message to a group"""
    # Validate parameters
    if not group_id or not content:
        print("Group ID and message content are required")
        return 0
        
    # Verify the group exists and user is a member
    if not self.peer_manager.is_in_group(group_id):
        print(f"You are not a member of group {group_id}")
        return 0
        
    # Get the group name
    group_name = self.peer_manager.get_group_name(group_id) or group_id
    
    # Prepare message
    message = {
        'TYPE': 'GROUP_MESSAGE',
        'FROM': self.peer_manager.user_id,
        'GROUP_ID': group_id,
        'CONTENT': content,
        'TIMESTAMP': str(int(time.time())),
        'MESSAGE_ID': self._generate_message_id()
    }
    
    # Process locally first (show in own chat)
    self.handle_group_message(message, ('127.0.0.1', 0))
    
    # Send to all members except self
    members = self.peer_manager.get_group_members(group_id)
    sent_count = 0
    
    for member_id in members:
        if member_id == self.peer_manager.user_id:
            continue
            
        peer_info = self.peer_manager.get_peer_info(member_id)
        if peer_info:
            if self.network_manager.send_to_address(message, peer_info['ip'], peer_info['port']):
                sent_count += 1
                
    return sent_count
    
def handle_group_message(self, msg_dict, addr):
    """Handle messages to groups"""
    import datetime

    from_user = msg_dict.get('FROM', 'Unknown')
    group_id = msg_dict.get('GROUP_ID', '')
    content = msg_dict.get('CONTENT', '')
    timestamp = msg_dict.get('TIMESTAMP', int(time.time()))
    
    # Verify this is a valid group and we're a member
    if not self.peer_manager.is_in_group(group_id):
        # Not a member, ignore the message
        return
        
    # Get group and sender info
    group_name = self.peer_manager.get_group_name(group_id) or group_id
    display_name = self.peer_manager.get_display_name(from_user) or from_user
    
    if self.verbose_mode:
        # Format timestamp
        try:
            ts_str = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            ts_str = str(timestamp)
            
        print(f"\nRECV < [{ts_str}] From {addr[0]} | Type: GROUP_MESSAGE")
        print(f"FROM: {from_user}")
        print(f"GROUP_ID: {group_id}")
        print(f"GROUP_NAME: {group_name}")
        print(f"CONTENT: {content}")
        print(f"TIMESTAMP: {timestamp}")
    else:
        # User-friendly format
        print(f"\n[{group_name}] {display_name}: {content}")
