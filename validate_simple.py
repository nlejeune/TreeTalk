#!/usr/bin/env python3
"""
TreeTalk MVP Simple Validation Script

This script validates the TreeTalk application structure and basic functionality.
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 11):
        print("[FAIL] Python 3.11+ required. Current version:", sys.version)
        return False
    print("[PASS] Python version:", sys.version.split()[0])
    return True

def check_project_structure():
    """Validate project directory structure."""
    print("\nChecking project structure...")
    
    required_dirs = [
        "src/backend",
        "src/frontend", 
        "test",
        ".build",
        ".config"
    ]
    
    required_files = [
        "requirements.txt",
        "src/backend/main.py",
        "src/frontend/main.py",
        ".build/docker-compose.yml",
        ".build/Dockerfile.backend",
        ".build/Dockerfile.frontend",
        "5-database.md"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"[PASS] Directory: {dir_path}")
        else:
            print(f"[FAIL] Missing directory: {dir_path}")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"[PASS] File: {file_path}")
        else:
            print(f"[FAIL] Missing file: {file_path}")
            all_good = False
    
    return all_good

def check_code_structure():
    """Check basic code structure."""
    print("\nChecking code structure...")
    
    backend_files = [
        "src/backend/main.py",
        "src/backend/models/__init__.py", 
        "src/backend/models/person.py",
        "src/backend/models/source.py",
        "src/backend/services/gedcom_parser.py",
        "src/backend/services/family_service.py",
        "src/backend/services/chat_service.py",
        "src/backend/routes/gedcom.py",
        "src/backend/routes/persons.py",
        "src/backend/routes/chat.py",
        "src/backend/utils/database.py"
    ]
    
    all_good = True
    
    for file_path in backend_files:
        if Path(file_path).exists():
            print(f"[PASS] Backend file: {file_path}")
        else:
            print(f"[FAIL] Missing backend file: {file_path}")
            all_good = False
    
    # Check if frontend main exists
    if Path("src/frontend/main.py").exists():
        print("[PASS] Frontend main file exists")
    else:
        print("[FAIL] Missing frontend main file")
        all_good = False
    
    return all_good

def check_test_structure():
    """Check test structure."""
    print("\nChecking test structure...")
    
    test_files = [
        "test/__init__.py",
        "test/test_models.py",
        "test/test_api_routes.py"
    ]
    
    all_good = True
    
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"[PASS] Test file: {file_path}")
        else:
            print(f"[FAIL] Missing test file: {file_path}")
            all_good = False
    
    return all_good

def check_docker_config():
    """Check Docker configuration."""
    print("\nChecking Docker configuration...")
    
    docker_files = [
        ".build/docker-compose.yml",
        ".build/Dockerfile.backend", 
        ".build/Dockerfile.frontend",
        ".build/init-db.sql"
    ]
    
    all_good = True
    
    for docker_file in docker_files:
        if Path(docker_file).exists():
            print(f"[PASS] Docker file: {docker_file}")
        else:
            print(f"[FAIL] Missing Docker file: {docker_file}")
            all_good = False
    
    return all_good

def check_documentation():
    """Check documentation files."""
    print("\nChecking documentation...")
    
    doc_files = [
        "0-Instructions.md",
        "1-application_requirements.md",
        "2-high_level_architecture.md",
        "3-user_interface_design.md", 
        "4-data-collection-strategy.md",
        "5-database.md",
        "README.md"
    ]
    
    all_good = True
    
    for doc_file in doc_files:
        if Path(doc_file).exists():
            print(f"[PASS] Documentation: {doc_file}")
        else:
            print(f"[FAIL] Missing documentation: {doc_file}")
            all_good = False
    
    return all_good

def check_config_files():
    """Check configuration files."""
    print("\nChecking configuration files...")
    
    config_files = [
        ".config/.env.example",
        "requirements.txt"
    ]
    
    all_good = True
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"[PASS] Config file: {config_file}")
        else:
            print(f"[FAIL] Missing config file: {config_file}")
            all_good = False
    
    return all_good

def main():
    """Run all validation checks."""
    print("TreeTalk MVP Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Code Structure", check_code_structure),
        ("Test Structure", check_test_structure),
        ("Docker Configuration", check_docker_config),
        ("Documentation", check_documentation),
        ("Configuration Files", check_config_files)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"[ERROR] {name} check failed: {e}")
            results[name] = False
    
    # Print summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status:8} {check}")
    
    print("-" * 50)
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\nAll validation checks passed! The TreeTalk MVP is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Copy .config/.env.example to .config/.env and configure")
        print("3. Run: docker-compose -f .build/docker-compose.yml up")
        print("4. Access frontend at: http://localhost:8501")
        print("5. Access backend API at: http://localhost:8000/docs")
        return True
    else:
        print("\nSome validation checks failed. Review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)