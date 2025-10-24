#!/usr/bin/env python3
"""
Smart Rate Limit Classifier - Handles GitHub rate limits intelligently
"""

import json
import boto3
import time
import requests
import sys
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional
from enhanced_generic_classifier import EnhancedGenericRepositoryClassifier

class SmartRateLimitClassifier(EnhancedGenericRepositoryClassifier):
    def __init__(self, org_name: str):
        super().__init__(org_name)
        
    def handle_rate_limit(self, response):
        """Smart rate limit handling with proper wait times"""
        if response.status_code == 403:
            rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
            
            if rate_limit_remaining == 0:
                # Calculate wait time until reset
                current_time = int(time.time())
                wait_time = max(rate_limit_reset - current_time, 0) + 60  # Add 1 minute buffer
                
                print(f"🚫 Rate limit exceeded!")
                print(f"⏰ Reset time: {datetime.fromtimestamp(rate_limit_reset)}")
                print(f"⏳ Waiting {wait_time} seconds ({wait_time//60:.1f} minutes)...")
                
                # Save checkpoint before waiting
                print("💾 Saving checkpoint before rate limit wait...")
                
                # Wait for rate limit reset
                time.sleep(wait_time)
                print("✅ Rate limit should be reset, resuming...")
                return True
        return False

    def classify_repository_with_smart_retry(self, repo: Dict) -> Optional[Dict]:
        """Classify repository with smart rate limit handling"""
        for attempt in range(self.max_retries):
            try:
                # Check if we need README (this uses GitHub API)
                desc = repo.get("description")
                if not desc:
                    # Try to get README with rate limit handling
                    readme_desc = self.get_readme_with_smart_retry(repo)
                    desc = readme_desc or ""
                else:
                    desc = desc or ""
                
                classification = {
                    # Basic Info
                    "repository": repo["full_name"],
                    "url": repo["html_url"],
                    "description": desc,
                    "created_date": repo.get("created_at", ""),
                    "last_modified": repo["updated_at"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    
                    # Business Classification
                    "solution_type": self.get_solution_type_safe(repo, desc),
                    "competency": self.get_competency_safe(desc),
                    "customer_problems": self.get_customer_problems_safe(desc),
                    "solution_marketing": self.get_solution_marketing_safe(repo, desc),
                    
                    # Technical Classification
                    "deployment_tools": self.get_deployment_tools(repo["name"]),
                    "deployment_level": self.get_deployment_level(repo["name"]),
                    "deployment_readiness": self.get_deployment_readiness(repo),
                    "primary_language": repo["language"] or "Multiple",
                    "secondary_language": self.get_secondary_language(repo),
                    "framework": self.get_framework(repo),
                    "aws_services": self.get_aws_services(desc),
                    
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
                    "freshness_status": self.get_freshness(repo["updated_at"]),
                    "days_since_update": self.get_days_since_update(repo["updated_at"]),
                    
                    # AI/GenAI
                    "genai_agentic": self.is_genai_agentic_safe(repo, desc),
                    
                    # Metadata
                    "topics": ", ".join(repo.get("topics", [])),
                    "classification_method": f"Smart Rate Limit Analysis (Attempt {attempt + 1})",
                    "classification_timestamp": datetime.now().isoformat()
                }
                return classification
            except Exception as e:
                print(f"⚠️  Classification attempt {attempt + 1} failed for {repo['full_name']}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"❌ Failed to classify {repo['full_name']} after {self.max_retries} attempts")
                    return None

    def get_readme_with_smart_retry(self, repo: Dict) -> str:
        """Get README with smart rate limit handling"""
        for attempt in range(self.max_retries):
            try:
                url = f"https://api.github.com/repos/{repo['full_name']}/readme"
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if self.handle_rate_limit(response):
                    continue  # Rate limit handled, retry
                elif response.status_code == 200:
                    import base64
                    content = base64.b64decode(response.json()['content']).decode('utf-8')
                    # Extract first 2 paragraphs (up to 300 chars)
                    lines = content.split('\n')
                    desc_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('!'):
                            desc_lines.append(line)
                            if len(' '.join(desc_lines)) > 300:
                                break
                            if len(desc_lines) >= 2:
                                break
                    return ' '.join(desc_lines)[:300]
                else:
                    break  # Other errors, don't retry
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"⚠️  Failed to get README for {repo['full_name']}: {e}")
                time.sleep(1)
        return ""

    # Safe classification methods that don't call GitHub API
    def get_solution_type_safe(self, repo: Dict, desc: str) -> str:
        """Safe solution type classification"""
        desc_lower = desc.lower()
        topics = " ".join(repo.get("topics", [])).lower()
        
        if any(word in desc_lower for word in ["ai", "ml", "machine learning", "neural", "deep learning", "llm", "genai", "bedrock"]):
            return "Innovation Catalysts"
        elif any(word in desc_lower for word in ["security", "compliance", "governance", "audit", "policy"]):
            return "Compliance Accelerators"
        elif any(word in desc_lower for word in ["tool", "utility", "helper", "simple", "quick"]):
            return "Quick Wins"
        else:
            return "Foundation Builders"

    def get_competency_safe(self, desc: str) -> str:
        """Safe competency classification"""
        desc_lower = desc.lower()
        
        if any(word in desc_lower for word in ["analytics", "data", "etl", "warehouse"]):
            return "Analytics"
        elif any(word in desc_lower for word in ["security", "iam", "encryption"]):
            return "Security"
        elif any(word in desc_lower for word in ["devops", "cicd", "pipeline", "deploy"]):
            return "DevOps"
        elif any(word in desc_lower for word in ["ai", "ml", "machine learning"]):
            return "AI/ML"
        else:
            return "General"

    def get_customer_problems_safe(self, desc: str) -> str:
        """Safe customer problems classification"""
        desc_lower = desc.lower()
        
        if any(word in desc_lower for word in ["complex", "difficult", "challenge"]):
            return "Complex Implementation"
        elif any(word in desc_lower for word in ["time", "quick", "fast"]):
            return "Time to Market"
        else:
            return "Development Efficiency"

    def get_solution_marketing_safe(self, repo: Dict, desc: str) -> str:
        """Safe solution marketing classification"""
        repo_name = repo.get("name", "").lower()
        desc_lower = desc.lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{repo_name} {desc_lower} {topics}"
        
        if any(word in text for word in ["setup", "bootstrap", "install", "getting-started", "quickstart"]):
            return "setup"
        elif any(word in text for word in ["landing-zone", "account-setup", "multi-account", "organization"]):
            return "landingzone"
        elif any(word in text for word in ["starter", "template", "boilerplate", "scaffold"]):
            return "starter"
        elif any(word in text for word in ["optim", "performance", "cost", "efficiency"]):
            return "optimise"
        elif any(word in text for word in ["compliance", "security", "governance", "audit"]):
            return "compliance"
        elif any(word in text for word in ["improve", "enhance", "upgrade", "migrate"]):
            return "improvement"
        elif any(word in text for word in ["monitor", "observ", "dashboard", "metric", "log"]):
            return "visibility"
        elif any(word in text for word in ["foundation", "infrastructure", "core", "base"]):
            return "foundation"
        else:
            return "foundation"

    def is_genai_agentic_safe(self, repo: Dict, desc: str) -> str:
        """Safe GenAI detection"""
        desc_lower = desc.lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{desc_lower} {topics}"
        
        if any(word in text for word in ["agent", "llm", "genai", "bedrock", "anthropic", "openai"]):
            return "Yes"
        else:
            return "No"

    def run_smart_classification(self, batch_size: int = 5) -> None:
        """Run classification with smart rate limit handling"""
        print("🧠 SMART RATE LIMIT REPOSITORY CLASSIFIER")
        print("=" * 60)
        print(f"🎯 Processing {self.org_name} with intelligent rate limit handling")
        
        # Load master index and checkpoint
        repos = self.load_master_index()
        checkpoint = self.load_checkpoint()
        
        if not repos:
            print("❌ No repositories found")
            return
        
        start_index = checkpoint["current_index"]
        completed_repos = set(checkpoint["completed_repos"])
        failed_repos = checkpoint.get("failed_repos", {})
        
        print(f"📊 Total repositories: {len(repos)}")
        print(f"🔄 Resuming from index: {start_index}")
        print(f"✅ Already completed: {len(completed_repos)}")
        print(f"❌ Previously failed: {len(failed_repos)}")
        print(f"📦 Batch size: {batch_size}")
        
        # Process repositories
        processed_in_session = 0
        
        for i in range(start_index, len(repos), batch_size):
            batch = repos[i:i+batch_size]
            batch_start_time = time.time()
            
            print(f"\n📦 Processing batch {i//batch_size + 1} (repos {i+1}-{min(i+batch_size, len(repos))})")
            
            for j, repo in enumerate(batch):
                repo_full_name = repo["full_name"]
                
                if repo_full_name in completed_repos:
                    print(f"⏭️  Skipping {repo_full_name} (already completed)")
                    continue
                
                if repo_full_name in failed_repos:
                    print(f"⏭️  Skipping {repo_full_name} (previously failed)")
                    continue
                
                print(f"🔍 Processing {repo_full_name} ({j+1}/{len(batch)})...")
                
                classification = self.classify_repository_with_smart_retry(repo)
                if classification:
                    print(f"✅ {repo_full_name} - {classification['solution_type']}")
                    completed_repos.add(repo_full_name)
                    checkpoint["total_processed"] += 1
                else:
                    print(f"❌ Failed to classify {repo_full_name}")
                    failed_repos[repo_full_name] = datetime.now().isoformat()
                
                processed_in_session += 1
                
                # Update checkpoint
                checkpoint["current_index"] = i + j + 1
                checkpoint["completed_repos"] = list(completed_repos)
                checkpoint["failed_repos"] = failed_repos
            
            # Save checkpoint after each batch
            self.save_checkpoint_with_retry(checkpoint)
            
            batch_time = time.time() - batch_start_time
            print(f"💾 Checkpoint saved - Progress: {len(completed_repos)}/{len(repos)} ({len(completed_repos)/len(repos)*100:.1f}%)")
            print(f"⏱️  Batch time: {batch_time:.1f}s")
            
            # Milestone celebrations
            if len(completed_repos) > 0 and len(completed_repos) % 1000 == 0:
                print(f"\n🎯 Milestone: {len(completed_repos)} repositories processed!")
        
        print(f"\n✅ Classification completed!")
        print(f"📊 Total processed: {len(completed_repos)}")
        print(f"❌ Total failed: {len(failed_repos)}")
        print(f"🔗 Bucket: https://{self.bucket_name}.s3.amazonaws.com/")

def main():
    parser = argparse.ArgumentParser(description='Smart Rate Limit GitHub Repository Classifier')
    parser.add_argument('org_name', help='GitHub organization name (e.g., aws-samples)')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing (default: 5)')
    parser.add_argument('--github-token', help='GitHub personal access token')
    
    args = parser.parse_args()
    
    classifier = SmartRateLimitClassifier(args.org_name)
    if args.github_token:
        classifier.github_token = args.github_token
        print("🔑 Using GitHub token for higher rate limits")
    
    classifier.run_smart_classification(args.batch_size)

if __name__ == "__main__":
    main()
