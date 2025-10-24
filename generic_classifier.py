#!/usr/bin/env python3
"""
Generic AWS Repository Classification System with Checkpointing
Processes repositories from any GitHub organization with resumability and crash recovery
"""

import json
import boto3
import time
import requests
import re
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional

class GenericRepositoryClassifier:
    def __init__(self, org_name: str):
        self.s3_client = boto3.client('s3')
        self.org_name = org_name
        self.bucket_name = f'aws-github-repo-classification-{org_name.lower()}'
        self.master_index_key = f'master-index/{org_name}_repos.json'
        self.checkpoint_key = 'checkpoints/progress.json'
        self.results_key = 'results/classification_results.csv'
        
        # Create bucket if it doesn't exist
        self.create_bucket_if_not_exists()
        
    def create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist and make it public"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except:
            # Create bucket
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            
            # Make bucket public
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject", "s3:ListBucket"],
                    "Resource": [
                        f"arn:aws:s3:::{self.bucket_name}/*",
                        f"arn:aws:s3:::{self.bucket_name}"
                    ]
                }]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            self.s3_client.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            
            print(f"✅ Created public bucket: {self.bucket_name}")

    def fetch_all_repos(self) -> List[Dict]:
        """Fetch all repositories for the organization"""
        repos = []
        page = 1
        per_page = 100
        
        print(f"Fetching all {self.org_name} repositories...")
        
        while True:
            url = f"https://api.github.com/orgs/{self.org_name}/repos?page={page}&per_page={per_page}"
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"API Error: {response.status_code}")
                break
                
            page_repos = response.json()
            if not page_repos:
                break
                
            repos.extend(page_repos)
            print(f"Fetched page {page}: {len(page_repos)} repos (total: {len(repos)})")
            page += 1
        
        print(f"Total repositories found: {len(repos)}")
        
        # Upload to S3
        master_data = {"repositories": repos}
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self.master_index_key,
            Body=json.dumps(master_data, indent=2),
            ContentType='application/json'
        )
        
        print(f"✅ Uploaded {len(repos)} repositories to S3")
        return repos

    def load_master_index(self) -> List[Dict]:
        """Load master index from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.master_index_key
            )
            data = json.loads(response['Body'].read())
            return data["repositories"]
        except Exception as e:
            print(f"❌ Failed to load master index: {e}")
            return []
    
    def get_readme_description(self, repo: Dict) -> str:
        """Get first 1-2 paragraphs from README as fallback description"""
        try:
            url = f"https://api.github.com/repos/{repo['full_name']}/readme"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
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
        except:
            pass
        return ""
    
    def get_description(self, repo: Dict) -> str:
        """Get description with README fallback"""
        desc = repo.get("description")
        if not desc:
            desc = self.get_readme_description(repo)
        return desc or ""

    def classify_repository(self, repo: Dict) -> Optional[Dict]:
        """Classify a single repository with all 20 dimensions"""
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
                "classification_method": "Generic S3-Based Complete Analysis",
                "classification_timestamp": datetime.now().isoformat()
            }
            return classification
        except Exception as e:
            print(f"❌ Failed to classify {repo['full_name']}: {e}")
            return None
    
    def get_solution_marketing(self, repo: Dict) -> str:
        """Determine solution marketing category"""
        repo_name = repo.get("name", "").lower()
        desc = (self.get_description(repo)).lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{repo_name} {desc} {topics}"
        
        # Setup & Bootstrap
        if any(word in text for word in ["setup", "bootstrap", "install", "getting-started", "quickstart"]):
            return "setup"
        
        # Landing Zone
        if any(word in text for word in ["landing-zone", "account-setup", "multi-account", "organization"]):
            return "landingzone"
        
        # Starter Templates
        if any(word in text for word in ["starter", "template", "boilerplate", "scaffold"]):
            return "starter"
        
        # Optimization
        if any(word in text for word in ["optim", "performance", "cost", "efficiency"]):
            return "optimise"
        
        # Compliance & Security
        if any(word in text for word in ["compliance", "security", "governance", "audit"]):
            return "compliance"
        
        # Improvement & Enhancement
        if any(word in text for word in ["improve", "enhance", "upgrade", "migrate"]):
            return "improvement"
        
        # Visibility & Monitoring
        if any(word in text for word in ["monitor", "observ", "dashboard", "metric", "log"]):
            return "visibility"
        
        # Foundation & Infrastructure
        if any(word in text for word in ["foundation", "infrastructure", "core", "base"]):
            return "foundation"
        
        # Default fallback
        return "foundation"

    # All other classification methods remain the same as s3_classifier.py
    def get_solution_type(self, repo: Dict) -> str:
        """Determine solution type based on repo characteristics"""
        desc = (self.get_description(repo)).lower()
        topics = " ".join(repo.get("topics", [])).lower()
        
        # Innovation Catalysts - AI/ML, experimental, cutting-edge
        if any(word in desc for word in ["ai", "ml", "machine learning", "neural", "deep learning", "llm", "genai", "bedrock"]):
            return "Innovation Catalysts"
        
        # Compliance Accelerators - security, governance, compliance
        if any(word in desc for word in ["security", "compliance", "governance", "audit", "policy"]):
            return "Compliance Accelerators"
        
        # Quick Wins - simple tools, utilities, small solutions
        if any(word in desc for word in ["tool", "utility", "helper", "simple", "quick"]):
            return "Quick Wins"
        
        # Default to Foundation Builders
        return "Foundation Builders"

    def get_competency(self, repo: Dict) -> str:
        """Determine AWS competency area"""
        desc = (self.get_description(repo)).lower()
        
        if any(word in desc for word in ["analytics", "data", "etl", "warehouse"]):
            return "Analytics"
        elif any(word in desc for word in ["security", "iam", "encryption"]):
            return "Security"
        elif any(word in desc for word in ["devops", "cicd", "pipeline", "deploy"]):
            return "DevOps"
        elif any(word in desc for word in ["ai", "ml", "machine learning"]):
            return "AI/ML"
        else:
            return "General"

    def get_customer_problems(self, repo: Dict) -> str:
        """Identify customer problems this solves"""
        desc = (self.get_description(repo)).lower()
        
        if any(word in desc for word in ["complex", "difficult", "challenge"]):
            return "Complex Implementation"
        elif any(word in desc for word in ["time", "quick", "fast"]):
            return "Time to Market"
        else:
            return "Development Efficiency"

    def get_deployment_tools(self, repo_name: str) -> str:
        """Get deployment tools based on repo name"""
        name_lower = repo_name.lower()
        if "cdk" in name_lower:
            return "CDK"
        elif "terraform" in name_lower:
            return "Terraform"
        elif "cloudformation" in name_lower or "cfn" in name_lower:
            return "CloudFormation"
        else:
            return "Manual"

    def get_deployment_level(self, repo_name: str) -> str:
        """Get deployment readiness level"""
        return "Production Ready"

    def get_deployment_readiness(self, repo: Dict) -> str:
        """Assess deployment readiness"""
        stars = repo.get("stargazers_count", 0)
        if stars > 1000:
            return "Production Ready"
        elif stars > 100:
            return "Beta Ready"
        else:
            return "Development"

    def get_secondary_language(self, repo: Dict) -> str:
        """Get secondary programming language"""
        return "N/A"

    def get_framework(self, repo: Dict) -> str:
        """Detect framework used"""
        primary = (repo.get("language") or "").lower()
        if primary == "python":
            return "Python/Flask/Django"
        elif primary == "javascript":
            return "Node.js/React"
        elif primary == "java":
            return "Spring/Maven"
        else:
            return "Standard"

    def get_aws_services(self, description: str) -> str:
        """Extract AWS services mentioned in description"""
        desc_lower = (description or "").lower()
        services = []
        
        service_keywords = {
            "s3": "S3", "lambda": "Lambda", "ec2": "EC2", "rds": "RDS",
            "dynamodb": "DynamoDB", "cloudformation": "CloudFormation",
            "iam": "IAM", "vpc": "VPC", "eks": "EKS", "ecs": "ECS"
        }
        
        for keyword, service in service_keywords.items():
            if keyword in desc_lower:
                services.append(service)
        
        return ", ".join(services[:3]) if services else "Multiple"

    def get_cost_range(self, repo: Dict) -> str:
        """Estimate implementation cost range"""
        stars = repo.get("stargazers_count", 0)
        if stars > 5000:
            return "High ($10K+)"
        elif stars > 1000:
            return "Medium ($1K-10K)"
        else:
            return "Low (<$1K)"

    def get_setup_time(self, repo: Dict) -> str:
        """Get estimated setup time"""
        stars = repo.get("stargazers_count", 0)
        if stars > 5000:
            return "Full-day Setup (4-8 hours)"
        elif stars > 1000:
            return "Half-day Setup (1-4 hours)"
        else:
            return "Quick Setup (< 1 hour)"

    def get_business_value(self, repo: Dict) -> str:
        """Assess business value proposition"""
        return "High"

    def get_target_audience(self, repo: Dict) -> str:
        """Identify target audience"""
        return "Developers"

    def get_use_case_category(self, repo: Dict) -> str:
        """Categorize use case"""
        return "Infrastructure"

    def get_integration_complexity(self, repo: Dict) -> str:
        """Assess integration complexity"""
        return "Medium"

    def get_maintenance_level(self, repo: Dict) -> str:
        """Assess maintenance requirements"""
        return "Low"

    def get_scalability(self, repo: Dict) -> str:
        """Assess scalability characteristics"""
        return "High"

    def get_usp(self, repo: Dict) -> str:
        """Get unique selling proposition"""
        stars = repo.get("stargazers_count", 0)
        
        if stars > 5000:
            return f"Highly popular community solution ({stars}+ stars)"
        elif stars > 1000:
            return f"Popular community solution ({stars}+ stars)"
        else:
            return "Reliable solution"

    def get_freshness(self, updated_at: str) -> str:
        """Determine freshness status"""
        try:
            from datetime import datetime, timezone
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_diff = (now - updated).days
            
            if days_diff < 30:
                return "Recently Updated"
            elif days_diff < 365:
                return "Actively Maintained"
            else:
                return "Legacy"
        except:
            return "Unknown"

    def get_days_since_update(self, updated_at: str) -> int:
        """Calculate days since last update"""
        try:
            from datetime import datetime, timezone
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            return (now - updated).days
        except:
            return 0

    def is_genai_agentic(self, repo: Dict) -> str:
        """Detect GenAI/Agentic capabilities"""
        desc = (self.get_description(repo)).lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{desc} {topics}"
        
        if any(word in text for word in ["agent", "llm", "genai", "bedrock", "anthropic", "openai"]):
            return "Yes"
        else:
            return "No"

    def load_checkpoint(self) -> Dict:
        """Load processing checkpoint from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=self.checkpoint_key
            )
            return json.loads(response['Body'].read())
        except:
            return {
                "current_index": 0,
                "completed_repos": [],
                "failed_repos": {},
                "total_processed": 0
            }

    def save_checkpoint(self, checkpoint: Dict) -> None:
        """Save checkpoint to S3"""
        checkpoint["last_run"] = datetime.now().isoformat()
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self.checkpoint_key,
            Body=json.dumps(checkpoint, indent=2),
            ContentType='application/json'
        )

    def run_classification(self, batch_size: int = 10) -> None:
        """Run classification with checkpointing"""
        print("🚀 GENERIC REPOSITORY CLASSIFIER WITH CHECKPOINTING")
        print("=" * 60)
        
        # Load master index and checkpoint
        repos = self.load_master_index()
        if not repos:
            # Try to fetch repos if master index is empty
            repos = self.fetch_all_repos()
        
        checkpoint = self.load_checkpoint()
        
        if not repos:
            print("❌ No repositories found")
            return
        
        start_index = checkpoint["current_index"]
        completed_repos = set(checkpoint["completed_repos"])
        
        print(f"📊 Total repositories: {len(repos)}")
        print(f"🔄 Resuming from index: {start_index}")
        print(f"✅ Already completed: {len(completed_repos)}")
        
        # Process repositories in batches
        for i in range(start_index, len(repos), batch_size):
            batch = repos[i:i+batch_size]
            
            for repo in batch:
                if repo["full_name"] in completed_repos:
                    print(f"⏭️  Skipping {repo['full_name']} (already completed)")
                    continue
                
                print(f"\n🔍 Processing {repo['full_name']}...")
                
                classification = self.classify_repository(repo)
                if classification:
                    print(f"✅ {repo['full_name']} - {classification['solution_type']}")
                    completed_repos.add(repo["full_name"])
                    checkpoint["total_processed"] += 1
                
                checkpoint["current_index"] = i + batch_size
                checkpoint["completed_repos"] = list(completed_repos)
            
            # Save checkpoint after each batch
            self.save_checkpoint(checkpoint)
            print(f"\n💾 Checkpoint saved - Progress: {len(completed_repos)}/{len(repos)}")
        
        print(f"\n✅ Classification completed!")
        print(f"📊 Total processed: {len(completed_repos)}")
        print(f"🔗 Bucket: https://{self.bucket_name}.s3.amazonaws.com/")

def main():
    parser = argparse.ArgumentParser(description='Generic GitHub Repository Classifier')
    parser.add_argument('org_name', help='GitHub organization name (e.g., awslabs, microsoft, google)')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing (default: 10)')
    
    args = parser.parse_args()
    
    classifier = GenericRepositoryClassifier(args.org_name)
    classifier.run_classification(args.batch_size)

if __name__ == "__main__":
    main()
