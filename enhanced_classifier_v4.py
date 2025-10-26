#!/usr/bin/env python3
"""
Enhanced Classifier V4 - Bug fixes for None handling and robust error recovery
Fixes: 'NoneType' object has no attribute 'strip' and other None-related errors
"""

import json
import boto3
import time
import requests
import re
import sys
import argparse
import base64
from datetime import datetime
from typing import Dict, List, Optional, Set
from enhanced_classifier_v3 import EnhancedClassifierV3

class EnhancedClassifierV4(EnhancedClassifierV3):
    def __init__(self, org_name: str):
        super().__init__(org_name)

    def get_description_enhanced(self, repo: Dict) -> str:
        """Enhanced description with README fallback - FIXED None handling"""
        try:
            # 1. GitHub description - FIXED: Handle None properly
            desc = repo.get('description') or ''
            if isinstance(desc, str):
                desc = desc.strip()
                if desc and len(desc) > 10:
                    return desc
            
            # 2. README first paragraph
            readme = self.get_readme_content_cached(repo)
            if readme and isinstance(readme, str):
                # Extract first meaningful paragraph
                lines = readme.split('\n')
                desc_lines = []
                
                for line in lines:
                    if not isinstance(line, str):
                        continue
                    line = line.strip()
                    # Skip headers, images, badges
                    if (line and 
                        not line.startswith('#') and 
                        not line.startswith('!') and
                        not line.startswith('[') and
                        not line.startswith('[![') and
                        len(line) > 20):
                        desc_lines.append(line)
                        if len(' '.join(desc_lines)) > 200:
                            break
                        if len(desc_lines) >= 2:
                            break
                
                if desc_lines:
                    return ' '.join(desc_lines)[:300]
            
            # 3. Generate from repository name - FIXED: Handle None repo name
            repo_name = repo.get('name') or 'unknown'
            if isinstance(repo_name, str):
                repo_name = repo_name.replace('-', ' ').replace('_', ' ')
                return f"AWS solution for {repo_name}"
            else:
                return "AWS solution"
                
        except Exception as e:
            print(f"      🐛 Description enhancement error: {e}")
            # Fallback to basic description
            basic_desc = repo.get('description') or ''
            if isinstance(basic_desc, str) and basic_desc.strip():
                return basic_desc.strip()
            else:
                repo_name = repo.get('name') or 'unknown'
                return f"AWS solution for {repo_name}"

    def extract_aws_services_from_text(self, text: str) -> Set[str]:
        """Extract AWS services from text - FIXED None handling"""
        if not text or not isinstance(text, str):
            return set()
        
        try:
            text_lower = text.lower()
            services = set()
            
            for keyword, service in self.aws_services_map.items():
                # Look for keyword with word boundaries
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    services.add(service)
            
            return services
        except Exception as e:
            print(f"      🐛 AWS services extraction error: {e}")
            return set()

    def get_readme_content_cached(self, repo: Dict) -> str:
        """Get README content with caching - FIXED None handling"""
        if not repo or not isinstance(repo, dict):
            return ""
            
        repo_name = repo.get('full_name')
        if not repo_name or not isinstance(repo_name, str):
            return ""
        
        if repo_name in self.readme_cache:
            return self.readme_cache[repo_name]
        
        for attempt in range(self.max_retries):
            try:
                url = f"https://api.github.com/repos/{repo_name}/readme"
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if self.handle_rate_limit(response):
                    continue
                    
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data and 'content' in response_data:
                        content = base64.b64decode(response_data['content']).decode('utf-8', errors='ignore')
                        # Cache first 3000 chars for performance
                        self.readme_cache[repo_name] = content[:3000] if content else ""
                        return self.readme_cache[repo_name]
                else:
                    break
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"      🐛 README fetch error for {repo_name}: {e}")
                time.sleep(1)
        
        self.readme_cache[repo_name] = ""
        return ""

    def get_repo_topics_cached(self, repo: Dict) -> List[str]:
        """Get repository topics - FIXED None handling"""
        if not repo or not isinstance(repo, dict):
            return []
            
        repo_name = repo.get('full_name')
        if not repo_name or not isinstance(repo_name, str):
            return []
        
        if repo_name in self.topics_cache:
            return self.topics_cache[repo_name]
        
        # First try from repo data
        topics = repo.get('topics', [])
        if topics and isinstance(topics, list):
            self.topics_cache[repo_name] = topics
            return topics
        
        # Fallback to API call if needed
        for attempt in range(self.max_retries):
            try:
                url = f"https://api.github.com/repos/{repo_name}/topics"
                headers = {'Accept': 'application/vnd.github.mercy-preview+json'}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if self.handle_rate_limit(response):
                    continue
                    
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data and 'names' in response_data:
                        topics = response_data.get('names', [])
                        if isinstance(topics, list):
                            self.topics_cache[repo_name] = topics
                            return topics
                else:
                    break
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"      🐛 Topics fetch error for {repo_name}: {e}")
                time.sleep(1)
        
        self.topics_cache[repo_name] = []
        return []

    def get_aws_services_enhanced(self, repo: Dict) -> str:
        """Enhanced AWS services detection - FIXED None handling"""
        if not repo or not isinstance(repo, dict):
            return 'General AWS'
            
        try:
            services = set()
            sources = []
            
            # Source 1: Repository description
            desc = repo.get('description') or ''
            if isinstance(desc, str) and desc.strip():
                desc_services = self.extract_aws_services_from_text(desc)
                services.update(desc_services)
                if desc_services:
                    sources.append('description')
            
            # Source 2: README content
            readme = self.get_readme_content_cached(repo)
            if readme and isinstance(readme, str):
                readme_services = self.extract_aws_services_from_text(readme)
                services.update(readme_services)
                if readme_services:
                    sources.append('readme')
            
            # Source 3: GitHub topics
            topics = self.get_repo_topics_cached(repo)
            if topics and isinstance(topics, list):
                topic_services = self.map_topics_to_services(topics)
                services.update(topic_services)
                if topic_services:
                    sources.append('topics')
            
            # Return top 5 services
            service_list = sorted(list(services))[:5]
            
            if service_list:
                return ', '.join(service_list)
            else:
                return 'General AWS'
                
        except Exception as e:
            print(f"      🐛 AWS services detection error: {e}")
            return 'General AWS'

    def map_topics_to_services(self, topics: List[str]) -> Set[str]:
        """Map GitHub topics to AWS services - FIXED None handling"""
        if not topics or not isinstance(topics, list):
            return set()
            
        services = set()
        
        try:
            for topic in topics:
                if not isinstance(topic, str):
                    continue
                    
                topic_lower = topic.lower()
                if topic_lower in self.aws_services_map:
                    services.add(self.aws_services_map[topic_lower])
                # Handle common topic variations
                elif topic_lower in ['serverless', 'aws-lambda']:
                    services.add('Lambda')
                elif topic_lower in ['aws-s3', 'amazon-s3']:
                    services.add('S3')
                elif topic_lower in ['aws-dynamodb']:
                    services.add('DynamoDB')
        except Exception as e:
            print(f"      🐛 Topics mapping error: {e}")
        
        return services

    def classify_repository_enhanced_with_logging(self, repo: Dict) -> Optional[Dict]:
        """Enhanced repository classification - FIXED None handling"""
        if not repo or not isinstance(repo, dict):
            return None
            
        repo_name = repo.get("full_name", "unknown")
        
        try:
            # Get enhanced data with individual error handling and safe defaults
            enhanced_description = "AWS solution"
            enhanced_aws_services = "General AWS"
            topics = []
            
            # Try to get description
            try:
                enhanced_description = self.get_description_enhanced(repo)
            except Exception as e:
                print(f"      ⚠️  Description failed for {repo_name}: {e}")
                desc = repo.get('description') or ''
                if isinstance(desc, str) and desc.strip():
                    enhanced_description = desc.strip()
                else:
                    repo_name_clean = repo.get('name', 'unknown').replace('-', ' ').replace('_', ' ')
                    enhanced_description = f"AWS solution for {repo_name_clean}"
            
            # Try to get AWS services
            try:
                enhanced_aws_services = self.get_aws_services_enhanced(repo)
            except Exception as e:
                print(f"      ⚠️  AWS services detection failed for {repo_name}: {e}")
                enhanced_aws_services = "General AWS"
            
            # Try to get topics
            try:
                topics = self.get_repo_topics_cached(repo)
                if not isinstance(topics, list):
                    topics = []
            except Exception as e:
                print(f"      ⚠️  Topics failed for {repo_name}: {e}")
                topics = repo.get('topics', []) if isinstance(repo.get('topics'), list) else []
            
            # Build classification with safe defaults and None checks
            classification = {
                # Basic Info - with None checks
                "repository": repo.get("full_name", "unknown"),
                "url": repo.get("html_url", ""),
                "description": enhanced_description,
                "created_date": repo.get("created_at", ""),
                "last_modified": repo.get("updated_at", ""),
                "stars": repo.get("stargazers_count", 0) or 0,
                "forks": repo.get("forks_count", 0) or 0,
                
                # Enhanced AWS Services
                "aws_services": enhanced_aws_services,
                "topics": ", ".join(topics) if topics else "",
                
                # Business Classification (using enhanced description)
                "solution_type": self.get_solution_type_enhanced(repo, enhanced_description),
                "competency": self.get_competency_enhanced(enhanced_description, enhanced_aws_services),
                "customer_problems": self.get_customer_problems(repo),
                "solution_marketing": self.get_solution_marketing_enhanced(repo, enhanced_description),
                
                # Technical Classification
                "deployment_tools": self.get_deployment_tools(repo.get("name", "")),
                "deployment_level": self.get_deployment_level(repo.get("name", "")),
                "deployment_readiness": self.get_deployment_readiness(repo),
                "primary_language": repo.get("language") or "Multiple",
                "secondary_language": self.get_secondary_language(repo),
                "framework": self.get_framework(repo),
                
                # Business Value
                "cost_range": self.get_cost_range(repo),
                "setup_time": self.get_setup_time(repo),
                "business_value": self.get_business_value(repo),
                "target_audience": self.get_target_audience(repo),
                "use_case_category": self.get_use_case_category(repo),
                "integration_complexity": self.get_integration_complexity(repo),
                "maintenance_level": self.get_maintenance_level(repo),
                "scalability": self.get_scalability(repo),
                "usp": self.get_usp(repo),
                "freshness_status": self.get_freshness(repo.get("updated_at", "")),
                "days_since_update": self.get_days_since_update(repo.get("updated_at", "")),
                
                # AI/GenAI
                "genai_agentic": self.is_genai_agentic_enhanced(repo, enhanced_description),
                
                # Metadata
                "classification_method": "Enhanced V4 - Bug-Fixed Analysis",
                "classification_timestamp": datetime.now().isoformat()
            }
            
            self.success_count += 1
            return classification
            
        except Exception as e:
            self.log_failed_repository(repo, str(e))
            return None

def main():
    parser = argparse.ArgumentParser(description='Enhanced AWS Repository Classifier V4 - Bug Fixed')
    parser.add_argument('org_name', help='GitHub organization name')
    parser.add_argument('--github-token', help='GitHub personal access token')
    parser.add_argument('--limit', type=int, help='Number of repositories to process')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')
    parser.add_argument('--retry-failed', action='store_true', help='Process only failed repositories from previous runs')
    
    args = parser.parse_args()
    
    classifier = EnhancedClassifierV4(args.org_name)
    if args.github_token:
        classifier.github_token = args.github_token
        print("🔑 Using GitHub token for higher rate limits")
    
    if args.retry_failed:
        classifier.process_failed_repositories_only()
    else:
        classifier.process_all_repositories_with_logging(args.limit, args.batch_size)

if __name__ == "__main__":
    main()
