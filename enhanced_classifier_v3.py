#!/usr/bin/env python3
"""
Enhanced Classifier V3 - With comprehensive error logging and retry mechanism
Logs all failed repositories for later retry processing
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
from enhanced_classifier_v2 import EnhancedClassifierV2

class EnhancedClassifierV3(EnhancedClassifierV2):
    def __init__(self, org_name: str):
        super().__init__(org_name)
        self.failed_repos = []
        self.failed_log_key = 'logs/failed_repositories.json'
        self.processing_log_key = 'logs/processing_log.txt'
        self.success_count = 0
        self.failure_count = 0
        
    def log_processing_event(self, message: str):
        """Log processing events to S3"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            # Append to existing log
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.processing_log_key)
                existing_log = response['Body'].read().decode('utf-8')
            except:
                existing_log = ""
            
            updated_log = existing_log + log_entry
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.processing_log_key,
                Body=updated_log,
                ContentType='text/plain'
            )
        except Exception as e:
            print(f"⚠️  Failed to log to S3: {e}")

    def log_failed_repository(self, repo: Dict, error: str):
        """Log failed repository with error details"""
        failed_entry = {
            "repository": repo.get("full_name", "unknown"),
            "url": repo.get("html_url", ""),
            "stars": repo.get("stargazers_count", 0),
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "retry_count": 0
        }
        
        self.failed_repos.append(failed_entry)
        self.failure_count += 1
        
        # Log to console
        print(f"    ❌ FAILED: {repo.get('full_name', 'unknown')} - {error}")
        
        # Save failed repos to S3 every 10 failures
        if len(self.failed_repos) % 10 == 0:
            self.save_failed_repos_log()

    def save_failed_repos_log(self):
        """Save failed repositories log to S3"""
        if not self.failed_repos:
            return
            
        try:
            # Load existing failed repos if any
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.failed_log_key)
                existing_failed = json.loads(response['Body'].read().decode('utf-8'))
            except:
                existing_failed = []
            
            # Merge with current failures
            all_failed = existing_failed + self.failed_repos
            
            # Save to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.failed_log_key,
                Body=json.dumps(all_failed, indent=2),
                ContentType='application/json'
            )
            
            print(f"💾 Saved {len(all_failed)} failed repositories to S3")
            self.failed_repos = []  # Clear current batch
            
        except Exception as e:
            print(f"⚠️  Failed to save failed repos log: {e}")

    def classify_repository_enhanced_with_logging(self, repo: Dict) -> Optional[Dict]:
        """Enhanced repository classification with comprehensive error logging"""
        repo_name = repo.get("full_name", "unknown")
        
        try:
            # Get enhanced data with individual error handling
            enhanced_description = ""
            enhanced_aws_services = "General AWS"
            topics = []
            
            # Try to get description
            try:
                enhanced_description = self.get_description_enhanced(repo)
            except Exception as e:
                print(f"      ⚠️  Description failed for {repo_name}: {e}")
                enhanced_description = repo.get('description', '') or f"AWS solution for {repo.get('name', '').replace('-', ' ')}"
            
            # Try to get AWS services
            try:
                enhanced_aws_services = self.get_aws_services_enhanced(repo)
            except Exception as e:
                print(f"      ⚠️  AWS services detection failed for {repo_name}: {e}")
                enhanced_aws_services = "General AWS"
            
            # Try to get topics
            try:
                topics = self.get_repo_topics_cached(repo)
            except Exception as e:
                print(f"      ⚠️  Topics failed for {repo_name}: {e}")
                topics = repo.get('topics', [])
            
            # Build classification with safe defaults
            classification = {
                # Basic Info
                "repository": repo["full_name"],
                "url": repo["html_url"],
                "description": enhanced_description,
                "created_date": repo.get("created_at", ""),
                "last_modified": repo["updated_at"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                
                # Enhanced AWS Services
                "aws_services": enhanced_aws_services,
                "topics": ", ".join(topics),
                
                # Business Classification (using enhanced description)
                "solution_type": self.get_solution_type_enhanced(repo, enhanced_description),
                "competency": self.get_competency_enhanced(enhanced_description, enhanced_aws_services),
                "customer_problems": self.get_customer_problems(repo),
                "solution_marketing": self.get_solution_marketing_enhanced(repo, enhanced_description),
                
                # Technical Classification
                "deployment_tools": self.get_deployment_tools(repo["name"]),
                "deployment_level": self.get_deployment_level(repo["name"]),
                "deployment_readiness": self.get_deployment_readiness(repo),
                "primary_language": repo["language"] or "Multiple",
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
                "freshness_status": self.get_freshness(repo["updated_at"]),
                "days_since_update": self.get_days_since_update(repo["updated_at"]),
                
                # AI/GenAI
                "genai_agentic": self.is_genai_agentic_enhanced(repo, enhanced_description),
                
                # Metadata
                "classification_method": "Enhanced V3 - Error-Resilient Analysis",
                "classification_timestamp": datetime.now().isoformat()
            }
            
            self.success_count += 1
            return classification
            
        except Exception as e:
            self.log_failed_repository(repo, str(e))
            return None

    def process_all_repositories_with_logging(self, limit: int = None, batch_size: int = 5):
        """Process all repositories with comprehensive logging and error handling"""
        print(f"🚀 Starting Enhanced Classification V3 with Error Logging")
        
        # Load all repositories
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.master_index_key)
            all_repos = json.loads(response['Body'].read())['repositories']
        except Exception as e:
            print(f"❌ Failed to load repositories: {e}")
            return
        
        # Apply limit if specified
        if limit:
            all_repos = all_repos[:limit]
        
        # Sort by stars for better progress visibility
        all_repos = sorted(all_repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)
        
        print(f"📊 Processing {len(all_repos)} repositories")
        print(f"⭐ Star range: {all_repos[0].get('stargazers_count', 0)} to {all_repos[-1].get('stargazers_count', 0)}")
        
        self.log_processing_event(f"Started processing {len(all_repos)} repositories")
        
        # Process in batches
        results = []
        start_time = time.time()
        
        for i in range(0, len(all_repos), batch_size):
            batch = all_repos[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(all_repos) - 1) // batch_size + 1
            
            print(f"\n📦 Batch {batch_num}/{total_batches} (repos {i+1}-{min(i+batch_size, len(all_repos))})")
            
            batch_start = time.time()
            batch_successes = 0
            
            for repo in batch:
                repo_name = repo['full_name']
                stars = repo.get('stargazers_count', 0)
                
                print(f"  🔍 {repo_name} (⭐{stars})")
                
                classification = self.classify_repository_enhanced_with_logging(repo)
                if classification:
                    results.append(classification)
                    batch_successes += 1
                    print(f"    ✅ AWS: {classification['aws_services']}")
                    print(f"    📝 Desc: {classification['description'][:80]}...")
            
            # Batch summary
            batch_time = time.time() - batch_start
            elapsed_time = time.time() - start_time
            avg_time_per_repo = elapsed_time / (i + len(batch))
            estimated_remaining = avg_time_per_repo * (len(all_repos) - i - len(batch))
            
            print(f"  📊 Batch {batch_num}: {batch_successes}/{len(batch)} successful ({batch_time:.1f}s)")
            print(f"  📈 Overall: {self.success_count}/{i+len(batch)} successful, {self.failure_count} failed")
            print(f"  ⏱️  Estimated remaining: {estimated_remaining/60:.1f} minutes")
            
            # Save progress every batch
            if results:
                self.save_enhanced_results(results, f"enhanced_v3_progress_batch{batch_num}")
            
            # Save failed repos log
            if self.failed_repos:
                self.save_failed_repos_log()
            
            # Log progress
            self.log_processing_event(f"Completed batch {batch_num}/{total_batches}: {batch_successes}/{len(batch)} successful")
            
            # Rate limiting delay
            time.sleep(1)
        
        # Final summary
        total_time = time.time() - start_time
        success_rate = (self.success_count / len(all_repos)) * 100
        
        print(f"\n🎉 Processing Complete!")
        print(f"✅ Successful: {self.success_count}/{len(all_repos)} ({success_rate:.1f}%)")
        print(f"❌ Failed: {self.failure_count}/{len(all_repos)} ({100-success_rate:.1f}%)")
        print(f"⏱️  Total time: {total_time/60:.1f} minutes")
        
        # Save final results
        if results:
            self.save_enhanced_results(results, f"enhanced_v3_final_{len(results)}_repos")
        
        # Save final failed repos log
        if self.failed_repos:
            self.save_failed_repos_log()
        
        self.log_processing_event(f"Processing complete: {self.success_count} successful, {self.failure_count} failed")
        
        # Show failed repos summary
        if self.failure_count > 0:
            print(f"\n📋 Failed repositories logged to: s3://{self.bucket_name}/{self.failed_log_key}")
            print(f"🔄 Run retry processing later to fix failed repositories")

    def process_failed_repositories_only(self):
        """Process only the failed repositories from previous runs"""
        print(f"🔄 Processing Failed Repositories Only")
        
        try:
            # Load failed repositories
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.failed_log_key)
            failed_repos_data = json.loads(response['Body'].read().decode('utf-8'))
            
            print(f"📋 Found {len(failed_repos_data)} failed repositories to retry")
            
            # Convert failed repo data back to repo format for processing
            retry_repos = []
            for failed_entry in failed_repos_data:
                # We need to fetch the full repo data again
                repo_name = failed_entry['repository']
                print(f"🔍 Fetching repo data for: {repo_name}")
                
                # Fetch repo data from GitHub API
                url = f"https://api.github.com/repos/{repo_name}"
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        repo_data = response.json()
                        retry_repos.append(repo_data)
                    else:
                        print(f"  ❌ Failed to fetch {repo_name}: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ Error fetching {repo_name}: {e}")
            
            if retry_repos:
                print(f"🚀 Retrying {len(retry_repos)} repositories")
                self.process_all_repositories_with_logging(limit=len(retry_repos), batch_size=3)
            else:
                print("❌ No repositories available for retry")
                
        except Exception as e:
            print(f"❌ Failed to load failed repositories: {e}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced AWS Repository Classifier V3 with Error Logging')
    parser.add_argument('org_name', help='GitHub organization name')
    parser.add_argument('--github-token', help='GitHub personal access token')
    parser.add_argument('--limit', type=int, help='Number of repositories to process')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')
    parser.add_argument('--retry-failed', action='store_true', help='Process only failed repositories from previous runs')
    
    args = parser.parse_args()
    
    classifier = EnhancedClassifierV3(args.org_name)
    if args.github_token:
        classifier.github_token = args.github_token
        print("🔑 Using GitHub token for higher rate limits")
    
    if args.retry_failed:
        classifier.process_failed_repositories_only()
    else:
        classifier.process_all_repositories_with_logging(args.limit, args.batch_size)

if __name__ == "__main__":
    main()
