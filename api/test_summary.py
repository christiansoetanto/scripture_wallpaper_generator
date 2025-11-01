#!/usr/bin/env python3

import subprocess
import re

# Run the debug script and capture output
result = subprocess.run(['python3', 'debug_psalm1.py'], capture_output=True, text=True)
output = result.stdout

# Extract test case results
test_cases = re.findall(r'--- Test Case (\d+) ---.*?Contains \'Blessed\': (\w+).*?Contains \'manwho\': (\w+).*?Contains \'man who\': (\w+).*?Starts with \'is the man\': (\w+)', output, re.DOTALL)

print("=== Test Results Summary ===")
for case_num, blessed, manwho, man_who, starts_with in test_cases:
    print(f"Test Case {case_num}:")
    print(f"  ✓ Blessed preserved: {blessed}")
    print(f"  ✓ manwho fixed: {man_who}")
    print(f"  ✓ No 'manwho': {manwho == 'False'}")
    print(f"  ✓ No 'is the man' start: {starts_with == 'False'}")
    print()

# Check if all tests pass
all_blessed = all(blessed == 'True' for _, blessed, _, _, _ in test_cases)
all_man_who = all(man_who == 'True' for _, _, _, man_who, _ in test_cases)
all_no_manwho = all(manwho == 'False' for _, _, manwho, _, _ in test_cases)
all_no_starts = all(starts_with == 'False' for _, _, _, _, starts_with in test_cases)

if all_blessed and all_man_who and all_no_manwho and all_no_starts:
    print("🎉 ALL TESTS PASS! Both issues are fixed!")
else:
    print("❌ Some tests still failing")