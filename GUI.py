# Importing tkinter
# Importing ttk from tkinter
import tkinter as tk
from tkinter import ttk
from functools import partial
import datetime as dt
from tkinter import messagebox

# Function to store the input values
def store_values(indices,inputs,input_box):
    # Loop through all the input boxes
    for i,index in enumerate(indices):
        # Store the value in the dictionary
        (index_dict[index])[1] = inputs[i].get()
        data_dict[index] = inputs[i].get()
    input_box.destroy()
    print(data_dict)
    # Should also update default values and close window

# Define a function to validate the input
def validate_input(value, type, data_validation):
    if value == "":
        return True
    if type == 'List':
        if value not in data_validation:
            return False
    elif type == 'Date':
        try:
            date = dt.datetime.strptime(value, '%d/%m/%Y')
        except:
            return False
    elif type == 'Int':
        try:
            value = int(value)
        except:
            return False
    return True

def on_invalid(input_entry):
    """
    Show the error message if the data is not valid
    :return:
    """
    input_entry.delete(0,tk.END)
    messagebox.showerror('Input Error', 'Please Enter a valid input.')

# Define a function to create inputs boxes for a given tree node

def create_input_box(i):
    maxRows = 43
    input_box = tk.Toplevel()
    input_box.title((index_dict[i])[0]+" Input Box")
    input_box.geometry("1000x800")
    inputs = []
    children_indices = [i+(j,) for j in range(len(index_dict[i][1]))]
    for i,index in enumerate(children_indices):
        label = tk.Label(input_box, text=(index_dict[index])[0])
        label.grid(row=(i)%maxRows,column=((i)//maxRows)*2,sticky=tk.W)
        input_entry = tk.Entry(input_box)
        input_entry.insert(i,(index_dict[index])[1]) # Add default value
        # Data validation
        input_entry.config(validate="focusout", validatecommand=(input_entry.register(lambda value, index=index: validate_input(value,
            (index_dict[index])[2],(index_dict[index])[3])),'%P'),invalidcommand=(input_entry.register(lambda input_entry=input_entry: on_invalid(input_entry))))
        input_entry.grid(row=(i)%maxRows,column=((i)//maxRows)*2+1,sticky=tk.W)
        inputs.append(input_entry)
    # Create a button to store the input value
    store_button = tk.Button(input_box, text="Enter", command=partial(store_values,children_indices,inputs,input_box))
    store_button.grid(row=(i+1)%maxRows,column=((i+1)//maxRows)*2,columnspan=2)
# Define a function to create input boxes for all tree nodes
def create_input_boxes(event):
    nonInputItems = [('3',)]
    selected_item = tree.selection()
    if selected_item:
        if selected_item not in nonInputItems:
            create_input_box(tuple(map(int, selected_item)))

numCategories = 90
numFormsMax = 5
links = ['All in the Family','Android Assault','Attack of the Clones','Auto Regeneration','Battlefield Diva','Berserker','Big Bad Bosses','Blazing Battle','Bombardment','Brainiacs','Brutal Beatdown','Budding Warrior','Champion\'s Strength','Cold Judgement','Connoisseur','Cooler\'s Armored Squad','Cooler\'s Underling','Courage','Coward','Crane School','Deficit Boost','Demonic Power','Demonic Ways','Destroyer of the Universe','Dismal Future','Dodon Ray','Energy Absorption','Evil Autocrats','Experienced Fighters','Family Ties','Fear and Faith','Fierce Battle','Flee','Formidable Enemy','Fortuneteller Baba\'s Fighter','Frieza\'s Army','Frieza\'s Minion','Fused Fighter','Fusion','Fusion Failure','Galactic Warriors','Galactuc Visitor','Gaze of Respect','Gentleman','Godly Power','Golden Warrior','Golden Z-Fighter','GT','Guidance of the Dragon Balls','Hardened Grudge','Hatred of Saiyans','Hero','Hero of Justice','High Compatility','Infighter','Infinite Energy','Infinite Regeneration','Kamehameha','Legendary Power','Limit-Breaking Form','Loyalty','Majin','Majin Resurrection Plan','Master of Magic','Mechanical Menaces','Messenger from the Future','Metamorphosis','Money Money Money','More Than Meets the Eye','Namekians','New','New Frieza Army','Nightmare','None','Organic Upgrade','Otherworld Warriors','Over 9000','Over in a Flash','Patrol','Penguin Village Adventure','Power Bestowed by God','Prepared for Battle','Prodigies','Respect','Resurrection F','Revival','Royal Lineage','RR Army','Saiyan Pride','Saiyan Roar','Saiyan Warrior Race','Scientist','Shadow Dragons','Shattering the Limit','Shocking Speed','Signature Pose','Solid Support','Soul vs Soul','Speedy Retribution','Strength in Unity','Strongest Clan in Space','Super Saiyan','Super Strike','Super-God Combat','Supreme Power','Supreme Warrior','Tag Team of Terror','Team Bardock','Team Turles','Telekinesis','Telepathy','The First Awakened','The Ginyu Force','The Hera Clan','The Incredible Adventure','The Innocents','The Saiyan Lineage','The Students','The Wall Standing Tall','Thirst for Conquest','Tough as Nails','Tournament of Power','Transform','Turtle School','Twin Terrors','Ultimate Lifeform','Unbreakable Bond','Universe\'s Most Malevolent','Warrior Gods','Warriors of Universe 6','World Tournament Champion','World Tournament Reborn','Xenoverse','Z Fighters']
# Tree strucutre as tuple/list structure - leaf nodes are inputs
tree_struct =   ('unit',
                [
                    ('General',
                    [
                        ('Name', []),('Exclusivity', []),('Class', []),('Type', []),('EZA\'d?',[]),('JP Release Date',[]),('GLB Release Date',[]),('HP',[]),('ATK',[]),('DEF', []),('12 Ki Modifier',[]),('Keep Stacking?',[])
                    ]),
                    ('Leader Skill',
                    [
                        ('Leader Skill Tier (Z-H)', [])
                    ]),
                    ('Categories',
                    [
                        ('DB Saga',[]),('Saiyan Saga', []), ('Planet Namek Saga', []), ('Androids/Cell Saga', []), ('Majin Buu Saga', []), ('Future Saga', []), ('Universe Survival Saga', []), ('Shadow Dragon Saga', []), ('Pure Saiyans', []), ('Hybrid Saiyans', []), ('Earthlings', []), ('Namekians', []), ('Androids', []), ('Artificial Life Forms',[]),('Goku\'s Family',[]),('Vegeta\'s Family', []),('Wicked Bloodline', []),('Youth',[]),('Peppy Gals',[]),('Super Saiyans',[]),('Super Saiyan 2',[]),('Super Saiyan 3',[]),('Power Beyond Super Saiyan',[]),('Fusion',[]),('Potara',[]),('Fused Fighters',[]),('Giant Form',[]),('Transformation Boost',[]),('Power Absorption',[]),('Kamehameha',[]),('Realm of Gods',[]),('Full Power',[]),('Giant Ape Power',[]),('Majin Power',[]),('Powerful Comeback',[]),('Power of Wishes',[]),('Miraculous Awakening',[]),('Corroded Body and Mind',[]),('Rapid Growth',[]),('Mastered Evolution',[]),('Time Limit', []),('Final Trump Card',[]),('Worthy Rivals',[]),('Sworn Enemies',[]),('Joined Forces',[]),('Bond of Parent and Child',[]),('Siblings\' Bond',[]),('Bond of Friendship',[]),('Bond of Master and Disciple',[]),('Ginyu Force',[]),('Team Bardock',[]),('Universe 6',[]),('Representatives of Universe 7',[]),('Universe 11',[]),('GT Heroes',[]),('GT Bosses',[]),('Super Heroes',[]),('Movie Heroes',[]),('Movie Bosses',[]),('Turtle School',[]),('World Tournament',[]),('Earth-Bred Fighters',[]),('Low-Class Warriors',[]),('Gifted Warriors',[]),('Otherworld Warriors',[]),('Resurrected Warriors',[]),('Space-Traveling Warriors',[]),('Time Travelers',[]),('Dragon Ball Seekers',[]),('Storied Figures',[]),('Legendary Existence',[]),('Saviors',[]),('Defenders of Justice',[]),('Revenge',[]),('Target: Goku',[]),('Terrifying Conquerors',[]),('Inhuman Deeds',[]),('Planetary Destruction',[]),('Exploding Rage',[]),('Connected Hope',[]),('Entrusted Will',[]),('All-Out Struggle',[]),('Battle of Wits',[]),('Accelerated Battle',[]),('Battle of Fate',[]),('Heavenly Events',[]),('Special Pose',[]),('Worldwide Choas',[]),('Crossover',[]),('Dragon Ball Heroes',[])
                    ]),
                    ('Links',
                    [#Should make this into a for loop
                        ('Form 1',
                        [
                            ('Link 1', []),('Pr(Link 1 Active)',[]),('Link 2', []),('Pr(Link 2 Active)',[]),('Link 3', []),('Pr(Link 3 Active)',[]),('Link 4', []),('Pr(Link 4 Active)',[]),('Link 5', []),('Pr(Link 5 Active)',[]),('Link 6', []),('Pr(Link 6 Active)',[]),('Link 7', []),('Pr(Link 7 Active)',[])
                        ]),
                        ('Form 2',
                        [
                            ('Link 1', []),('Pr(Link 1 Active)',[]),('Link 2', []),('Pr(Link 2 Active)',[]),('Link 3', []),('Pr(Link 3 Active)',[]),('Link 4', []),('Pr(Link 4 Active)',[]),('Link 5', []),('Pr(Link 5 Active)',[]),('Link 6', []),('Pr(Link 6 Active)',[]),('Link 7', []),('Pr(Link 7 Active)',[])
                        ]),
                        ('Form 3',
                        [
                            ('Link 1', []),('Pr(Link 1 Active)',[]),('Link 2', []),('Pr(Link 2 Active)',[]),('Link 3', []),('Pr(Link 3 Active)',[]),('Link 4', []),('Pr(Link 4 Active)',[]),('Link 5', []),('Pr(Link 5 Active)',[]),('Link 6', []),('Pr(Link 6 Active)',[]),('Link 7', []),('Pr(Link 7 Active)',[])
                        ]),
                        ('Form 4',
                        [
                            ('Link 1', []),('Pr(Link 1 Active)',[]),('Link 2', []),('Pr(Link 2 Active)',[]),('Link 3', []),('Pr(Link 3 Active)',[]),('Link 4', []),('Pr(Link 4 Active)',[]),('Link 5', []),('Pr(Link 5 Active)',[]),('Link 6', []),('Pr(Link 6 Active)',[]),('Link 7', []),('Pr(Link 7 Active)',[])
                        ]),
                        ('Form 5',
                        [
                            ('Link 1', []),('Pr(Link 1 Active)',[]),('Link 2', []),('Pr(Link 2 Active)',[]),('Link 3', []),('Pr(Link 3 Active)',[]),('Link 4', []),('Pr(Link 4 Active)',[]),('Link 5', []),('Pr(Link 5 Active)',[]),('Link 6', []),('Pr(Link 6 Active)',[]),('Link 7', []),('Pr(Link 7 Active)',[])
                        ]),
                    ]
                    )#,
                    #('Super Attacks',
                    #    [('Unit Super Attacks',[])]),
                    #('Stats', [])
                ])
default_inputs = [
                    ['Super Saiyan Goku','DF','Super','STR','No','1/1/2023','1/1/2023','10000','10000','10000','1.5','No'],
                    ['H'],
                    ['No']*numCategories,
                    [ # Want form defaults to be that of the previous form (nice to have)
                        ['Golden Warrior','Default','Saiyan Warrior Race','Default','Super Saiyan','Default','Kamehameha','Default','Prepared for Battle','Default','Fierce Battle','Default','Legendary Power','Default'],
                        ['Golden Warrior','Default','Saiyan Warrior Race','Default','Super Saiyan','Default','Kamehameha','Default','Prepared for Battle','Default','Fierce Battle','Default','Legendary Power','Default'],
                        ['Golden Warrior','Default','Saiyan Warrior Race','Default','Super Saiyan','Default','Kamehameha','Default','Prepared for Battle','Default','Fierce Battle','Default','Legendary Power','Default'],
                        ['Golden Warrior','Default','Saiyan Warrior Race','Default','Super Saiyan','Default','Kamehameha','Default','Prepared for Battle','Default','Fierce Battle','Default','Legendary Power','Default'],
                        ['Golden Warrior','Default','Saiyan Warrior Race','Default','Super Saiyan','Default','Kamehameha','Default','Prepared for Battle','Default','Fierce Battle','Default','Legendary Power','Default']
                    ]
                  ]
data_val_types = [
                    ['None','List','List','List','List','Date','Date','Int','Int','Int','List','List'],
                    ['List'],
                    ['List']*numCategories,
                    [['List']*2*7 for i in range(numFormsMax)]
                ]
data_val_lists = [
                    [None,["DF", "Banner", "DF LR", "Carnival LR", "LR", "Heroes"],['Extreme','Super'],['AGL','INT','PHY','STR','TEQ'],['No','Yes'],None,None,None,None,None,["1.4","1.45","1.5","1.6"],['No','Yes']],
                    [['Z','A','B','C','D','E','F','G','H']],
                    [['No','Yes'] for i in range(numCategories)],
                    [links for i in range(numFormsMax)]
                ]

# Creating application window
app = tk.Tk()
app.title("Dokkan GUI")
app.geometry('400x200')

# Configure the grid layout
app.rowconfigure(0, weight=1)
app.columnconfigure(0, weight=1)

# Create a treeview
tree = ttk.Treeview(app)
tree.heading('#0', text='Unit', anchor=tk.W)

queue = [(tree_struct, ())]
index_dict = {(): tree_struct[0]}
data_dict = {(): tree_struct[0]}
while queue:
    current_node, parent_index = queue.pop(0)
    children = current_node[1]
    for i, child in enumerate(children):
        child_index = parent_index + (i,)
        if child[1]:
            tree.insert(parent_index,tk.END, text=child[0], iid=child_index,open=False)
            queue.append((child, child_index))
            index_dict[child_index] = child
            data_dict[child_index] = child[0]
        else:
            default_input = default_inputs
            data_val_type = data_val_types
            data_val_list = data_val_lists
            for j in child_index:
                default_input = default_input[j]
                data_val_type = data_val_type[j]
                data_val_list = data_val_list[j]
            index_dict[child_index] = [child[0],default_input,data_val_type,data_val_list]
            data_dict[child_index] = [child[0],default_input]

# Bind the function to the Treeview widget
tree.bind("<Button-1>", create_input_boxes)

# place the Treeview widget on the root window
tree.grid(row=0, column=0, sticky=tk.NSEW)

# run the app
app.mainloop()