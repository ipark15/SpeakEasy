"""
Quick end-to-end test: loads the most recent assessment JSON and sends it to Gemma.
Run: .venv/bin/python test_gemma.py
"""
import glob
import json
import sys
from dotenv import load_dotenv

load_dotenv()

# Find most recent assessment JSON
files = sorted(glob.glob("assessment_*.json"))
if not files:
    print("[error] No assessment_*.json found. Run test_pipeline.py first.")
    sys.exit(1)

path = files[-1]
print(f"Using: {path}\n")

with open(path) as f:
    assessment = json.load(f)

print(f"Composite score: {assessment['composite_score']}")
print(f"Dimensions: {assessment['scores_summary']}")
print(f"Tasks: {[t['task_id'] for t in assessment['tasks']]}")
print("\nSending to Gemma...\n")

from backend.agents.orchestrator_agent.gemma_client import generate_narrative

narrative = generate_narrative(assessment)

print("=" * 60)
for section, content in narrative.items():
    if content:
        print(f"\n[{section.upper()}]")
        print(content)
print("=" * 60)
