#!/bin/bash

# Run all tests with coverage
echo "Running all tests with coverage..."
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test categories
echo -e "\nRun specific test categories:"
echo "  pytest -m unit          # Run only unit tests"
echo "  pytest -m integration   # Run only integration tests"
echo "  pytest -m security      # Run only security tests"
echo "  pytest -k test_auth     # Run only authentication tests"
echo "  pytest tests/test_transactions.py  # Run specific test file"

# Check coverage
echo -e "\nChecking test coverage..."
pytest --cov=. --cov-report=term-missing --cov-fail-under=70

echo -e "\nTest report generated in htmlcov/index.html"