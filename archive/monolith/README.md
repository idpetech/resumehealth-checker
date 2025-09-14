# Monolith Archive

This directory contains archived files from the monolith version of the resume health checker.

## Archived Files:
- main_vercel.py - The main monolith application (had JavaScript issues)
- main.py - Entry point shim
- lambda_handler_monolith.py - Lambda handler for monolith
- test_monolith.py - Tests for monolith
- test_vercel.py - Vercel-specific tests
- requirements-vercel.txt - Vercel requirements
- vercel.json - Vercel configuration

## Why Archived:
The monolith had fundamental JavaScript issues (handleFileSelect ReferenceError) that prevented basic file upload functionality. The modular app (main_modular.py) works correctly and provides the same functionality.

## Current Working App:
Use `main_modular.py` - it's the working version with proper file upload, analysis, and payment flow.

Archived on: Mon Sep  1 19:13:31 EDT 2025
