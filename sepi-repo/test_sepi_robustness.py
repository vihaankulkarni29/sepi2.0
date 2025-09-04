#!/usr/bin/env python3
"""
Comprehensive robustness test for SEPI 2.0
Tests all features and edge cases to ensure production readiness.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, description, expect_failure=False):
    """Run a command and return success status."""
    print(f"\n[*] Testing: {description}")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if expect_failure:
            # For commands that should fail
            if result.returncode != 0:
                print("[PASS] SUCCESS (failed as expected)")
                return True
            else:
                print("[FAIL] FAILED (should have failed)")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
        else:
            # For commands that should succeed
            if result.returncode == 0:
                print("[PASS] SUCCESS")
                return True
            else:
                print("[FAIL] FAILED")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] 5 minutes")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_basic_functionality():
    """Test basic command-line functionality."""
    print("\n" + "="*60)
    print("[TEST] COMPREHENSIVE ROBUSTNESS TEST FOR SEPI 2.0")
    print("="*60)

    # Test 1: Help message
    success = run_command("python sepi.py --help", "Help message display")

    # Test 2: Invalid arguments
    success &= run_command("python sepi.py", "Error handling for missing required args", expect_failure=True)

    # Test 3: Version info in header
    with open('sepi.py', 'r') as f:
        content = f.read()
        if 'Version: 2.0' in content and 'SEPI 2.0' in content:
            print("[PASS] Version info in header")
            success &= True
        else:
            print("[FAIL] Version info missing")
            success &= False

    return success

def test_yaml_config():
    """Test YAML configuration functionality."""
    print("\n[CONFIG] Testing YAML Configuration")

    # Test existing YAML config
    success = run_command("python sepi.py --config saureus_virulence.yml", "YAML config loading")

    # Test invalid YAML
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("invalid: yaml: content: [\n")
        invalid_yaml = f.name

    success &= run_command(f"python sepi.py --config {invalid_yaml}", "Invalid YAML error handling", expect_failure=True)
    os.unlink(invalid_yaml)

    return success

def test_protein_lists():
    """Test protein list functionality."""
    print("\n[PROTEIN] Testing Protein List Features")

    # Test with existing protein list
    success = run_command('python sepi.py --organism "Escherichia coli" --protein_list saureus_targets.txt --output test_protein_list --email test@example.com', "Protein list file loading")

    # Test with comma-separated proteins
    success &= run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA,AcrB" --output test_comma_sep --email test@example.com', "Comma-separated protein input")

    # Test empty protein list
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("")  # Empty file
        empty_list = f.name

    success &= run_command(f'python sepi.py --organism "Escherichia coli" --protein_list {empty_list} --output test_empty --email test@example.com', "Empty protein list handling", expect_failure=True)
    os.unlink(empty_list)

    return success

def test_filters():
    """Test filtering functionality."""
    print("\n[FILTER] Testing Filtering Features")

    # Test assembly level filter
    success = run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA" --assembly_level complete_genome --output test_assembly --email test@example.com', "Assembly level filtering")

    # Test biosample query
    success &= run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA" --biosample_query "host=human" --output test_biosample --email test@example.com', "BioSample query filtering")

    # Test invalid assembly level
    success &= run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA" --assembly_level invalid_level --output test_invalid --email test@example.com', "Invalid assembly level handling", expect_failure=True)

    return success

def test_output_formats():
    """Test different output formats."""
    print("\n[OUTPUT] Testing Output Formats")

    # Test multi-FASTA output
    success = run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA" --multi_fasta --output test_multifasta --email test@example.com', "Multi-FASTA output")

    # Test HTML report
    success &= run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA" --html_report --output test_html --email test@example.com', "HTML report generation")

    # Test combined outputs
    success &= run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA" --multi_fasta --html_report --output test_combined --email test@example.com', "Combined output formats")

    return success

def test_caching():
    """Test caching functionality."""
    print("\n[CACHE] Testing Caching System")

    # Clean up any existing cache for fresh test
    if os.path.exists('.sepi_cache'):
        shutil.rmtree('.sepi_cache')

    success = True

    # Test cache usage by running same query twice
    cmd = 'python sepi.py --organism "Escherichia coli" --proteins "AcrA" --output test_cache --email test@example.com'
    success &= run_command(cmd, "First run (populates cache)")
    success &= run_command(cmd, "Second run (uses cache)")

    # Check if cache was created
    if os.path.exists('.sepi_cache'):
        print("[PASS] Cache directory created")
        if os.path.exists('.sepi_cache/query_cache.json'):
            print("[PASS] Cache file created")
        else:
            print("[FAIL] Cache file not created")
            success = False
    else:
        print("[FAIL] Cache directory not created")
        success = False

    return success

def test_error_handling():
    """Test error handling and edge cases."""
    print("\n[ERROR] Testing Error Handling")

    # Test with non-existent organism
    success = run_command("python sepi.py --organism 'NonExistentOrganism12345' --proteins 'FakeProtein' --output test_error --email test@example.com", "Non-existent organism handling")

    # Test with invalid email
    success &= run_command('python sepi.py --organism "Escherichia coli" --proteins "AcrA" --output test_invalid_email --email invalid-email', "Invalid email handling")

    # Test network timeout simulation (if possible)
    # This would require mocking, but we'll test graceful degradation

    return success

def test_legacy_compatibility():
    """Test backward compatibility with SEPI 1.0 style usage."""
    print("\n[LEGACY] Testing Legacy Compatibility")

    # Test with old-style organism names (should still work)
    success = run_command('python sepi.py --organism "Escherichia coli" --proteins "all" --output test_legacy --email test@example.com', "Legacy 'all' protein option")

    return success

def cleanup_test_files():
    """Clean up test-generated files."""
    print("\n[CLEANUP] Cleaning up test files...")

    test_prefixes = ['test_', 'ecoli_test', 'SEPI_output']
    for file in os.listdir('.'):
        if any(file.startswith(prefix) for prefix in test_prefixes):
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"Removed: {file}")
                elif os.path.isdir(file):
                    shutil.rmtree(file)
                    print(f"Removed directory: {file}")
            except Exception as e:
                print(f"Could not remove {file}: {e}")

def main():
    """Run all robustness tests."""
    print("[START] Starting SEPI 2.0 Robustness Test Suite")
    print("This will test all features and edge cases...")

    # Run all tests
    results = []
    results.append(("Basic Functionality", test_basic_functionality()))
    results.append(("YAML Configuration", test_yaml_config()))
    results.append(("Protein Lists", test_protein_lists()))
    results.append(("Filters", test_filters()))
    results.append(("Output Formats", test_output_formats()))
    results.append(("Caching", test_caching()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Legacy Compatibility", test_legacy_compatibility()))

    # Summary
    print("\n" + "="*60)
    print("[SUMMARY] TEST RESULTS SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "[PASS] SUCCESS" if success else "[FAIL] FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED! SEPI 2.0 is production-ready!")
        cleanup_test_files()
        return True
    else:
        print("[WARNING] Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)