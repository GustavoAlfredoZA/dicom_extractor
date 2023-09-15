import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory
from tkinter import messagebox
from PIL import Image, ImageTk
import os, sys
#yyimport math
import numpy as np
import pydicom as dicom
from zoom import AutoScrollbar, CanvasImage
#import cv2
#import imageio
#from skimage import data, img_as_float
from skimage import exposure
#import matplotlib.pyplot as plt
from sklearn import preprocessing as pre
import nibabel as nib


from os.path import sep, join

def sep(path: str, delimiter : str = '/') -> str:
    if delimiter == '\\':
        aux_delimiter = '/'
    else:
        aux_delimiter = '\\'
    return path.replace(aux_delimiter, delimiter)

class FileBrowserGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("File Browser")
        
        ############# Variables #############
        self.size = tk.IntVar()
        self.size.set(512)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(self.master, textvariable=self.path_var, width= 50)
        
        self.contrast_var = tk.IntVar()
        self.slope_var = tk.DoubleVar()
        self.intercept_var = tk.DoubleVar()
        

        self.file_index = 0
        self.list_files = []
        self.aux_path = ''
        
        self.bs_var = tk.StringVar()
        self.bg_var = tk.StringVar()
        self.lv_var = tk.StringVar()
        self.radio_var = tk.IntVar()

        self.output_path_var = tk.StringVar()
        self.prev_output_path_var = tk.StringVar()
        
        bs_selected_file = 'icons/button_brainstem_selected.png'
        bg_selected_file = 'icons/button_basal-ganglia_selected.png'
        lv_selected_file = 'icons/button_lateral-ventricles_selected.png'
        bs_file = 'icons/button_brainstem.png'
        bg_file = 'icons/button_basal-ganglia.png'
        lv_file = 'icons/button_lateral-ventricles.png'
        self.log_file = './log.txt'

        """ for pyinstaller """
        bs_selected_file = sep(os.path.join(os.path.dirname(sys.executable),bs_selected_file))
        bg_selected_file = sep(os.path.join(os.path.dirname(sys.executable),bg_selected_file))
        lv_selected_file = sep(os.path.join(os.path.dirname(sys.executable),lv_selected_file))
        bs_file = sep(os.path.join(os.path.dirname(sys.executable),bs_file))
        bg_file = sep(os.path.join(os.path.dirname(sys.executable),bg_file))
        lv_file = sep(os.path.join(os.path.dirname(sys.executable),lv_file))
        self.log_file = sep(os.path.join(os.path.dirname(sys.executable),self.log_file))

        log = open(self.log_file, 'a+')
        log.write('Starting program\n')
        log.close()

        ############# Input #############
        self.browse_button = ttk.Button(self.master, text="Browse input", command=self.browse_files)
        self.tree = ttk.Treeview(self.master)
        self.tree.bind("<Double-1>", self.tree_double_click)
        self.image_frame = ttk.Frame(self.master, width = 200, height = 200)
        
        ############# Output #############
        self.path_entry_output = ttk.Entry(self.master, textvariable=self.output_path_var, width= 50)
        self.browse_button_output = ttk.Button(self.master, text="Browse output", command=self.browse_button_output_click)
        self.prev_path_label = ttk.Label(self.master, textvariable=self.prev_output_path_var)
                
        ############# Images #############
        bs_selected_path = Image.open(bs_selected_file).resize((160,40))
        bg_selected_path = Image.open(bg_selected_file).resize((160,40))
        lv_selected_path = Image.open(lv_selected_file).resize((160,40))
        bs_path = Image.open(bs_file).resize((160,40))
        bg_path = Image.open(bg_file).resize((160,40))
        lv_path = Image.open(lv_file).resize((160,40))

        self.bs_selected_b_i = ImageTk.PhotoImage(bs_selected_path)
        self.bg_selected_b_i = ImageTk.PhotoImage(bg_selected_path)
        self.lv_selected_b_i = ImageTk.PhotoImage(lv_selected_path)
        self.bs_b_i = ImageTk.PhotoImage(bs_path)
        self.bg_b_i = ImageTk.PhotoImage(bg_path)
        self.lv_b_i = ImageTk.PhotoImage(lv_path)
        
        ############# Selection #############
        self.selection_frame = tk.Canvas(self.master, border=0,relief='solid',height=100)
        self.bs_selection_button = ttk.Label(self.selection_frame, image=self.bs_b_i)
        self.bg_selection_button = ttk.Label(self.selection_frame, image=self.bg_b_i)
        self.lv_selection_button = ttk.Label(self.selection_frame, image=self.lv_b_i)
        
        self.bs_selection_button.bind("<Button-1>", self.bs_button_click)
        self.bg_selection_button.bind("<Button-1>", self.bg_button_click)
        self.lv_selection_button.bind("<Button-1>", self.lv_button_click)
        
        ############# Navigation #############
        self.navigation_frame = ttk.Frame(self.master, height=100)
        next_button = ttk.Button(self.navigation_frame, text="Next", command = self.next_button_click)
        prev_button = ttk.Button(self.navigation_frame, text="Previous", command = self.prev_button_click)
        self.save_button = ttk.Button(self.navigation_frame, text="Save", command = self.save_button_click,state='disabled')

        self.gallery_buttons_frame = ttk.Frame(self.master, border=5,relief='solid',height=100)  
        self.prev_gallery_button = ttk.Button(self.gallery_buttons_frame, text="^", command = self.prev_gallery_button_click, state='disabled')
        self.next_gallery_button = ttk.Button(self.gallery_buttons_frame, text="v", command = self.next_gallery_button_click, state='disabled')
        
        self.gallery_frame = ttk.Frame(self.master, border=5,relief='solid',height=100)
        self.gallery_frame.config(height=100)
        self.gallery_frame_vbar1 = ttk.Scrollbar(self.gallery_frame, orient='vertical', command=self.gallery_scroll)
        self.gallery_frame_vbar = ttk.Scrollbar(self.gallery_frame, orient='vertical', command=self.gallery_scroll)
        self.gallery_frame_vbar.grid(row=0, column=1, sticky='ns')
        self.gallery_canvas = tk.Canvas(self.gallery_frame,
                                yscrollcommand=self.gallery_frame_vbar.set,width=100, height=100)
        self.gallery_canvas.grid(row=0, column=0, sticky='nswe',padx=(50,50), ipadx=10, pady=0, ipady=0)
        self.gallery_canvas.update()
        self.gallery_frame_vbar.configure(command=self.gallery_canvas.yview)
        
        ############# Labels #############
        self.radio_button_frame = ttk.Frame(self.master, border=5,relief='solid',height=100)
        self.h_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Hemorrhage", variable=self.radio_var, value=1)
        self.n_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Normal", variable=self.radio_var, value=2)
        self.i_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Isquemic", variable=self.radio_var, value=3)
        self.u_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Unknown", variable=self.radio_var, value=4)
        
        ############# Settings #############
        self.settings_frame = ttk.Frame(self.master, height=100)
        self.size_label = ttk.Label(self.settings_frame, text="Size = " )
        self.size_entry = ttk.Entry(self.settings_frame, textvariable=self.size)
        self.o_c_radio_button = ttk.Radiobutton(self.settings_frame, text="Original", variable=self.contrast_var, value=0)
        #self.s_c_radio_button = ttk.Radiobutton(self.settings_frame, text="Contrast stretching", variable=self.contrast_var, value=1)
        self.e_c_radio_button = ttk.Radiobutton(self.settings_frame, text="Histogram equalization", variable=self.contrast_var, value=2)
        #self.a_c_radio_button = ttk.Radiobutton(self.settings_frame, text="Adaptive equaliztion", variable=self.contrast_var, value=3)
        self.size_update_button = ttk.Button(self.settings_frame, text="Update", command=self.update_size)

        ############# Layout #############
        self.path_entry.grid(row=0, column=0, sticky="e", padx=(10,0))
        self.browse_button.grid(row=0, column=1, sticky="w", padx=(1, 50))
        self.tree.grid(row=1, column=0, sticky="nsew",padx=50)
        self.image_frame.grid(row=1, column=1, sticky="nsew", columnspan= 3, padx=50,pady=0, ipadx=1, ipady=0)

        self.path_entry_output.grid(row=4,column=0, sticky="e", padx=(10,0))
        self.browse_button_output.grid(row=4, column=1, sticky="w", padx=(1, 50))
        self.prev_path_label.grid(row=5, column = 0, sticky="we")

        ############# Layout Selection #############
        self.selection_frame.grid(row=2, column=1, sticky="we", columnspan=2,ipadx=60, ipady=10)
        self.bs_selection_button.grid(row=0, column=0, sticky="we")
        self.bg_selection_button.grid(row=0, column=1, sticky="we",padx=50)
        self.lv_selection_button.grid(row=0, column=2, sticky="we")
        self.selection_frame.columnconfigure(0, weight=1)
        self.selection_frame.columnconfigure(1, weight=1)
        self.selection_frame.columnconfigure(2, weight=1)

        ############# Layout Navigation #############
        self.navigation_frame.grid(row = 3, column=1, sticky="we", columnspan=2, ipady=10)
        next_button.grid(row=0, column=2, sticky="w")
        self.save_button.grid(row=0, column=1, sticky="we")
        prev_button.grid(row=0, column=0, sticky="e")
        
        self.gallery_buttons_frame.grid(row=2, column=4, sticky="nswe", columnspan=1, padx=50, pady=0)
        self.next_gallery_button.grid(row=0, column=1, sticky="e")
        self.prev_gallery_button.grid(row=0, column=0, sticky="w")

        self.gallery_frame.grid(row=1, column=4,sticky='nswe', padx=5,pady=0, ipadx=5, ipady=0)
        
        self.gallery_frame.rowconfigure(0, weight=1)
        self.gallery_frame.columnconfigure(0, weight=1)
        
        ############## Layout set label #############
        self.radio_button_frame.grid(row=4, column=2, sticky="nw", rowspan=2, columnspan=1)
        self.h_radio_button.grid(row=0, column=0, sticky="we")#, ipadx=25, ipady=20)
        self.n_radio_button.grid(row=1, column=1, sticky="we")#, ipadx=25, ipady=20)
        self.i_radio_button.grid(row=0, column=1, sticky="we")#, ipadx=25, ipady=20)
        self.u_radio_button.grid(row=1, column=0, sticky="we")#, ipadx=25, ipady=20)

        ############# Layout Settings #############
        self.settings_frame.grid(row=3, column=4, sticky="nswe", columnspan=1, rowspan=4, padx=50, pady=0)
        self.size_label.grid(row=0, column=0, sticky="w")
        self.size_entry.grid(row=0, column=1, sticky="we")
        #self.slope_entry.grid(row=1, column=1, sticky="we")
        #self.slope_label.grid(row=1, column=0, sticky="w")
        #self.intercept_entry.grid(row=2, column=1, sticky="we")
        #self.intercept_label.grid(row=2, column=0, sticky="w")
        self.o_c_radio_button.grid(row=1, column=0, sticky="w")
        #self.s_c_radio_button.grid(row=2, column=0, sticky="w")
        self.e_c_radio_button.grid(row=3, column=0, sticky="w")
        #self.a_c_radio_button.grid(row=4, column=0, sticky="w")
        #self.contrast_entry.grid(row=3, column=1, sticky="we")
        #self.contrast_label.grid(row=3, column=0, sticky="w")
        self.size_update_button.grid(row=5, column=0, sticky="w")

        ############# Grid #############
        self.master.grid_columnconfigure(0,weight=1)
        self.master.grid_columnconfigure(1,weight=1)
        self.master.grid_columnconfigure(2,weight=1)
        self.master.grid_columnconfigure(3,weight=1)
        self.master.grid_columnconfigure(4,weight=1)
        self.master.grid_rowconfigure(0,weight=1)
        self.master.grid_rowconfigure(1,weight=1)
        self.master.grid_rowconfigure(2,weight=1)
        self.master.grid_rowconfigure(3,weight=1)
        self.master.grid_rowconfigure(4,weight=1)
        self.master.grid_rowconfigure(5,weight=1)
        self.master.grid_rowconfigure(6,weight=1)

        self.gallery_buttons_frame.grid_columnconfigure(0,weight=1)
        self.gallery_buttons_frame.grid_columnconfigure(1,weight=1)
        self.gallery_buttons_frame.grid_columnconfigure(2,weight=1)
        self.gallery_buttons_frame.grid_columnconfigure(3,weight=1)

        self.navigation_frame.grid_columnconfigure(0,weight=1)
        self.navigation_frame.grid_columnconfigure(1,weight=1)
        self.navigation_frame.grid_columnconfigure(2,weight=1)
        
        ############# Var Setup #############
        self.bs_var.set('')
        self.bg_var.set('')
        self.lv_var.set('')
        
        self.prev_image = ''
        self.actual_image = ''
        self.prev_dir = ''
        self.output_path_var.set('')
        self.prev_output_path_var.set('')

        
        self.gallery_index = 0
        self.prev_gallery_button.config(state='disabled')
        self.max_gallery_index = 0

        # Set up treeview columns
        self.path_entry.delete(0, tk.END)
        self.path_var.set(sep(os.getcwd()))

        self.radio_var.set(0)
        
        # Populate treeview with root directory
        root_node = self.tree.insert("", "end", text=os.getcwd())
        self.populate_tree(root_node)
        self.delimiter = '/'
        
        ############# Bindings #############
        self.master.bind("s", self.save_button_click)
        self.master.bind("<Right>", self.next_button_click)
        self.master.bind("<Left>", self.prev_button_click)
        self.master.bind("<Up>", self.prev_gallery_button_click)
        self.master.bind("<Down>", self.next_gallery_button_click)
        self.master.bind("1", self.bs_button_click)
        self.master.bind("2", self.bg_button_click)
        self.master.bind("3", self.lv_button_click)
        self.master.bind("h", lambda event: self.radio_var.set(1))
        self.master.bind("n", lambda event: self.radio_var.set(2))
        self.master.bind("i", lambda event: self.radio_var.set(3))
        self.master.bind("u", lambda event: self.radio_var.set(4))
        self.master.bind("o", self.browse_files)
        self.master.bind("b", self.browse_button_output_click)
        self.master.bind("<Escape>", self.reset)
    
    def populate_tree(self, parent, full_path:str=None):
        # Get subdirectories of parent directory
        try:
            path = self.tree.item(parent, "text")
            if full_path is None and os.path.isdir(path):
                directory_list = os.listdir(path)
            elif os.path.isdir(full_path):
                directory_list = os.listdir(full_path)
            else: 
                directory_list = []
            if full_path is None:
                full_path = path
            ic_var = False
            for directory in directory_list:
                ic_var = False
                d_full_path = sep(os.path.join(full_path, directory))
                if os.path.isdir(d_full_path):
                    node = self.tree.insert(parent, "end", text=directory,value=d_full_path)
                    ic_var = self.populate_tree(node, d_full_path)
                    sub_f = [f for f in os.listdir(d_full_path) if os.path.isdir(os.path.join(d_full_path, f))]
                    image_files = [f for f in os.listdir(d_full_path) if os.path.isfile(os.path.join(d_full_path, f)) and f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".dcm",".nii", ".nii.gz" ))]
                    nii_files = [f for f in os.listdir(d_full_path) if os.path.isfile(os.path.join(d_full_path, f)) and f.lower().endswith((".nii", ".nii.gz" ))]
                    if len(image_files)>0:
                        ic_var = True
                    if (not(ic_var)  ) or (len(sub_f)==0 and len(image_files)==0):
                        self.tree.delete(node)
                    for ni in nii_files:
                        n = self.tree.insert(node, "end", text=ni,value=sep(os.path.join(d_full_path, ni)))
            return ic_var
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
                
    def browse_files(self, event=None):
        try:
            directory = askdirectory()
            self.path_var.set(directory)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)
            if directory:
                for item in self.tree.get_children():
                    self.tree.delete(item)
                root_node = self.tree.insert("", "end", text=directory,value=directory)
                self.populate_tree(root_node)
            else:
                messagebox.showerror("Error", "Invalid path")
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def tree_double_click(self, event):
        try:
            item = self.tree.selection()[0]
            path = ' '.join(self.tree.item(item, "value"))
            if os.path.isdir(path) or '.nii' in path:
                # Update directory size in treeview
                self.tree.set(item)

                # Clear image frame
                
                for widget in self.image_frame.winfo_children():
                    widget.destroy()
                # Populate image frame with images from selected directory
                self.aux_path = path
                self.populate_images(path)
                self.manage_gallery()
                self.bs_var.set('')
                self.bg_var.set('')
                self.lv_var.set('')
                self.prev_image = ''
                self.bs_selection_button.config(image=self.bs_b_i)
                self.bg_selection_button.config(image=self.bg_b_i)
                self.lv_selection_button.config(image=self.lv_b_i)
                self.save_button.config(state=tk.DISABLED)
                self.reset()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
  
    def browse_button_output_click(self,event=None):
        try:
            directory = askdirectory()
            self.output_path_var.set(directory)
            self.path_entry_output.delete(0, tk.END)
            self.path_entry_output.insert(0, directory)
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def reset(self,event=None):
        try:
            self.bs_var.set('')
            self.bg_var.set('')
            self.lv_var.set('')

            self.file_index = 0
            self.gallery_index = 0
            
            self.prev_image = ''
            self.actual_image = ''
            self.prev_dir = ''
            #self.output_path_var.set('')
            #self.prev_output_path_var.set('')
            
            #self.max_gallery_index = 0

            self.slope_var.set(1)
            self.intercept_var.set(1)

            self.bs_selection_button.config(image=self.bs_b_i)
            self.bg_selection_button.config(image=self.bg_b_i)
            self.lv_selection_button.config(image=self.lv_b_i)


            # Set up treeview columns
            #self.path_entry.delete(0, tk.END)
            #self.path_var.set(sep(os.getcwd()))

            #self.radio_var.set(0)
            
            # Populate treeview with root directory
            #root_node = self.tree.insert("", "end", text=os.getcwd())
            #self.populate_tree(root_node)
            #self.delimiter = '/'
            self.save_button.config(state='disabled')
            
            self.contrast_var.set(0)
            self.slope_var.set(1)
            self.intercept_var.set(1)
            self.manage_images()
            self.manage_gallery()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def save_button_click(self,event=None):
        """
        Hemorrhage self.radio_var = 1, folder = 'H'
        Normal self.radio_var = 2, folder = 'N'
        Isquemic self.radio_var = 3, folder = 'I'
        Unknown self.radio_var = 4, folder = 'U'
        """
        try:
            self.log_file.write('Saving\n')
            if self.save_button['state'] != 'normal':
                return
            if (self.radio_var.get() == 0):
                messagebox.showerror("Error", "First select if the set of images are Ischemia, normal, hemorrhage or unknown.")
                return
            if (self.output_path_var.get() == '') or not(os.path.isdir(self.output_path_var.get())):
                messagebox.showerror("Error", "Select a valid output folder")
                return
            else:
                folder = ['H','N','I','U'][self.radio_var.get()-1]
                full_folder =  self.output_path_var.get()+'/'+folder
                folders = os.listdir(self.output_path_var.get())
                if not(folder in folders) or not(os.path.isdir(full_folder)):
                    os.makedirs(full_folder)
                list_full_folder = os.listdir(full_folder)
                list_full_folder =  [int('0'.join(filter(str.isdigit, s))) for s in list_full_folder]
                if len(list_full_folder) == 0:
                    output_path = full_folder+'/0/'
                else:
                    output_path = full_folder+'/'+str(list_full_folder[-1]+1)+'/'
                os.makedirs(output_path)
                bs = int(self.bs_var.get())
                bg = int(self.bg_var.get())    
                lv = int(self.lv_var.get())

                bs_path = sep(os.path.join(self.aux_path, self.list_files[bs%len(self.list_files)]))
                bg_path = sep(os.path.join(self.aux_path, self.list_files[bg%len(self.list_files)]))
                lv_path = sep(os.path.join(self.aux_path, self.list_files[lv%len(self.list_files)]))

                image_list = [bs_path, bg_path, lv_path]
                image_list_i = [bs, bg, lv]
                for i,f in enumerate(image_list):
                    if '.nii' in f:
                        image = self.nii_image.get_fdata()[:,:,image_list_i[i]]
                        image = pre.MinMaxScaler((0,255)).fit_transform(image)
                        image = np.rot90(image, 1)
                        image = Image.fromarray(image)
                    if '.dcm' in f:
                        output_image = self.dcm_image(f)
                        image = Image.fromarray(output_image)        
                    else:
                        image = Image.open(f)
                    image.thumbnail((int(self.size.get()), int(self.size.get())))
                    image.convert('L').save(output_path+str(i)+'.jpg')
                self.prev_output_path_var.set('Previous set saved in '+output_path)
                self.reset()
        except Exception as e:
            messagebox.showerror("Error", "Error")
            self.log_file.write('Error\n'+ str(e))
            self.log_file.close()
    
    def bs_button_click(self, event):
        try:
            if self.bs_var.get() != '' and self.file_index != int(self.bs_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Brain Stem? ")
                if r:
                    self.bs_var.set('')
                    self.bs_selection_button.config(image=self.bs_b_i)
                else:
                    return None
            if self.bg_var.get() != '' and self.file_index == int(self.bg_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Basal Ganglia? ")
                if r:
                    self.bg_button_click(event)
                else:
                    return None
            if self.lv_var.get() != '' and self.file_index == int(self.lv_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Lateral Ventricles? ")
                if r:
                    self.lv_button_click(event)
                else:
                    return None
            
            
            if self.bs_var.get() == '':
                self.bs_var.set(self.file_index)
                self.bs_selection_button.config(image=self.bs_selected_b_i)
                self.manage_images()
                self.manage_gallery()
                if self.bg_var.get() != '' and self.lv_var.get() != '':
                    self.save_button.config(state='normal')    
            else:
                if self.file_index == int(self.bs_var.get()):
                    self.bs_var.set('')
                    self.manage_images()
                self.bs_var.set('')
                self.manage_gallery()
                self.bs_selection_button.config(image=self.bs_b_i)
                self.save_button.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
              
    def bg_button_click(self, event):
        try:
            if self.bg_var.get() != '' and self.file_index != int(self.bg_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Basal Ganglia? ")
                if r:
                    self.bg_var.set('')
                    self.bg_selection_button.config(image=self.bg_b_i)
                else:
                    return None
            if self.bs_var.get() != '' and self.file_index == int(self.bs_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Brainstem? ")
                if r:
                    self.bs_button_click(event)
                else:
                    return None
            if self.lv_var.get() != '' and self.file_index == int(self.lv_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Lateral Ventricles? ")
                if r:
                    self.lv_button_click(event)
                else:
                    return None
            
            if self.bg_var.get() == '':
                self.bg_var.set(self.file_index)
                self.bg_selection_button.config(image=self.bg_selected_b_i)
                self.manage_images()
                self.manage_gallery()
                if self.bs_var.get() != '' and self.lv_var.get() != '':
                    self.save_button.config(state='normal')
            else:
                if self.file_index == int(self.bg_var.get()):
                    self.bg_var.set('')
                    self.manage_images()
                self.bg_var.set('')
                self.manage_gallery()
                self.bg_selection_button.config(image=self.bg_b_i)
                self.save_button.config(state='disabled')          
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def lv_button_click(self, event):
        try:
            if self.lv_var.get() != '' and self.file_index != int(self.lv_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Lateral Ventricles? ")
                if r:
                    self.lv_var.set('')
                    self.lv_selection_button.config(image=self.lv_b_i)
                else:
                    return None
            if self.bs_var.get() != '' and self.file_index == int(self.bs_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Brainstem? ")
                if r:
                    self.bs_button_click(event)
                else:
                    return None
            if self.bg_var.get() != '' and self.file_index == int(self.bg_var.get()):
                r = messagebox.askyesno("Update", "Do you want to update the image of Basal Ganglia? ")
                if r:
                    self.bg_button_click(event)
                else:
                    return None

            if self.lv_var.get() == '':
                self.lv_var.set(self.file_index)
                self.lv_selection_button.config(image=self.lv_selected_b_i)
                self.manage_images()
                self.manage_gallery()
                #self.image_frame.config(bg='green')
                if self.bs_var.get() != '' and self.bg_var.get() != '':
                    self.save_button.config(state='normal')
            else:
                if self.file_index == int(self.lv_var.get()):
                    self.lv_var.set('')
                    self.manage_images()
                self.lv_var.set('')
                self.manage_gallery()
                self.lv_selection_button.config(image=self.lv_b_i)
                self.save_button.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def next_button_click(self,event=None):
        try:
            self.file_index += 1
            if self.file_index >= len(self.list_files):
                self.file_index = 0
            self.manage_images()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def prev_button_click(self,event=None):
        try:
            self.file_index -= 1
            if self.file_index <= -1:
                self.file_index = len(self.list_files) -1
            self.manage_images()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def next_gallery_button_click(self,event=None):
        try:
            if self.gallery_index == 0:
                self.prev_gallery_button.config(state='normal')
            self.gallery_index += 1
            if self.gallery_index >= self.max_gallery_index:
                self.gallery_index = self.max_gallery_index
                self.next_gallery_button.config(state='disabled')       
            self.manage_gallery()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
    
    def prev_gallery_button_click(self,event=None):
        try:
            if self.max_gallery_index != 0:
                self.next_gallery_button.config(state='normal')
            self.gallery_index -= 1
            if self.gallery_index <= 1:
                self.gallery_index = 0
                self.prev_gallery_button.config(state='disabled')
            self.manage_gallery()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def populate_images(self, path):
        # Get image files in directory
        # (0020, 0013) Instance Number                     IS: '29'
        try:
            if '.nii' in self.aux_path:
                self.nii_image = nib.load(self.aux_path)
                nii_image = self.nii_image.get_fdata()
                self.max_gallery_index = nii_image.shape[2] // 9
                if self.max_gallery_index != 0:
                    self.next_gallery_button.config(state='normal')
                self.file_index = 0
                self.list_files = [i for i in range(nii_image.shape[2])]
                return

            image_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".dcm" ))]
            
            if len(image_files) == 0:
                messagebox.showerror("Error", "No images in directory")
                return
            
            
            d_files = []
            for f in image_files:
                full_path = os.path.join(path, f)
                if '\\' in full_path:
                    full_path = sep(full_path)
                try:
                    ds = dicom.dcmread(full_path)
                    n = ds.InstanceNumber
                except:
                    n = int(''.join(filter(str.isdigit, '0'+f)))
                d_files.append([f,n])
            
            
            
            image_files = sorted(d_files, key=lambda  t:t[1])
            image_files = [s[0] for s in image_files]

            # Populate image frame with images
            self.list_files = image_files

            self.max_gallery_index = len(image_files) // 9
            if self.max_gallery_index != 0:
                self.next_gallery_button.config(state='normal')
            
            self.file_index = 0
            
            full_path = os.path.join(path, image_files[0])
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def update_size(self):
        try:
            self.size.set(self.size_entry.get())
            self.image_frame.config(width=self.size.get(), height=self.size.get())
            self.manage_images()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def get_first_of_dicom_field_as_int(self, x):
        #get x[0] as in int is x is a 'pydicom.multival.MultiValue', otherwise get int(x)
        try:
            if type(x) == dicom.multival.MultiValue: 
                return int(x[0])
            else: 
                return int(x)
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def window_image(self, img, window_center,window_width, intercept, slope, rescale=True):
        try:
            img = (img*slope +intercept) #for translation adjustments given in the dicom file. 
            img_min = window_center - window_width//2 #minimum HU level
            img_max = window_center + window_width//2 #maximum HU level
            img[img<img_min] = img_min #set img_min for all HU levels less than minimum HU level
            img[img>img_max] = img_max #set img_max for all HU levels higher than maximum HU level
            if rescale: 
                img = (img - img_min) / (img_max - img_min)*255.0 
            return img
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def get_windowing(self,data):
        try:
            log = open(self.log_file, 'a+')
            log.write(f'get_windowing \n')
            log.close()
            try:
                dicom_fields = [data[('0028','1050')].value, #window center
                                data[('0028','1051')].value, #window width
                                data[('0028','1052')].value, #intercept
                                data[('0028','1053')].value] #slope
            except:
                dicom_fields = [40.0, #window center
                                100.0, #window width
                                -1024.0, #intercept
                                1] #slope
                log = open(self.log_file, 'a+')
                log.write(f'finish get windowing {data}\n')
                log.close()
                return dicom_fields
            log = open(self.log_file, 'a+')
            log.write(f'finish get windowing {data}\n')
            log.close()
            return [self.get_first_of_dicom_field_as_int(x) for x in dicom_fields]
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
    
    def dcm_image(self, full_path):
        
        if '\\' in full_path:
            full_path = sep(full_path)
        print('dcm_image')            
        ds = dicom.dcmread(full_path)
        log = open(self.log_file, 'a+')
        log.write('dcm_image\n'+str(full_path)+ '\n')
        log.close()
        #print(ds)
        
        image = ds.pixel_array
        log = open(self.log_file, 'a+')
        log.write(f'dcm_image pixel array\n')
        log.close()
        window_center , window_width, intercept, slope = self.get_windowing(ds)
        log = open(self.log_file, 'a+')
        log.write(f'dcm_image\n {str(window_center)} {str(window_width)} {str(intercept)} {str(slope)}')
        log.close()
        output = self.window_image(image, window_center, window_width, intercept, slope, rescale = False)
        log = open(self.log_file, 'a+')
        log.write(f'dcm_image\n{output}\n')
        log.close()
        #print(ds)
        
        contrast = self.contrast_var.get()
        if contrast == 1:
            p2, p98 = np.percentile(output, (10, 90))
            output = exposure.rescale_intensity(output, in_range=(p2, p98))
            log = open(self.log_file, 'a+')
            log.write(f'dcm contrast 1 {output}\n')
            log.close()
        elif contrast == 2:
            output = pre.MinMaxScaler().fit_transform(output)
            output = exposure.equalize_hist(output)   
            log = open(self.log_file, 'a+')
            log.write(f'dcm contrast 2 {output}\n')
            log.close()
        output = pre.MinMaxScaler((0,255)).fit_transform(output)

        #ds = dicom.dcmread(full_path)
        log = open(self.log_file, 'a+')
        log.write(f'Final dcm {output}\n')
        log.close()
        return output
        
    def manage_images(self):
        # Get image files in directory
        # Populate image frame with images
        # clear image frame

        try:
            self.prev_image = self.actual_image
            log = open(self.log_file, 'a+')
            log.write('Manage_images Actual_image\n'+str(self.actual_image)+','+ str(self.file_index)+ '\n')
            log.close()
            
            bs, bg, lv = -1, -1, -1
            if self.bs_var.get() != '': 
                bs = int(self.bs_var.get())
            if self.bg_var.get() != '': 
                bg = int(self.bg_var.get())    
            if self.lv_var.get() != '': 
                lv = int(self.lv_var.get())
            
            for widget in self.image_frame.winfo_children():
                widget.destroy()        
            log = open(self.log_file, 'a+')
            log.write('Manage_images before image\n')
            log.close()
            if not '.nii' in self.aux_path:
                full_path = sep(os.path.join(self.aux_path, self.list_files[self.file_index%len(self.list_files)]))
                self.actual_image = full_path
            if '.nii' in self.aux_path:
                image = self.nii_image.get_fdata()[:,:,self.file_index]
                image = pre.MinMaxScaler((0,255)).fit_transform(image)
                image = np.rot90(image, 1)
                image = Image.fromarray(image)
            elif '.dcm' in full_path:
                output_image = self.dcm_image(full_path)
                image = Image.fromarray(output_image)           
            else:
                image = Image.open(full_path)
            image = image.convert('HSV')
            log = open(self.log_file, 'a+')
            log.write('manage\n'+str(full_path)+ '\n')
            log.close()

            image.thumbnail((int(self.size.get()), int(self.size.get())), Image.Resampling.LANCZOS)
            
            canva_height = image.size[0]+10
            canva_width = image.size[1]+10
            if self.file_index == bs:
                new_im = Image.new("RGB", (canva_height,canva_width),'purple')
                box = tuple((n - o) // 2 for n, o in zip((canva_height+10,canva_width+10), (canva_height,canva_width)))
                new_im.paste(image, box)
                image = new_im
            elif self.file_index == bg:
                new_im = Image.new("RGB", (canva_height,canva_width),'orange')
                box = tuple((n - o) // 2 for n, o in zip((canva_height+10,canva_width+10), (canva_height,canva_width)))
                new_im.paste(image, box)
                image = new_im
            elif self.file_index == lv:
                new_im = Image.new("RGB", (canva_height,canva_width),'green')
                box = tuple((n - o) // 2 for n, o in zip((canva_height+10,canva_width+10), (canva_height,canva_width)))
                new_im.paste(image, box)
                image = new_im
            
            canvas = CanvasImage(self.image_frame,image, size= int(self.size.get()), )  # create widget
            canvas.grid(row=0, column=0)  # show widget
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
             
    def gallery_scroll(self, event):
        try:
            print(event)
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
    
    def gallery_click(self, event, index):
        try:
            self.file_index = index
            self.manage_images()
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()

    def manage_gallery(self):
        try:
            log = open(self.log_file, 'a+')
            log.write('Actual_image\n'+'Manage_gallery'+str(self.list_files)+','+ str(self.gallery_index)+ '\n')
            log.close()
            for widget in self.gallery_canvas.winfo_children():
                widget.destroy()
            
            start_index = self.gallery_index*9
            sublist = self.list_files[start_index:min(start_index+9, len(self.list_files))]
            row = 0

            bs, bg, lv = -1, -1, -1
            if self.bs_var.get() != '':
                bs = int(self.bs_var.get())
            if self.bg_var.get() != '':
                bg = int(self.bg_var.get())    
            if self.lv_var.get() != '':
                lv = int(self.lv_var.get())
            
            log = open(self.log_file, 'a+')
            log.write(f"Manage_gallery before for {str(','.join(sublist))}\n")
            log.close()
            for i, path in enumerate(sublist):
                full_path = sep(os.path.join(self.aux_path, str(path)))
                if '.nii' in self.aux_path:
                    image = self.nii_image.get_fdata()[:,:,i+start_index]
                    image = pre.MinMaxScaler((0,255)).fit_transform(image)
                    image = np.rot90(image, 1)
                    image = Image.fromarray(image)
                elif '.dcm' in full_path:
                    output_image = self.dcm_image(full_path)
                    image = Image.fromarray(output_image)   
                else:
                    image = Image.open(full_path)
                image.thumbnail((100, 100))

                log = open(self.log_file, 'a+')
                log.write('manage_gallery full_path\n'+str(full_path)+ '\n')
                log.close()
                
                canva_height = image.size[0]+10
                canva_width = image.size[1]+10
                if i+start_index == bs:
                    new_im = Image.new("RGB", (canva_height,canva_width),'purple')
                    box = tuple((n - o) // 2 for n, o in zip((canva_height+10,canva_width+10), (canva_height,canva_width)))
                    new_im.paste(image, box)
                    image = new_im
                elif i+start_index == bg:
                    new_im = Image.new("RGB", (canva_height,canva_width),'orange')
                    box = tuple((n - o) // 2 for n, o in zip((canva_height+10,canva_width+10), (canva_height,canva_width)))
                    new_im.paste(image, box)
                    image = new_im
                elif i+start_index == lv:
                    new_im = Image.new("RGB", (canva_height,canva_width),'green')
                    box = tuple((n - o) // 2 for n, o in zip((canva_height+10,canva_width+10), (canva_height,canva_width)))
                    new_im.paste(image, box)
                    image = new_im
                
                photo = ImageTk.PhotoImage(image)
                label = ttk.Label(self.gallery_canvas, image=photo)
                label.bind("<Button-1>", lambda event, index=start_index+i: self.gallery_click(event, index))
                label.image = photo
                label.grid(row=row, column=i%3, padx=5, pady=5)
                
            
                if i%3 == 2:
                    row += 1
                #print(i,self.gallery_canvas.winfo_children())
                #print(self.gallery_canvas.winfo_children()[i])
        except Exception as e:
            messagebox.showerror("Error", "Error\n"+ str(e))
            log = open(self.log_file, 'a+')
            log.write('Error\n'+ str(e))
            log.close()
            
              
if __name__ == "__main__":
    root = tk.Tk()
    width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.maxsize(width, height)
    root.geometry('%dx%d+0+0' % (width,height))
    root.tk.call('tk', 'scaling', '-displayof', '.', 100.0/72.0)
    gui = FileBrowserGUI(root)
    root.mainloop()
