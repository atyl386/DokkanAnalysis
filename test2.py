lst = [[1, 2, 3], [4, 5, 6], [7]]

# create an index tuple of unknown length
index = (1, 2)

# use a loop to index into the nested lists sequentially
result = lst
for i in index:
    result = result[i]

print(result)  # Output: 6
