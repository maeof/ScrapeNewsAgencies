import re

print(re.findall( r'all (.*?) are', 'all cats are smarter than dogs, all dogs are dumber than cats'))
# Output: ['cats', 'dogs']

print([x.group() for x in re.finditer( r'all (.*?) are', 'all cats are smarter than dogs, all dogs are dumber than cats')])
# Output: ['all cats are', 'all dogs are']

print("stringidfngidfs"[:5])