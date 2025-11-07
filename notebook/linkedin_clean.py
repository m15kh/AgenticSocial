#!/usr/bin/env python3
"""
Test the LinkedIn text cleanup function
"""
import re

def clean_linkedin_text(text: str) -> str:
    """Clean text for LinkedIn"""
    # Replace parentheses with square brackets
    text = re.sub(r'\(([^)]+)\)', r'[\1]', text)
    
    # Remove markdown bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    
    # Remove markdown italic
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+)\*(?!\*)', r'\1', text)
    
    # Remove markdown headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown links [text](url) -> text url
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)
    
    # Clean up multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


# Test cases
test_cases = [
    {
        "name": "Parentheses in acronyms",
        "input": "Vision Language Models (VLM) are amazing (AI) tools",
        "expected": "Vision Language Models [VLM] are amazing [AI] tools"
    },
    {
        "name": "Markdown bold",
        "input": "This is **bold** text",
        "expected": "This is bold text"
    },
    {
        "name": "Markdown links",
        "input": "Check [this article](https://example.com) out",
        "expected": "Check this article https://example.com out"
    },
    {
        "name": "Complex case",
        "input": "**Mixture of Experts (MoE)** is a technique where models use specialized sub-networks (experts)",
        "expected": "Mixture of Experts [MoE] is a technique where models use specialized sub-networks [experts]"
    },
    {
        "name": "Multiple parentheses",
        "input": "LLM (Large Language Model) and VLM (Vision Language Model) are both AI (Artificial Intelligence) systems",
        "expected": "LLM [Large Language Model] and VLM [Vision Language Model] are both AI [Artificial Intelligence] systems"
    }
]

print("=" * 80)
print("TESTING LINKEDIN TEXT CLEANUP")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. {test['name']}")
    print("-" * 80)
    print(f"Input:    {test['input']}")
    
    result = clean_linkedin_text(test['input'])
    print(f"Output:   {result}")
    print(f"Expected: {test['expected']}")
    
    if result == test['expected']:
        print("✅ PASS")
    else:
        print("❌ FAIL")

print("\n" + "=" * 80)
print("Testing complete!")
print("=" * 80)