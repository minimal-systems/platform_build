import re
import sys
makefile_path = sys.argv[1]


# Read the Makefile
with open(makefile_path) as f:
    makefile = f.read()

# Parse the Makefile using regular expressions


rules = {}
for line in makefile.splitlines():
    # Skip empty lines or comments
    if not line or line.startswith('#'):
        continue

    # Use regular expressions to extract the target and dependencies
    match = re.match(r'(\S+):\s*(\S+(?:\s+\S+)*)', line)
    if not match:
        continue

    target, dependencies = match.groups()

    # Split the dependencies into a list
    dependencies = dependencies.split()

    # Save the rule in a dictionary
    rules[target] = dependencies

# Convert the rules to Python code
python_code = '\n'.join('{}: {}'.format(target, dependencies) for target, dependencies in rules.items())

# Print the Python code
print(python_code)
