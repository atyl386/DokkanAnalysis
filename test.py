import numpy as np
tree_struct =   ('unit',
                    [('General',
                        [('Name', []),('Exclusivity', []),('Class', []),('Type', []),('EZA\'d?',[]),('JP Release Date',[]),('GLB Release Date',[]),('HP',[]),('ATK',[]),('DEF', []),('12 Ki Modifier',[]),('Keep Stacking?',[])]),
                    ('Leader Skill',
                        [('Leader Skill Tier (Z-H)', [])])#,
                    #('Categories',[]),
                    #('Links',[]),
                    #('Super Attacks',
                    #    [('Unit Super Attacks',[])]),
                    #('Stats', [])
                    ]
                )
default_inputs = [['Super Saiyan Goku','DF','Super','STR','No','1/1/2023','1/1/2023','10000','10000','10000','1.5','No'],
                  ['H']]
queue = [(tree_struct, ())]
index_dict = {(): tree_struct[0]}

while queue:
    current_node, parent_indices = queue.pop(0)
    children = current_node[1]
    for i, child in enumerate(children):
        child_index = parent_indices + (i,)
        index_dict[child_index] = child[0]
        if child[1]:
            queue.append((child, child_index))
        else:
            default_input = default_inputs
            for j in child_index:
                default_input = default_input[j]
            print(default_input)

print(index_dict)