#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitLab API script for version 15.11
Implement functions for managing user permissions and retrieve issues/MRs by the year.
"""

import os
import sys
import json
import requests
from typing import List, Dict, Optional, Union
from datetime import datetime

class GitLabAPI:
    """GitLab API client for version 15.11"""
    
    def __init__(self, base_url: str = None, token: str = None):
        """
        Initialize GitLab API client.
        
        Args:
            base_url: GitLab instance URL (default is GITLAB_URL env var)
            token: GitLab access token (default is GITLAB_TOKEN env var)
        """
        self.base_url = (base_url or os.getenv('GITLAB_URL', 'http://localhost')).rstrip('/')
        self.token = token or os.getenv('GITLAB_TOKEN')
        
        if not self.token:
            raise ValueError("GitLab token required. Set GITLAB_TOKEN environment variable.")
        
        self.headers = {
            'PRIVATE-TOKEN': self.token,
            'Content-Type': 'application/json'
        }
        self.api_base = f"{self.base_url}/api/v4"
    
    def _get_project_id(self, project_path: str) -> Optional[int]:
        """Get project ID from project path (group/project)."""
        try:
            encoded_path = requests.utils.quote(project_path, safe='')
            response = requests.get(
                f"{self.api_base}/projects/{encoded_path}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get('id')
            return None
        except Exception as e:
            print(f"Error getting project ID: {e}", file=sys.stderr)
            return None
    
    def _get_group_id(self, group_path: str) -> Optional[int]:
        """Get group ID from group path."""
        try:
            encoded_path = requests.utils.quote(group_path, safe='')
            response = requests.get(
                f"{self.api_base}/groups/{encoded_path}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get('id')
            return None
        except Exception as e:
            print(f"Error getting group ID: {e}", file=sys.stderr)
            return None
    
    def _get_user_id(self, username: str) -> Optional[int]:
        """Get user ID from username."""
        try:
            response = requests.get(
                f"{self.api_base}/users",
                headers=self.headers,
                params={'username': username}
            )
            if response.status_code == 200:
                users = response.json()
                if users:
                    return users[0].get('id')
            return None
        except Exception as e:
            print(f"Error getting user ID: {e}", file=sys.stderr)
            return None
    
    def grant_role_permissions(self, username: str, repository_or_group: str, role: str) -> Dict:
        """
        Grant or change role permissions to a user on a repository or group.
        
        Args:
            username: GitLab username
            repository_or_group: Repository path (group/project) or group path
            role: Role to assign (e.g., 'Guest', 'Reporter', 'Developer', 'Maintainer', 'Owner')
        
        Returns:
            Dictionary with success status and message
        """
        try:
            # Get user ID
            user_id = self._get_user_id(username)
            if not user_id:
                return {
                    'success': False,
                    'message': f'User "{username}" not found'
                }
            
            # Try to get project ID first (repository)
            project_id = self._get_project_id(repository_or_group)
            
            if project_id:

                return self._add_project_member(project_id, user_id, role)
            else:
                # Try group
                group_id = self._get_group_id(repository_or_group)
                if group_id:
                    return self._add_group_member(group_id, user_id, role)
                else:
                    return {
                        'success': False,
                        'message': f'Repository or group "{repository_or_group}" not found'
                    }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error granting permissions: {str(e)}'
            }
    
    def _add_project_member(self, project_id: int, user_id: int, role: str) -> Dict:
        """Add or update project member."""
        try:
            # Check if member alreadexists
            response = requests.get(
                f"{self.api_base}/projects/{project_id}/members/{user_id}",
                headers=self.headers
            )
            
            data = {
                'user_id': user_id,
                'access_level': self._role_to_access_level(role)
            }
            
            if response.status_code == 200:
                # Update  member if already exists
                response = requests.put(
                    f"{self.api_base}/projects/{project_id}/members/{user_id}",
                    headers=self.headers,
                    json=data
                )
                action = 'updated'
            else:
                # Add a member
                response = requests.post(
                    f"{self.api_base}/projects/{project_id}/members",
                    headers=self.headers,
                    json=data
                )
                action = 'granted'
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': f'Role {action} successfully. User "{user_id}" now has "{role}" role on project "{project_id}"'
                }
            else:
                error_msg = response.json().get('message', 'Unknown error')
                return {
                    'success': False,
                    'message': f'Failed to {action} role: {error_msg}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error managing project member: {str(e)}'
            }
    
    def _add_group_member(self, group_id: int, user_id: int, role: str) -> Dict:
        """Add or update group member."""
        try:
            # Check if member already exists
            response = requests.get(
                f"{self.api_base}/groups/{group_id}/members/{user_id}",
                headers=self.headers
            )
            
            data = {
                'user_id': user_id,
                'access_level': self._role_to_access_level(role)
            }
            
            if response.status_code == 200:
                # Update existing member
                response = requests.put(
                    f"{self.api_base}/groups/{group_id}/members/{user_id}",
                    headers=self.headers,
                    json=data
                )
                action = 'updated'
            else:
                # TODOadd new member
                response = requests.post(
                    f"{self.api_base}/groups/{group_id}/members",
                    headers=self.headers,
                    json=data
                )
                action = 'granted'
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': f'Role {action} successfully. User "{user_id}" now has "{role}" role on group "{group_id}"'
                }
            else:
                error_msg = response.json().get('message', 'Unknown error')
                return {
                    'success': False,
                    'message': f'Failed to {action} role: {error_msg}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error managing group member: {str(e)}'
            }
    
    def _role_to_access_level(self, role: str) -> int:
        """
        Convert role name to GitLab access level.
        Reference: https://archives.docs.gitlab.com/15.11/ee/api/members.html#roles
        """
        role_map = {
            'Guest': 10,
            'Reporter': 20,
            'Developer': 30,
            'Maintainer': 40,
            'Owner': 50
        }
        role_normalized = role.capitalize()
        if role_normalized not in role_map:
            raise ValueError(f'Invalid role: {role}. Valid roles: {list(role_map.keys())}')
        return role_map[role_normalized]
    
    def get_items_by_year(self, item_type: str, year: int) -> Dict:
        """
        Get all issues or merge requests created in the given year.
        
        Args:
            item_type: Either 'issues' or 'mr' (merge requests)
            year: 4-digit year (e.g., 2025)
        
        Returns:
            Dictionary with success status and list of items
        """
        try:
            if item_type not in ['mr', 'issues']:
                return {
                    'success': False,
                    'message': f'Invalid item_type: {item_type}. Must be "mr" or "issues"'
                }
            
            if not isinstance(year, int) or len(str(year)) != 4:
                return {
                    'success': False,
                    'message': f'Invalid year: {year}. Must be a 4-digit integer'
                }
            
            # Calculate date range for the year
            start_date = f"{year}-01-01T00:00:00Z"
            end_date = f"{year}-12-31T23:59:59Z"
            
            all_items = []
            page = 1
            per_page = 100
            
            while True:
                if item_type == 'issues':
                    endpoint = f"{self.api_base}/issues"
                    params = {
                        'created_after': start_date,
                        'created_before': end_date,
                        'page': page,
                        'per_page': per_page,
                        'scope': 'all'  # Get all issues across all projects
                    }
                else:  # mr
                    endpoint = f"{self.api_base}/merge_requests"
                    params = {
                        'created_after': start_date,
                        'created_before': end_date,
                        'page': page,
                        'per_page': per_page,
                        'scope': 'all'  # Get all MRs across all projects
                    }
                
                response = requests.get(endpoint, headers=self.headers, params=params)
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'message': f'API request failed: {response.status_code} - {response.text}'
                    }
                
                items = response.json()
                if not items:
                    break
                
                all_items.extend(items)
                
                # Check if there are more pages
                if len(items) < per_page:
                    break
                
                page += 1
            
            return {
                'success': True,
                'count': len(all_items),
                'items': all_items,
                'message': f'Found {len(all_items)} {item_type} created in {year}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving items: {str(e)}'
            }


def main():
    """Main entry point for command-line interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  grant_role <username> <repository_or_group> <role>")
        print("  get_items <mr|issues> <year>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        api = GitLabAPI()
        
        if command == 'grant_role':
            if len(sys.argv) != 5:
                print("Error: grant_role requires 3 arguments: username, repository_or_group, role")
                sys.exit(1)
            
            username = sys.argv[2]
            repository_or_group = sys.argv[3]
            role = sys.argv[4]
            
            result = api.grant_role_permissions(username, repository_or_group, role)
            print(json.dumps(result, indent=2))
            
            if not result['success']:
                sys.exit(1)
        
        elif command == 'get_items':
            if len(sys.argv) != 4:
                print("Error: get_items requires 2 arguments: item_type (mr|issues), year")
                sys.exit(1)
            
            item_type = sys.argv[2]
            try:
                year = int(sys.argv[3])
            except ValueError:
                print("Error: year must be an integer")
                sys.exit(1)
            
            result = api.get_items_by_year(item_type, year)
            print(json.dumps(result, indent=2))
            
            if not result['success']:
                sys.exit(1)
        
        else:
            print(f"Error: Unknown command '{command}'")
            print("Available commands: grant_role, get_items")
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({'success': False, 'message': str(e)}, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()

