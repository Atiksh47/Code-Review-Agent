"""
Git Integration module for repository analysis
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

@dataclass
class CommitInfo:
    """Information about a Git commit"""
    hash: str
    author: str
    email: str
    date: datetime
    message: str
    files_changed: List[str]
    insertions: int
    deletions: int

@dataclass
class BranchInfo:
    """Information about a Git branch"""
    name: str
    is_current: bool
    last_commit: str
    last_commit_date: datetime
    ahead: int
    behind: int

class GitIntegration:
    """Git repository integration and analysis"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.git.enabled
        self.auto_review_commits = config.git.auto_review_commits
        self.review_branches = config.git.review_branches
        self.exclude_patterns = config.git.exclude_patterns
    
    def is_git_repository(self, path: Path) -> bool:
        """Check if the given path is a Git repository"""
        if not self.enabled:
            return False
        
        git_dir = path / '.git'
        return git_dir.exists() and git_dir.is_dir()
    
    def get_repository_info(self, path: Path) -> Dict[str, Any]:
        """Get basic repository information"""
        if not self.is_git_repository(path):
            return {"error": "Not a Git repository"}
        
        try:
            info = {}
            
            # Get repository URL
            info['remote_url'] = self._get_remote_url(path)
            
            # Get current branch
            info['current_branch'] = self._get_current_branch(path)
            
            # Get last commit info
            info['last_commit'] = self._get_last_commit(path)
            
            # Get branch information
            info['branches'] = self._get_branches(path)
            
            # Get repository statistics
            info['stats'] = self._get_repository_stats(path)
            
            return info
            
        except Exception as e:
            return {"error": f"Failed to get repository info: {str(e)}"}
    
    def get_commits_since(self, path: Path, since: Optional[datetime] = None) -> List[CommitInfo]:
        """Get commits since a specific date"""
        if not self.is_git_repository(path):
            return []
        
        try:
            # Build git log command
            cmd = ['git', 'log', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=iso']
            
            if since:
                cmd.extend(['--since', since.isoformat()])
            
            # Execute command
            result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) >= 5:
                    commit_hash = parts[0]
                    author = parts[1]
                    email = parts[2]
                    date_str = parts[3]
                    message = parts[4]
                    
                    # Parse date
                    try:
                        date = datetime.fromisoformat(date_str.replace(' +', '+').replace(' -', '-'))
                    except:
                        date = datetime.now()
                    
                    # Get file changes for this commit
                    files_changed, insertions, deletions = self._get_commit_stats(path, commit_hash)
                    
                    commits.append(CommitInfo(
                        hash=commit_hash,
                        author=author,
                        email=email,
                        date=date,
                        message=message,
                        files_changed=files_changed,
                        insertions=insertions,
                        deletions=deletions
                    ))
            
            return commits
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting commits: {e}")
            return []
    
    def get_changed_files(self, path: Path, commit_range: Optional[str] = None) -> List[Path]:
        """Get list of changed files in a commit range"""
        if not self.is_git_repository(path):
            return []
        
        try:
            cmd = ['git', 'diff', '--name-only']
            
            if commit_range:
                cmd.append(commit_range)
            else:
                cmd.append('HEAD~1')
                cmd.append('HEAD')
            
            result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            
            changed_files = []
            for line in result.stdout.strip().split('\n'):
                if line and not self._should_exclude_file(Path(line)):
                    changed_files.append(path / line)
            
            return changed_files
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting changed files: {e}")
            return []
    
    def get_file_blame(self, path: Path, file_path: Path) -> List[Dict[str, Any]]:
        """Get blame information for a file"""
        if not self.is_git_repository(path):
            return []
        
        try:
            # Get relative path from repository root
            rel_path = file_path.relative_to(path)
            
            cmd = ['git', 'blame', '--line-porcelain', str(rel_path)]
            
            result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            
            blame_info = []
            current_commit = {}
            line_num = 1
            
            for line in result.stdout.split('\n'):
                if line.startswith('author '):
                    current_commit['author'] = line[7:]
                elif line.startswith('author-time '):
                    current_commit['author_time'] = int(line[12:])
                elif line.startswith('summary '):
                    current_commit['summary'] = line[8:]
                elif line.startswith('\t'):
                    # This is the actual line content
                    current_commit['line_number'] = line_num
                    current_commit['content'] = line[1:]
                    blame_info.append(current_commit.copy())
                    line_num += 1
                    current_commit = {}
            
            return blame_info
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting blame info: {e}")
            return []
    
    def get_repository_metrics(self, path: Path) -> Dict[str, Any]:
        """Get various repository metrics"""
        if not self.is_git_repository(path):
            return {}
        
        try:
            metrics = {}
            
            # Get total commits
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            metrics['total_commits'] = int(result.stdout.strip())
            
            # Get total contributors
            result = subprocess.run(
                ['git', 'shortlog', '-sn'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            metrics['total_contributors'] = len(result.stdout.strip().split('\n'))
            
            # Get repository size
            result = subprocess.run(
                ['git', 'count-objects', '-vH'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n'):
                if line.startswith('size-pack:'):
                    metrics['repository_size'] = line.split(':')[1].strip()
                    break
            
            # Get file count by language
            metrics['languages'] = self._get_language_stats(path)
            
            return metrics
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting repository metrics: {e}")
            return {}
    
    def _get_remote_url(self, path: Path) -> Optional[str]:
        """Get the remote URL of the repository"""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def _get_current_branch(self, path: Path) -> Optional[str]:
        """Get the current branch name"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def _get_last_commit(self, path: Path) -> Optional[Dict[str, Any]]:
        """Get information about the last commit"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=iso'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            
            parts = result.stdout.strip().split('|')
            if len(parts) >= 5:
                return {
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'date': parts[3],
                    'message': parts[4]
                }
        except subprocess.CalledProcessError:
            pass
        
        return None
    
    def _get_branches(self, path: Path) -> List[BranchInfo]:
        """Get information about all branches"""
        try:
            result = subprocess.run(
                ['git', 'branch', '-v'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            
            branches = []
            current_branch = self._get_current_branch(path)
            
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                
                is_current = line.startswith('*')
                parts = line.strip().split()
                
                if len(parts) >= 3:
                    name = parts[0] if not is_current else parts[1]
                    last_commit = parts[1] if not is_current else parts[2]
                    
                    branches.append(BranchInfo(
                        name=name,
                        is_current=is_current,
                        last_commit=last_commit,
                        last_commit_date=datetime.now(),  # Would need additional call to get actual date
                        ahead=0,  # Would need additional call to get ahead/behind info
                        behind=0
                    ))
            
            return branches
            
        except subprocess.CalledProcessError:
            return []
    
    def _get_repository_stats(self, path: Path) -> Dict[str, Any]:
        """Get repository statistics"""
        try:
            stats = {}
            
            # Get total lines of code
            result = subprocess.run(
                ['git', 'ls-files', '|', 'xargs', 'wc', '-l'],
                cwd=path,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')[-1]
                if 'total' in lines.lower():
                    stats['total_lines'] = int(lines.split()[0])
            
            return stats
            
        except subprocess.CalledProcessError:
            return {}
    
    def _get_commit_stats(self, path: Path, commit_hash: str) -> Tuple[List[str], int, int]:
        """Get file changes and line statistics for a commit"""
        try:
            result = subprocess.run(
                ['git', 'show', '--stat', '--format=', commit_hash],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files_changed = []
            total_insertions = 0
            total_deletions = 0
            
            for line in result.stdout.split('\n'):
                if '|' in line and 'file' not in line.lower():
                    parts = line.split('|')
                    if len(parts) >= 2:
                        file_path = parts[0].strip()
                        files_changed.append(file_path)
                        
                        # Parse insertions/deletions
                        stats = parts[1].strip()
                        if 'insertion' in stats and 'deletion' in stats:
                            # Format: "2 insertions(+), 1 deletion(-)"
                            import re
                            insertions = re.search(r'(\d+)\s+insertion', stats)
                            deletions = re.search(r'(\d+)\s+deletion', stats)
                            
                            if insertions:
                                total_insertions += int(insertions.group(1))
                            if deletions:
                                total_deletions += int(deletions.group(1))
            
            return files_changed, total_insertions, total_deletions
            
        except subprocess.CalledProcessError:
            return [], 0, 0
    
    def _get_language_stats(self, path: Path) -> Dict[str, int]:
        """Get statistics about programming languages used"""
        try:
            result = subprocess.run(
                ['git', 'ls-files'],
                cwd=path,
                capture_output=True,
                text=True,
                check=True
            )
            
            language_counts = {}
            ext_to_lang = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.java': 'Java',
                '.cpp': 'C++',
                '.c': 'C',
                '.go': 'Go',
                '.rs': 'Rust',
                '.php': 'PHP',
                '.rb': 'Ruby',
                '.ts': 'TypeScript',
                '.html': 'HTML',
                '.css': 'CSS',
                '.sql': 'SQL',
                '.sh': 'Shell',
                '.yml': 'YAML',
                '.yaml': 'YAML',
                '.json': 'JSON',
                '.xml': 'XML',
                '.md': 'Markdown',
                '.txt': 'Text'
            }
            
            for line in result.stdout.split('\n'):
                if line.strip():
                    file_path = Path(line)
                    ext = file_path.suffix.lower()
                    language = ext_to_lang.get(ext, 'Other')
                    language_counts[language] = language_counts.get(language, 0) + 1
            
            return language_counts
            
        except subprocess.CalledProcessError:
            return {}
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded based on patterns"""
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return True
        return False
