#!/usr/bin/env python3
"""
Group Chat Implementation
Implements methods for handling group chat operations
"""

def add_group(self, group_id, group_name, creator_id, members, timestamp):
    """Add a group the user belongs to"""
    if group_id not in self.groups:
        self.groups[group_id] = {
            'name': group_name,
            'creator': creator_id,
            'members': set(),
            'created_at': timestamp
        }
        
    # Update group info
    self.groups[group_id]['name'] = group_name
    
    # Update member list
    self.groups[group_id]['members'] = members
    
    # Check if user is creator
    if creator_id == self.user_id:
        self.created_groups.add(group_id)
        
    return True
    
def update_group(self, group_id, updater_id, add_members=None, remove_members=None):
    """Update group membership"""
    # Verify group exists
    if group_id not in self.groups:
        return False
        
    # Verify updater is creator (only creator can update)
    if self.groups[group_id]['creator'] != updater_id:
        return False
        
    # Add members
    if add_members:
        for member in add_members:
            self.groups[group_id]['members'].add(member)
            
    # Remove members
    if remove_members:
        for member in remove_members:
            if member in self.groups[group_id]['members']:
                self.groups[group_id]['members'].remove(member)
                
    return True
    
def leave_group(self, group_id):
    """Leave a group"""
    # Verify group exists
    if group_id not in self.groups:
        return False, "Group not found"
    
    # Remove self from members
    if self.user_id in self.groups[group_id]['members']:
        self.groups[group_id]['members'].remove(self.user_id)
    
    return True, "Left group successfully"
    
def get_my_groups(self):
    """Get groups the user is a member of"""
    return [group_id for group_id, group in self.groups.items() 
            if self.user_id in group['members']]
    
def get_created_groups(self):
    """Get groups created by the user"""
    return list(self.created_groups)
    
def is_in_group(self, group_id):
    """Check if user is in a group"""
    return (group_id in self.groups and 
            self.user_id in self.groups[group_id]['members'])
    
def get_group_name(self, group_id):
    """Get name of a group"""
    if group_id in self.groups:
        return self.groups[group_id]['name']
    return None
    
def get_group_members(self, group_id):
    """Get members of a group"""
    if group_id in self.groups:
        return self.groups[group_id]['members']
    return set()
