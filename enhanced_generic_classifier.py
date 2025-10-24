#!/usr/bin/env python3
"""
Enhanced Generic Repository Classifier with Advanced Rate Limit Handling
Optimized for large organizations like aws-samples (7.6k+ repositories)
"""

import json
import boto3
import time
import requests
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from generic_classifier import GenericRepositoryClassifier

class EnhancedGenericRepositoryClassifier(GenericRepositoryClassifier):
    def __init__(self, org_name: str):
        super().__init__(org_name)
        self.rate_limit_delay = 1  # Start with 1 second delay
        self.max_retries = 3
        self.github_token = None  # Add GitHub token support for higher rate limits
        
    def get_readme_description_with_retry(self, repo: Dict) -> str:
        """Get README description with rate limit handling"""
        for attempt in range(self.max_retries):
            try:
                url = f"https://api.github.com/repos/{repo['full_name']}/readme"
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 403:  # Rate limit
                    print(f"⚠️  Rate limit hit, waiting {self.rate_limit_delay * (attempt + 1)} seconds...")
                    time.sleep(self.rate_limit_delay * (attempt + 1))
                    continue
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

    def classify_repository_with_retry(self, repo: Dict) -> Optional[Dict]:
        """Classify repository with enhanced error handling"""
        for attempt in range(self.max_retries):
            try:
                classification = {
                    # Basic Info
                    "repository": repo["full_name"],
                    "url": repo["html_url"],
                    "description": self.get_description(repo),
                    "created_date": repo.get("created_at", ""),
                    "last_modified": repo["updated_at"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    
                    # Business Classification
                    "solution_type": self.get_solution_type(repo),
                    "competency": self.get_competency(repo),
                    "customer_problems": self.get_customer_problems(repo),
                    "solution_marketing": self.get_solution_marketing(repo),
                    
                    # Technical Classification
                    "deployment_tools": self.get_deployment_tools(repo["name"]),
                    "deployment_level": self.get_deployment_level(repo["name"]),
                    "deployment_readiness": self.get_deployment_readiness(repo),
                    "primary_language": repo["language"] or "Multiple",
                    "secondary_language": self.get_secondary_language(repo),
                    "framework": self.get_framework(repo),
                    "aws_services": self.get_aws_services(self.get_description(repo)),
                    
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
                    "genai_agentic": self.is_genai_agentic(repo),
                    
                    # Metadata
                    "topics": ", ".join(repo.get("topics", [])),
                    "classification_method": f"Enhanced Generic S3-Based Analysis (Attempt {attempt + 1})",
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

    def get_description(self, repo: Dict) -> str:
        """Get description with enhanced README fallback"""
        desc = repo.get("description")
        if not desc:
            desc = self.get_readme_description_with_retry(repo)
        return desc or ""

    def save_checkpoint_with_retry(self, checkpoint: Dict) -> None:
        """Save checkpoint with retry logic"""
        for attempt in range(self.max_retries):
            try:
                checkpoint["last_run"] = datetime.now().isoformat()
                
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=self.checkpoint_key,
                    Body=json.dumps(checkpoint, indent=2),
                    ContentType='application/json'
                )
                return
            except Exception as e:
                print(f"⚠️  Checkpoint save attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"❌ Failed to save checkpoint after {self.max_retries} attempts")

    def run_enhanced_classification(self, batch_size: int = 5) -> None:
        """Run classification with enhanced error handling for large datasets"""
        print("🚀 ENHANCED GENERIC REPOSITORY CLASSIFIER")
        print("=" * 60)
        print(f"🎯 Optimized for large organizations like {self.org_name}")
        
        # Load master index and checkpoint
        repos = self.load_master_index()
        if not repos:
            repos = self.fetch_all_repos()
        
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
        print(f"📦 Batch size: {batch_size} (optimized for large datasets)")
        
        # Process repositories in smaller batches for large datasets
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
                
                # Add small delay to avoid rate limits
                if processed_in_session > 0 and processed_in_session % 10 == 0:
                    print("⏸️  Brief pause to avoid rate limits...")
                    time.sleep(self.rate_limit_delay)
                
                classification = self.classify_repository_with_retry(repo)
                if classification:
                    print(f"✅ {repo_full_name} - {classification['solution_type']}")
                    completed_repos.add(repo_full_name)
                    checkpoint["total_processed"] += 1
                else:
                    print(f"❌ Failed to classify {repo_full_name}")
                    failed_repos[repo_full_name] = datetime.now().isoformat()
                
                processed_in_session += 1
                
                # Update checkpoint more frequently for large datasets
                checkpoint["current_index"] = i + j + 1
                checkpoint["completed_repos"] = list(completed_repos)
                checkpoint["failed_repos"] = failed_repos
            
            # Save checkpoint after each batch
            self.save_checkpoint_with_retry(checkpoint)
            
            batch_time = time.time() - batch_start_time
            print(f"💾 Batch checkpoint saved - Progress: {len(completed_repos)}/{len(repos)} ({len(completed_repos)/len(repos)*100:.1f}%)")
            print(f"⏱️  Batch processing time: {batch_time:.1f}s")
            
            # Milestone celebrations for large datasets
            if len(completed_repos) > 0 and len(completed_repos) % 1000 == 0:
                print(f"\n🎯 Milestone: {len(completed_repos)} repositories processed!")
                print(f"📈 Success rate: {len(completed_repos)/(len(completed_repos)+len(failed_repos))*100:.1f}%")
        
        print(f"\n✅ Classification completed!")
        print(f"📊 Total processed: {len(completed_repos)}")
        print(f"❌ Total failed: {len(failed_repos)}")
        print(f"📈 Success rate: {len(completed_repos)/(len(completed_repos)+len(failed_repos))*100:.1f}%")
        print(f"🔗 Bucket: https://{self.bucket_name}.s3.amazonaws.com/")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Generic GitHub Repository Classifier')
    parser.add_argument('org_name', help='GitHub organization name (e.g., aws-samples, microsoft, google)')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing (default: 5 for large orgs)')
    parser.add_argument('--github-token', help='GitHub personal access token for higher rate limits')
    
    args = parser.parse_args()
    
    classifier = EnhancedGenericRepositoryClassifier(args.org_name)
    if args.github_token:
        classifier.github_token = args.github_token
        print("🔑 Using GitHub token for higher rate limits")
    
    classifier.run_enhanced_classification(args.batch_size)

if __name__ == "__main__":
    main()
