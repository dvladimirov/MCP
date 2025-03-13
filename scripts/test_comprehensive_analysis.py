#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests

def test_comprehensive_analysis(repo_url, commit_sha, target_commit='HEAD'):
    """Test the comprehensive analysis endpoint
    
    Args:
        repo_url: URL of the Git repository to analyze
        commit_sha: Base commit SHA to compare from
        target_commit: Target commit to compare to (default: HEAD)
    """
    print(f"Testing comprehensive analysis for repository: {repo_url}")
    print(f"Comparing commits: {commit_sha} -> {target_commit}")
    
    # Create the payload
    payload = {
        "repo_url": repo_url,
        "commit_sha": commit_sha,
        "target_commit": target_commit
    }
    
    # Call the API endpoint directly
    try:
        response = requests.post(
            "http://localhost:8000/v1/git/analyze_comprehensive",
            json=payload,
            timeout=60
        )
        
        # Check for success
        if response.status_code == 200:
            result = response.json()
            
            print("\n=== Comprehensive Analysis Results ===")
            
            # Print summary
            if "summary" in result:
                print(f"\nSummary: {result['summary']}")
            
            # Print diff analysis if available
            diff_analysis = result.get("diff_analysis", {})
            print(f"\nCode Changes:")
            print(f"  Files changed: {diff_analysis.get('total_files_changed', 0)}")
            print(f"  Additions: {diff_analysis.get('total_additions', 0)}")
            print(f"  Deletions: {diff_analysis.get('total_deletions', 0)}")
            
            # Print requirements analysis if available
            req_analysis = result.get("requirements_analysis", {})
            if req_analysis.get("status") == "success":
                print(f"\nRequirements Changes:")
                
                # Added packages
                added_packages = req_analysis.get("added_packages", {})
                if added_packages:
                    print(f"\n  Added Dependencies ({len(added_packages)}):")
                    for pkg_name, version in added_packages.items():
                        print(f"    + {pkg_name}{version}")
                
                # Removed packages
                removed_packages = req_analysis.get("removed_packages", {})
                if removed_packages:
                    print(f"\n  Removed Dependencies ({len(removed_packages)}):")
                    for pkg_name, version in removed_packages.items():
                        print(f"    - {pkg_name}{version}")
                
                # Changed packages
                changed_packages = req_analysis.get("changed_packages", {})
                if changed_packages:
                    print(f"\n  Changed Dependencies ({len(changed_packages)}):")
                    for pkg_name, change in changed_packages.items():
                        print(f"    ~ {pkg_name}: {change['old']} -> {change['new']}")
            
            # Print AI analysis if available
            if "ai_analysis" in result:
                ai_analysis = result.get("ai_analysis", {})
                if "dependency_analysis" in ai_analysis:
                    dep_analysis = ai_analysis["dependency_analysis"]
                    
                    # Print risk assessment
                    print("\nRisk Assessment:")
                    risk_assessment = dep_analysis.get("risk_assessment", {})
                    
                    for risk_level in ["high_risk", "medium_risk", "low_risk"]:
                        risk_packages = risk_assessment.get(risk_level, [])
                        if risk_packages:
                            print(f"\n  {risk_level.replace('_', ' ').title()} ({len(risk_packages)}):")
                            for pkg in risk_packages:
                                pkg_name = pkg.get("package", "Unknown")
                                analysis = pkg.get("analysis", "No details available")
                                print(f"    • {pkg_name}: {analysis}")
            
            # Print recommendations
            recommendations = result.get("recommendations", [])
            if recommendations:
                print("\nRecommendations:")
                for idx, rec in enumerate(recommendations, 1):
                    print(f"  {idx}. {rec}")
            
            # Print next steps
            next_steps = result.get("next_steps", [])
            if next_steps:
                print("\nNext Steps:")
                for idx, step in enumerate(next_steps, 1):
                    print(f"  {idx}. {step}")
                    
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the comprehensive Git analysis")
    parser.add_argument("repo_url", help="URL of the Git repository")
    parser.add_argument("commit_sha", help="Base commit SHA to compare from")
    parser.add_argument("--target-commit", default="HEAD", help="Target commit to compare to (default: HEAD)")
    
    args = parser.parse_args()
    test_comprehensive_analysis(args.repo_url, args.commit_sha, args.target_commit) 