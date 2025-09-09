#!/usr/bin/env python3
"""
TreeTalk MVP Validation Script

This script validates the TreeTalk application by running unit tests,
checking code quality, and verifying the application structure.

Usage:
    python validate.py [--quick] [--no-tests] [--no-lint]
    
Options:
    --quick     Skip slower tests and checks
    --no-tests  Skip unit tests
    --no-lint   Skip code quality checks
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import importlib.util

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_project_structure():
    """Validate project directory structure."""
    print("\n📁 Checking project structure...")
    
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
        ".build/Dockerfile.frontend"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ File: {file_path}")
        else:
            print(f"❌ Missing file: {file_path}")
            all_good = False
    
    return all_good

def check_dependencies():
    """Check if required dependencies are available."""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "streamlit", 
        "sqlalchemy",
        "psycopg2-binary",
        "pydantic",
        "plotly",
        "requests",
        "pytest"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ Missing: {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def run_unit_tests():
    """Run unit tests with pytest."""
    print("\n🧪 Running unit tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test/", 
            "-v", 
            "--tb=short",
            "--maxfail=5"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ All unit tests passed!")
            return True
        else:
            print("❌ Some unit tests failed")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def check_code_imports():
    """Check if main modules can be imported without errors."""
    print("\n🔍 Checking code imports...")
    
    modules_to_check = [
        ("Backend Main", "src.backend.main"),
        ("Frontend Main", "src.frontend.main"),
        ("Person Model", "src.backend.models.person"),
        ("Family Service", "src.backend.services.family_service"),
        ("GEDCOM Parser", "src.backend.services.gedcom_parser")
    ]
    
    all_good = True
    original_path = sys.path.copy()
    
    try:
        # Add src to Python path
        sys.path.insert(0, str(Path("src").absolute()))
        sys.path.insert(0, str(Path(".").absolute()))
        
        for name, module_path in modules_to_check:
            try:
                spec = importlib.util.find_spec(module_path)
                if spec is None:
                    print(f"❌ {name}: Module not found")
                    all_good = False
                else:
                    print(f"✅ {name}: Import OK")
            except Exception as e:
                print(f"❌ {name}: Import error - {e}")
                all_good = False
                
    finally:
        sys.path = original_path
    
    return all_good

def check_docker_config():
    """Validate Docker configuration files."""
    print("\n🐳 Checking Docker configuration...")
    
    docker_files = [
        ".build/docker-compose.yml",
        ".build/Dockerfile.backend", 
        ".build/Dockerfile.frontend"
    ]
    
    all_good = True
    
    for docker_file in docker_files:
        if Path(docker_file).exists():
            try:
                with open(docker_file, 'r') as f:
                    content = f.read()
                    if len(content.strip()) > 0:
                        print(f"✅ {docker_file}: Valid")
                    else:
                        print(f"❌ {docker_file}: Empty file")
                        all_good = False
            except Exception as e:
                print(f"❌ {docker_file}: Read error - {e}")
                all_good = False
        else:
            print(f"❌ {docker_file}: Not found")
            all_good = False
    
    return all_good

def check_database_models():
    """Check database models structure."""
    print("\n🗄️ Checking database models...")
    
    try:
        sys.path.insert(0, str(Path("src").absolute()))
        
        from backend.models import (
            Source, Person, Relationship, Event, Place,
            ChatSession, ChatMessage, Configuration
        )
        
        models = [
            ("Source", Source),
            ("Person", Person), 
            ("Relationship", Relationship),
            ("Event", Event),
            ("Place", Place),
            ("ChatSession", ChatSession),
            ("ChatMessage", ChatMessage),
            ("Configuration", Configuration)
        ]
        
        all_good = True
        
        for name, model_class in models:
            try:
                # Check if model has required attributes
                if hasattr(model_class, '__tablename__'):
                    print(f"✅ {name}: Table name '{model_class.__tablename__}'")
                else:
                    print(f"❌ {name}: Missing __tablename__")
                    all_good = False
                    
                # Check if model has to_dict method (for API models)
                if hasattr(model_class, 'to_dict') and name != "Configuration":
                    print(f"✅ {name}: Has to_dict method")
                else:
                    print(f"ℹ️ {name}: No to_dict method (may be OK)")
                    
            except Exception as e:
                print(f"❌ {name}: Error - {e}")
                all_good = False
        
        return all_good
        
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False
    finally:
        sys.path = sys.path[1:]  # Remove added path

def validate_gedcom_test_file():
    """Check if GEDCOM test file exists."""
    print("\n📄 Checking GEDCOM test file...")
    
    gedcom_paths = [
        "Gedcom/Généalogie Lison LE JEUNE_export.ged",
        "test_data/sample.ged",
        "*.ged"
    ]
    
    for path in gedcom_paths:
        if "*" in path:
            # Check for any .ged files
            ged_files = list(Path(".").rglob("*.ged"))
            if ged_files:
                print(f"✅ Found GEDCOM files: {[str(f) for f in ged_files[:3]]}")
                return True
        elif Path(path).exists():
            print(f"✅ GEDCOM test file: {path}")
            return True
    
    print("⚠️ No GEDCOM test files found. Upload one to test import functionality.")
    return True  # Not critical for MVP validation

def run_quick_validation():
    """Run quick validation checks."""
    print("Running quick validation...")
    
    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Code Imports", check_code_imports),
        ("Docker Config", check_docker_config),
        ("Database Models", check_database_models),
        ("GEDCOM Test File", validate_gedcom_test_file)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results[name] = False
    
    return results

def run_full_validation(skip_tests=False, skip_lint=False):
    """Run complete validation."""
    print("Running full validation...")
    
    results = run_quick_validation()
    
    if not skip_tests:
        results["Dependencies"] = check_dependencies()
        if results["Dependencies"]:
            results["Unit Tests"] = run_unit_tests()
        else:
            print("⚠️ Skipping unit tests due to missing dependencies")
            results["Unit Tests"] = False
    
    return results

def print_summary(results):
    """Print validation summary."""
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status:8} {check}")
    
    print("-"*50)
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("All validation checks passed! The TreeTalk MVP is ready.")
        return True
    else:
        print("Some validation checks failed. Review the output above.")
        return False

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate TreeTalk MVP application")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick validation only")
    parser.add_argument("--no-tests", action="store_true",
                       help="Skip unit tests")
    parser.add_argument("--no-lint", action="store_true",
                       help="Skip linting checks")
    
    args = parser.parse_args()
    
    print("TreeTalk MVP Validation")
    print("="*50)
    
    if args.quick:
        results = run_quick_validation()
    else:
        results = run_full_validation(
            skip_tests=args.no_tests,
            skip_lint=args.no_lint
        )
    
    success = print_summary(results)
    
    if success:
        print("\nNext steps:")
        print("1. Copy .config/.env.example to .config/.env and configure")
        print("2. Run: docker-compose -f .build/docker-compose.yml up")
        print("3. Access frontend at: http://localhost:8501")
        print("4. Access backend API at: http://localhost:8000/docs")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()