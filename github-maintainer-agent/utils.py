"""
Simple utility functions for the GitHub Maintainer Bot
"""

import re
from typing import List, Dict

def is_github_notification(email_from: str) -> bool:
    """Check if email is from GitHub"""
    return "github.com" in email_from.lower()

def extract_github_info(email_subject: str, email_body: str) -> Dict:
    """Extract comprehensive GitHub information from email notifications"""
    info = {
        'is_github': is_github_notification(email_subject + " " + email_body),
        'is_pr': False,
        'is_issue': False,
        'is_comment': False,
        'is_review': False,
        'is_new': False,
        'is_closed': False,
        'repo_name': None,
        'pr_number': None,
        'issue_number': None,
        'author': None,
        'action': None,
        'title': None,
        'files_changed': [],
        'summary': None
    }
    
    if not info['is_github']:
        return info
    
    # Detect notification types from subject
    subject_lower = email_subject.lower()
    
    # PR detection
    if any(phrase in subject_lower for phrase in ['pull request', 'pr opened', 'pr #']):
        info['is_pr'] = True
        info['is_new'] = 'opened' in subject_lower or 'new pull request' in subject_lower
        info['is_closed'] = 'closed' in subject_lower or 'merged' in subject_lower
    
    # Issue detection  
    elif any(phrase in subject_lower for phrase in ['issue', 'bug report']) and 'pull request' not in subject_lower:
        info['is_issue'] = True
        info['is_new'] = 'opened' in subject_lower or 'new issue' in subject_lower
        info['is_closed'] = 'closed' in subject_lower
    
    # Comment detection
    elif any(phrase in subject_lower for phrase in ['commented', 'comment on', 'replied to']):
        info['is_comment'] = True
        info['is_pr'] = 'pull request' in subject_lower
        info['is_issue'] = 'issue' in subject_lower and 'pull request' not in subject_lower
    
    # Review detection
    elif any(phrase in subject_lower for phrase in ['review', 'approved', 'requested changes']):
        info['is_review'] = True
        info['is_pr'] = True
    
    # Extract repository name [owner/repo]
    repo_match = re.search(r'\[([^/]+/[^]]+)\]', email_subject)
    if repo_match:
        info['repo_name'] = repo_match.group(1)
    
    # Extract PR/issue numbers #123
    number_match = re.search(r'#(\d+)', email_subject)
    if number_match:
        number = number_match.group(1)
        if info['is_pr']:
            info['pr_number'] = number
        elif info['is_issue']:
            info['issue_number'] = number
    
    # Extract title after #number:
    title_match = re.search(r'#\d+:\s*(.+)$', email_subject)
    if title_match:
        info['title'] = title_match.group(1).strip()
    
    # Extract author from body
    author_patterns = [
        r'@(\w+)\s+opened',
        r'@(\w+)\s+commented',
        r'(\w+)\s+opened',
        r'Author:\s*@?(\w+)'
    ]
    for pattern in author_patterns:
        match = re.search(pattern, email_body)
        if match:
            info['author'] = match.group(1)
            break
    
    # Extract files changed from body
    files_match = re.findall(r'([a-zA-Z0-9_./\-]+\.[a-zA-Z]{1,4})', email_body)
    if files_match:
        info['files_changed'] = list(set(files_match))  # Remove duplicates
    
    # Determine action
    if info['is_new']:
        info['action'] = 'opened'
    elif info['is_closed']:
        info['action'] = 'closed'
    elif info['is_comment']:
        info['action'] = 'commented'
    elif info['is_review']:
        info['action'] = 'reviewed'
    else:
        info['action'] = 'updated'
    
    # Create summary
    item_type = 'PR' if info['is_pr'] else 'issue' if info['is_issue'] else 'item'
    info['summary'] = f"{info['author'] or 'Someone'} {info['action']} {item_type} #{info.get('pr_number') or info.get('issue_number') or '?'}"
    if info['title']:
        info['summary'] += f": {info['title']}"
    
    return info

def is_question(text: str) -> bool:
    """Simple check if text contains questions"""
    question_words = [
        'how', 'what', 'why', 'when', 'where', 'which', 'who',
        'can i', 'could you', 'would you', 'should i',
        'help', 'issue', 'problem', 'error'
    ]
    text_lower = text.lower()
    return '?' in text or any(word in text_lower for word in question_words)

