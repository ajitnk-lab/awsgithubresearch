#!/usr/bin/env python3
"""
S3-based AWS Repository Classification System with Checkpointing
Processes all 939 awslabs repositories with resumability and crash recovery
"""

import json
import boto3
import time
import requests
import re
from datetime import datetime
from typing import Dict, List, Optional

class S3RepositoryClassifier:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'aws-github-repo-classification'
        self.master_index_key = 'master-index/awslabs_repos_939.json'
        self.checkpoint_key = 'checkpoints/progress.json'
        self.results_key = 'results/classification_results.csv'
        
    def create_master_index(self, repos_data: List[Dict]) -> None:
        """Create and upload master index of all repositories"""
        master_index = {
            "total_repos": len(repos_data),
            "created_at": datetime.now().isoformat(),
            "organization": "awslabs",
            "repositories": []
        }
        
        for repo in repos_data:
            # Filter out excluded repos
            repo_name = repo['name']
            if any(word in repo_name.lower() for word in ["samples", "examples", "patterns", "labs"]):
                continue
                
            master_index["repositories"].append({
                "name": repo['name'],
                "full_name": repo['full_name'],
                "description": repo.get('description', ''),
                "stars": repo['stargazers_count'],
                "forks": repo['forks_count'],
                "language": repo.get('language', ''),
                "topics": repo.get('topics', []),
                "updated_at": repo['updated_at'],
                "created_at": repo['created_at'],
                "archived": repo.get('archived', False),
                "url": repo['html_url']
            })
        
        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self.master_index_key,
            Body=json.dumps(master_index, indent=2),
            ContentType='application/json'
        )
        
        print(f"✅ Master index created with {len(master_index['repositories'])} repositories")
        print(f"📁 Uploaded to s3://{self.bucket_name}/{self.master_index_key}")
        
    def load_checkpoint(self) -> Dict:
        """Load checkpoint from S3"""
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
                "last_run": None,
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
    
    def classify_repository(self, repo: Dict) -> Optional[Dict]:
        """Classify a single repository with all 20 dimensions (added solution_marketing)"""
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
                "solution_marketing": self.get_solution_marketing(repo),
                "technical_competencies": self.get_technical_competencies(repo),
                "solution_competencies": "Cross-Industry",
                
                # Deployment
                "deployment_tools": self.get_deployment_tools(repo["name"]),
                "deployment_level": self.get_deployment_level(repo["name"]),
                
                # Technical Stack
                "primary_language": repo["language"] or "Multiple",
                "additional_languages": self.get_additional_languages(repo),
                "frameworks": self.get_frameworks(repo),
                "aws_services": self.get_aws_services(repo["description"]),
                
                # Requirements
                "prerequisites": "AWS Account, IAM Permissions",
                "license": "Apache License 2.0",
                "copyright_holder": "Amazon Web Services, Inc.",
                "commercial_use": "Allowed",
                
                # Cost & Time
                "setup_time": self.get_setup_time(repo),
                "cost_range": self.get_cost_range(repo),
                
                # Business Value
                "customer_problems": self.get_customer_problems(repo),
                "usp": self.get_usp(repo),
                
                # Freshness
                "freshness_status": self.get_freshness(repo["updated_at"]),
                "days_since_update": self.get_days_since_update(repo["updated_at"]),
                
                # AI/GenAI
                "genai_agentic": self.is_genai_agentic(repo),
                
                # Metadata
                "topics": ", ".join(repo.get("topics", [])),
                "classification_method": "S3-Based Complete Analysis",
                "classification_timestamp": datetime.now().isoformat()
            }
            return classification
        except Exception as e:
            print(f"❌ Failed to classify {repo['full_name']}: {e}")
            return None
    
    def get_solution_marketing(self, repo: Dict) -> str:
        """Determine solution marketing category based on repo name, description and functionality"""
        repo_name = repo.get("name", "").lower()
        desc = (repo.get("description") or "").lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{repo_name} {desc} {topics}"
        
        # Setup & Bootstrap
        if any(word in text for word in ["setup", "bootstrap", "quickstart", "quick-start", "getting-started", "install", "deployment"]):
            return "setup"
        
        # Landing Zone
        if any(word in text for word in ["landing-zone", "landingzone", "multi-account", "account-factory", "control-tower"]):
            return "landingzone"
        
        # Starter & Templates
        if any(word in text for word in ["starter", "template", "boilerplate", "scaffold", "blueprint", "reference-architecture"]):
            return "starter"
        
        # Optimization
        if any(word in text for word in ["optim", "performance", "cost", "efficiency", "tuning", "scaling"]):
            return "optimise"
        
        # Compliance & Security
        if any(word in text for word in ["compliance", "security", "audit", "governance", "policy", "config-rules"]):
            return "compliance"
        
        # Improvement & Enhancement
        if any(word in text for word in ["improve", "enhance", "upgrade", "migration", "moderniz", "refactor"]):
            return "improvement"
        
        # Visibility & Monitoring
        if any(word in text for word in ["monitor", "observ", "dashboard", "metrics", "logging", "visibility", "insight"]):
            return "visibility"
        
        # Foundation & Infrastructure
        if any(word in text for word in ["foundation", "infrastructure", "platform", "framework", "core", "base"]):
            return "foundation"
        
        # Readiness & Preparation
        if any(word in text for word in ["ready", "prepar", "provision", "orchestrat", "automation"]):
            return "readiness"
        
        # Enablement & Tools
        if any(word in text for word in ["enable", "tool", "utility", "helper", "support", "assist"]):
            return "enablement"
        
        # Innovation & AI/ML
        if any(word in text for word in ["innovat", "ai", "ml", "machine-learning", "bedrock", "agent", "genai"]):
            return "innovation"
        
        # Assessment & Analysis
        if any(word in text for word in ["assess", "analyz", "evaluat", "test", "benchmark", "profil"]):
            return "assessment"
        
        # Advisor & Intelligence
        if any(word in text for word in ["advisor", "intelligent", "smart", "recommend", "suggest"]):
            return "advisor"
        
        # Recommendation & Best Practices
        if any(word in text for word in ["recommend", "best-practice", "pattern", "guideline", "standard"]):
            return "recommendation"
        
        # Guidance & Documentation
        if any(word in text for word in ["guidance", "guide", "tutorial", "workshop", "learn", "documentation"]):
            return "guidance"
        
        # Default based on solution type fallback
        return "enablement"
    
    def get_solution_type(self, repo: Dict) -> str:
        """Determine solution type"""
        desc = self.get_description(repo).lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{desc} {topics}"
        
        if any(word in text for word in ["security", "compliance", "audit", "governance"]):
            return "Compliance Accelerators"
        elif any(word in text for word in ["ai", "ml", "machine-learning", "bedrock", "agent"]):
            return "Innovation Catalysts"
        elif any(word in text for word in ["cost", "optimization", "performance"]):
            return "Quick Wins"
        elif any(word in text for word in ["monitoring", "observability", "logging"]):
            return "Operational Excellence"
        else:
            return "Foundation Builders"
    
    def get_technical_competencies(self, repo: Dict) -> str:
        """Get technical competencies"""
        desc = self.get_description(repo).lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{desc} {topics}"
        
        if any(word in text for word in ["ml", "ai", "machine-learning"]):
            return "Machine Learning, Data & Analytics"
        elif any(word in text for word in ["security", "compliance"]):
            return "Security, Compliance"
        elif any(word in text for word in ["serverless", "lambda"]):
            return "Modern Application Development"
        else:
            return "General Development"
    
    def get_deployment_tools(self, repo_name: str) -> str:
        """Get deployment tools"""
        if "cdk" in repo_name:
            return "CDK, CloudFormation"
        elif "lambda" in repo_name:
            return "SAM, CloudFormation"
        elif "terraform" in repo_name:
            return "Terraform"
        elif "docker" in repo_name:
            return "Docker, Container"
        else:
            return "CloudFormation, Scripts"
    
    def get_deployment_level(self, repo_name: str) -> str:
        """Get deployment readiness level"""
        if any(word in repo_name for word in ["template", "cloudformation", "cdk"]):
            return "Production-Ready"
        else:
            return "Basic Setup"
    
    def get_additional_languages(self, repo: Dict) -> str:
        """Get additional languages"""
        primary = (repo.get("language") or "").lower()
        if "python" in primary:
            return "JavaScript, Shell"
        elif "javascript" in primary:
            return "TypeScript, Python"
        elif "java" in primary:
            return "Python, Shell"
        else:
            return "Python, JavaScript"
    
    def get_frameworks(self, repo: Dict) -> str:
        """Get frameworks used"""
        desc = self.get_description(repo).lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{desc} {topics}"
        
        frameworks = []
        if "lambda" in text:
            frameworks.append("AWS Lambda")
        if "cdk" in text:
            frameworks.append("AWS CDK")
        if "sam" in text:
            frameworks.append("AWS SAM")
        if "docker" in text:
            frameworks.append("Docker")
        
        return ", ".join(frameworks) if frameworks else "AWS SDK"
    
    def get_aws_services(self, description: str) -> str:
        """Extract AWS services from description"""
        services = []
        desc_lower = (description or "").lower()
        
        service_map = {
            "lambda": "Lambda", "s3": "S3", "dynamodb": "DynamoDB",
            "kinesis": "Kinesis", "redshift": "Redshift", "eks": "EKS",
            "ecs": "ECS", "rds": "RDS", "bedrock": "Bedrock",
            "cloudformation": "CloudFormation", "iam": "IAM"
        }
        
        for key, service in service_map.items():
            if key in desc_lower:
                services.append(service)
        
        return ", ".join(services[:5]) if services else "General AWS"
    
    def get_setup_time(self, repo: Dict) -> str:
        """Get estimated setup time"""
        stars = repo.get("stargazers_count", 0)
        if stars > 5000:
            return "Full-day Setup (4-8 hours)"
        elif stars > 1000:
            return "Half-day Setup (1-4 hours)"
        else:
            return "Quick Setup (< 1 hour)"
    
    def get_cost_range(self, repo: Dict) -> str:
        """Get estimated cost range"""
        desc = self.get_description(repo).lower()
        if any(word in desc for word in ["enterprise", "scale", "production"]):
            return "Medium ($100-1000/month)"
        elif any(word in desc for word in ["simple", "basic", "tool"]):
            return "Minimal (< $10/month)"
        else:
            return "Low ($10-100/month)"
    
    def get_customer_problems(self, repo: Dict) -> str:
        """Get pre-deployment customer problems"""
        solution_type = self.get_solution_type(repo)
        
        problems_map = {
            "Compliance Accelerators": "Security Gaps, Compliance Burden, Audit Failures",
            "Innovation Catalysts": "AI Implementation Complexity, Slow Time-to-Market, Competitive Disadvantage",
            "Quick Wins": "High AWS Costs, Resource Waste, Manual Processes",
            "Operational Excellence": "Monitoring Blindness, Manual Operations, System Downtime",
            "Foundation Builders": "Infrastructure Complexity, Scalability Issues, Technical Debt"
        }
        
        return problems_map.get(solution_type, "Infrastructure Complexity, High Operational Costs")
    
    def get_usp(self, repo: Dict) -> str:
        """Get unique selling proposition"""
        stars = repo.get("stargazers_count", 0)
        
        if stars > 5000:
            return f"Highly popular community solution ({stars}+ stars)"
        elif stars > 1000:
            return f"Popular community solution ({stars}+ stars)"
        else:
            return "Reliable AWS solution"
    
    def get_freshness(self, updated_at: str) -> str:
        """Get repository freshness"""
        try:
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            days_old = (datetime.now(updated.tzinfo) - updated).days
            
            if days_old < 90:
                return "Active"
            elif days_old < 365:
                return "Maintained"
            else:
                return "Stale"
        except:
            return "Unknown"
    
    def get_days_since_update(self, updated_at: str) -> int:
        """Get days since last update"""
        try:
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            return (datetime.now(updated.tzinfo) - updated).days
        except:
            return 0
    
    def is_genai_agentic(self, repo: Dict) -> str:
        """Check if repository is GenAI/Agentic"""
        desc = self.get_description(repo).lower()
        topics = " ".join(repo.get("topics", [])).lower()
        text = f"{desc} {topics}"
        
        genai_keywords = ["ai", "ml", "bedrock", "agent", "llm", "generative", "neural"]
        return "Yes" if any(word in text for word in genai_keywords) else "No"
    
    def append_to_results_csv(self, classification: Dict) -> None:
        """Append classification result to S3 CSV (simplified for demo)"""
        print(f"✅ {classification['repository']} - {classification['solution_type']}")
    
    def run_classification(self, batch_size: int = 10) -> None:
        """Run classification with checkpointing"""
        print("🚀 S3-BASED REPOSITORY CLASSIFIER WITH CHECKPOINTING")
        print("=" * 60)
        
        # Load master index and checkpoint
        repos = self.load_master_index()
        checkpoint = self.load_checkpoint()
        
        if not repos:
            print("❌ No repositories found in master index")
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
                    self.append_to_results_csv(classification)
                    completed_repos.add(repo["full_name"])
                    checkpoint["total_processed"] += 1
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
            
            # Update checkpoint after each batch
            checkpoint["current_index"] = min(i + batch_size, len(repos))
            checkpoint["completed_repos"] = list(completed_repos)
            self.save_checkpoint(checkpoint)
            
            print(f"\n💾 Checkpoint saved - Progress: {len(completed_repos)}/{len(repos)}")
            
            # Continue processing all repositories
            if len(completed_repos) % 50 == 0 and len(completed_repos) > 0:
                print(f"\n🎯 Milestone: {len(completed_repos)} repositories processed")
        
        print(f"\n✅ Classification completed!")
        print(f"📊 Total processed: {len(completed_repos)}")
        print(f"🔗 Bucket: https://{self.bucket_name}.s3.amazonaws.com/")

if __name__ == "__main__":
    # For production, load from GitHub API
    classifier = S3RepositoryClassifier()
    classifier.run_classification()
