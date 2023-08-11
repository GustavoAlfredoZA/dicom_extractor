import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os
from explorer import *


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.folder_path = ''
        # Crea un cuadro de texto para mostrar la ruta del directorio seleccionado
        self.tb_path = tk.Entry(textvariable=self.folder_path, width=200)
        self.fsobjects = {}
        self.folder_image = tk.PhotoImage(file='icons/file.png')
        self.folder_image = tk.PhotoImage(file='icons/folder.png')
        self.window1()

    # Define una función que se llama cuando el usuario hace clic en el botón "Browse"
    def browse_button(self):
        # Permite al usuario seleccionar un directorio y lo guarda en la variable global "folder_path"
        self.folder_path.set(filedialog.askdirectory())

    # Define una función que actualiza el cuadro de texto con la ruta del directorio seleccionado
    def update_tb_path(self):
        path = self.folder_path.get()
        self.tb_path.delete(0, tk.END)
        self.tb_path.insert(0, path)
        self.update_tree(path)

    def update_tree(self, path):
        # Elimina todos los nodos del árbol
        self.tree.delete(*self.tree.get_children())
        print(path)
        # Agrega los nodos del árbol
        self.insert_item(self.tree, path)

    # Define una función que crea la ventana principal y los widgets necesarios
    def window1(self):
        # Define una variable llamada "folder_path" y la establece en la ruta actual del directorio de trabajo
        self.folder_path = tk.StringVar(value=os.getcwd())

        # Crea una etiqueta que muestra la ruta actual del directorio de trabajo
        tk.Label(text="Current Directory:").grid(row=0, column=0)
        self.tb_path.grid(row=0, column=1)

        # Crea un botón "Browse" que llama a la función "browse_button" cuando se hace clic en él
        tk.Button(text="Browse", command=self.browse_button).grid(row=0, column=2)

        # Actualiza el cuadro de texto con la ruta del directorio seleccionado por el usuario
        self.folder_path.trace('w', lambda name, index, mode, sv=self.folder_path: self.update_tb_path())

        # Crea una barra lateral con un árbol de directorios
        self.tree = ttk.Treeview(self.master)
        self.tree.grid(row=1, column=, rowspan=5, padx=10, pady=10, sticky='nswe')

        # Agrega las columnas al árbol
        self.tree['columns'] = ('Size', 'Type')

        # Establece las opciones para cada columna
        self.tree.column('#0', width=250, minwidth=250, stretch=tk.YES)
        self.tree.column('Size', width=100, minwidth=100, stretch=tk.NO)
        self.tree.column('Type', width=100, minwidth=100, stretch=tk.NO)

        # Define los encabezados de cada columna
        self.tree.heading('#0', text='Name', anchor=tk.W)
        self.tree.heading('Size', text='Size', anchor=tk.W)
        self.tree.heading('Type', text='Type', anchor=tk.W)

        # Agrega los nodos del árbol
        self.insert_item(self.tree, self.folder_path.get())
        self.children = {}
        self.tree.bind('<<TreeviewOpen>>', self.update_tree)

    def get_icon(self, path):
        """
        Retorna la imagen correspondiente según se especifique
        un archivo o un directorio.
        """
        print(path)
        return self.folder_image if os.path.isdir(path) else self.file_image

    def insert_item(self, name, path, parent=""):
        """
        Añade un archivo o carpeta a la lista y retorna el identificador
        del ítem.
        """
        iid = self.tree.insert(
            parent, tk.END, text=name, tags=("fstag",),
            image=self.get_icon(path))
        self.fsobjects[iid] = path
        return iid

    def load_tree(self, path, parent=""):
        """
        Carga el contenido del directorio especificado y lo añade
        a la lista como ítemes hijos del ítem "parent".
        """
        for fsobj in self.listdir(path):
            fullpath = join(path, fsobj)
            child = self.insert_item(fsobj, fullpath, parent)
            if isdir(fullpath):
                for sub_fsobj in self.listdir(fullpath):
                    self.insert_item(sub_fsobj, join(fullpath, sub_fsobj),
                                     child)


root = tk.Tk()
myapp = App(root)
root.mainloop()
