from tkinter import ttk
import tkinter as tk
import sqlite3

def connect():
    conn = sqlite3.connect("TRIAL.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY, First TEXT, Surname TEXT)")
    conn.commit()
    conn.close()


def Insert():
    conn = sqlite3.connect("TRIAL.db")
    cur = conn.cursor()
    data = (first_text.get(), surname_text.get())
    # insert data in db
    cur.execute("INSERT INTO profile (First, Surname) VALUES(?, ?)", data)  
    conn.commit()
    # insert data in treeview
    tree.insert('', tk.END, values=(str(cur.lastrowid),) + data)  
    conn.close()


connect()  #  this to create the db

root = tk.Tk()
root.geometry("400x400")

tree = ttk.Treeview(root, column=("column1", "column2", "column3"), show='headings')
tree.heading("#1", text="NUMBER")
tree.heading("#2", text="FIRST NAME")
tree.heading("#3", text="SURNAME")
tree.pack()

first_text = tk.StringVar()
e1 = tk.Entry(root, textvariable=first_text)
e1.pack()
surname_text = tk.StringVar()
e2 = tk.Entry(root, textvariable=surname_text)
e2.pack()

b1 = tk.Button(text="add data", command=Insert)
b1.pack(side=tk.BOTTOM)

root.mainloop()