def create_welcome_response(sender_name: str, repo_name: str, is_pr: bool = False) -> str:
    """Create a simple welcome response for new contributors"""
    if is_pr:
        return f"""<p>Hello {sender_name}! 👋</p>
<p>Thank you for your pull request to <strong>{repo_name}</strong>! We really appreciate your contribution.</p>
<p>Our maintainers will review your changes soon. While you wait, please make sure:</p>
<ul>
<li>All tests are passing ✅</li>
<li>Your code follows our guidelines 📝</li>
<li>You've updated documentation if needed 📚</li>
</ul>
<p>Feel free to reply if you have any questions!</p>
<p><em>Best regards,<br>Your GitHub Maintainer Bot 🤖</em></p>"""
    else:
        return f"""<p>Hello {sender_name}! 👋</p>
<p>Thank you for opening this issue in <strong>{repo_name}</strong>! We've received your report.</p>
<p>To help us resolve this quickly, please ensure you've included:</p>
<ul>
<li>Steps to reproduce the issue 🔄</li>
<li>Expected vs actual behavior 📋</li>
<li>Your environment details 🔧</li>
</ul>
<p>We'll investigate and get back to you soon!</p>
<p><em>Best regards,<br>Your GitHub Maintainer Bot 🤖</em></p>"""

def format_email_response(content: str, sender_name: str = "") -> str:
    """Format standard email response structure"""
    greeting = f"<p>Hello {sender_name},</p>" if sender_name else "<p>Hello,</p>"
    
    return f"""{greeting}
{content}
<p><em>Best regards,<br>GitHub Maintainer Bot 🤖</em></p>"""

def detect_duplicate_issue(issue_body: str, faq_knowledge: dict) -> dict:
    """Enhanced duplicate detection for bug reports"""
    issue_lower = issue_body.lower()
    
    # Extract key technical indicators
    error_keywords = [
        'error', 'exception', 'traceback', 'stack trace', 'failed', 'crash',
        'bug', 'broken', 'not working', 'issue', 'problem', 'TypeError',
        'ValueError', 'AttributeError', 'ImportError', 'KeyError'
    ]
    
    # Extract potential file names and functions
    import re
    file_patterns = re.findall(r'([a-zA-Z0-9_./\-]+\.[a-zA-Z]{2,4})', issue_body)
    function_patterns = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*\(\))', issue_body)
    
    # Score similarity with existing issues
    best_match = None
    highest_score = 0
    
    for faq_key, faq_data in faq_knowledge.items():
        score = 0
        stored_issue = faq_data.get('question', '').lower()
        
        # Check for common error keywords
        common_errors = sum(1 for keyword in error_keywords if keyword in issue_lower and keyword in stored_issue)
        score += common_errors * 2
        
        # Check for common file patterns
        stored_files = re.findall(r'([a-zA-Z0-9_./\-]+\.[a-zA-Z]{2,4})', faq_data.get('question', ''))
        common_files = len(set(file_patterns) & set(stored_files))
        score += common_files * 3
        
        # Check for function patterns
        stored_functions = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*\(\))', faq_data.get('question', ''))
        common_functions = len(set(function_patterns) & set(stored_functions))
        score += common_functions * 2
        
        # Basic word overlap (for general similarity)
        issue_words = set(issue_lower.split())
        stored_words = set(stored_issue.split())
        common_words = len(issue_words & stored_words)
        if len(issue_words) > 0:
            word_similarity = common_words / len(issue_words)
            score += word_similarity * 1
        
        if score > highest_score and score >= 3:  # Minimum threshold for duplicate
            highest_score = score
            best_match = {
                'faq_key': faq_key,
                'similarity_score': score,
                'original_issue': faq_data.get('question', '')[:150] + '...',
                'count': faq_data.get('count', 1)
            }
    
    return best_match

def group_duplicate_response(sender_name: str, duplicate_info: dict, repo_name: str) -> str:
    """Generate response for duplicate bug reports"""
    return f"""<p>Hello {sender_name},</p>
<p>Thank you for reporting this issue! This appears similar to a previous report we've received.</p>
<p><strong>Similar Issue Found:</strong></p>
<blockquote>
<p>{duplicate_info['original_issue']}</p>
</blockquote>
<p>This type of issue has been reported <strong>{duplicate_info['count']} time(s)</strong> before. We're actively investigating this pattern.</p>
<p>To help us resolve this more effectively:</p>
<ul>
<li>Please check if your environment matches the previous reports</li>
<li>Add any additional details that might be unique to your case</li>
<li>Let us know if you've found any workarounds</li>
</ul>
<p>We'll consolidate the information from all similar reports to provide a comprehensive solution.</p>
<p><em>Best regards,<br>GitHub Maintainer Bot 🤖</em></p>"""

def extract_sender_name(email_from: str) -> str:
    """Extract sender name from email address"""
    # Try to get name from "Name <email>" format
    match = re.match(r'^([^<]+)<', email_from)
    if match:
        return match.group(1).strip()
    
    # Fallback to username from email
    if '@' in email_from:
        return email_from.split('@')[0]
    
    return email_from
