import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps
import os
import math
import pydicom as dicom
from zoom import AutoScrollbar, CanvasImage

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
        
        # Create widgets
        self.size = tk.IntVar()
        self.size.set(500)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(master, textvariable=self.path_var)
        
        self.contrast_var = tk.DoubleVar()
        self.slope_var = tk.DoubleVar()
        self.intercept_var = tk.DoubleVar()
        

        self.file_index = 0
        self.list_files = []
        self.aux_path = ''
        
        self.bs_var = tk.StringVar()
        self.bg_var = tk.StringVar()
        self.lv_var = tk.StringVar()
        self.radio_var = tk.IntVar()

        self.browse_button = ttk.Button(master, text="Browse input", command=self.browse_files)
        self.tree = ttk.Treeview(master)
        self.tree.bind("<Double-1>", self.tree_double_click)
        self.image_frame = ttk.Frame(master, width = 200, height = 200)
        self.size_update_button = ttk.Button(master, text="Update", command=self.update_size)

        self.settings_frame = ttk.Frame(master, border=5,relief='solid',height=100)
        self.contrast_label = ttk.Label(self.settings_frame, text="Contrast = " )
        self.contrast_entry = ttk.Entry(self.settings_frame, textvariable=self.contrast_var)
        self.size_label = ttk.Label(self.settings_frame, text="Size = " )
        self.size_entry = ttk.Entry(self.settings_frame, textvariable=self.size)
        self.slope_label = ttk.Label(self.settings_frame, text="Slope = " )
        self.slope_entry = ttk.Entry(self.settings_frame, textvariable=self.slope_var)
        self.intercept_label = ttk.Label(self.settings_frame, text="Intercept = " )
        self.intercept_entry = ttk.Entry(self.settings_frame, textvariable=self.intercept_var)
        
        self.path_var_output = tk.StringVar()
        self.path_entry_output = ttk.Entry(master, textvariable=self.path_var_output)
        self.browse_button_output = ttk.Button(master, text="Browse output", command=self.browse_button_output_click)
        self.save_button = ttk.Button(master, text="Save", command = self.save_button_click,state='disabled')

        bs_selected_path = Image.open('icons/button_brainstem_selected.png').resize((160,40))
        bg_selected_path = Image.open('icons/button_basal-ganglia_selected.png').resize((160,40))
        lv_selected_path = Image.open('icons/button_lateral-ventricles_selected.png').resize((160,40))
        bs_path = Image.open('icons/button_brainstem.png').resize((160,40))
        bg_path = Image.open('icons/button_basal-ganglia.png').resize((160,40))
        lv_path = Image.open('icons/button_lateral-ventricles.png').resize((160,40))

        self.bs_selected_b_i = ImageTk.PhotoImage(bs_selected_path)
        self.bg_selected_b_i = ImageTk.PhotoImage(bg_selected_path)
        self.lv_selected_b_i = ImageTk.PhotoImage(lv_selected_path)
        self.bs_b_i = ImageTk.PhotoImage(bs_path)
        self.bg_b_i = ImageTk.PhotoImage(bg_path)
        self.lv_b_i = ImageTk.PhotoImage(lv_path)

        self.selection_frame = tk.Canvas(master) 
        
        self.bs_selection_button = ttk.Label(self.selection_frame, image=self.bs_b_i)
        self.bg_selection_button = ttk.Label(self.selection_frame, image=self.bg_b_i)
        self.lv_selection_button = ttk.Label(self.selection_frame, image=self.lv_b_i)
        
        self.bs_selection_button.bind("<Button-1>", self.bs_button_click)
        self.bg_selection_button.bind("<Button-1>", self.bg_button_click)
        self.lv_selection_button.bind("<Button-1>", self.lv_button_click)
        
        next_button = ttk.Button(master, text="Next", command = self.next_button_click)
        prev_button = ttk.Button(master, text="Previous", command = self.prev_button_click)

        self.gallery_buttons_frame = ttk.Frame(master)  
        self.prev_gallery_button = ttk.Button(self.gallery_buttons_frame, text="^", command = self.prev_gallery_button_click, state='disabled')
        self.next_gallery_button = ttk.Button(self.gallery_buttons_frame, text="v", command = self.next_gallery_button_click, state='disabled')
        
        self.gallery_frame = ttk.Frame(master, border=5,relief='solid',height=100)
        self.gallery_frame.config(height=200)
        self.gallery_frame_vbar1 = ttk.Scrollbar(self.gallery_frame, orient='vertical', command=self.gallery_scroll)
        self.gallery_frame_vbar = ttk.Scrollbar(self.gallery_frame, orient='vertical', command=self.gallery_scroll)
        self.gallery_frame_vbar.grid(row=0, column=1, sticky='ns')
        self.gallery_canvas = tk.Canvas(self.gallery_frame,
                                yscrollcommand=self.gallery_frame_vbar.set,width=100, height=100)
        self.gallery_canvas.grid(row=0, column=0, sticky='nswe')
        self.gallery_canvas.update()
        self.gallery_frame_vbar.configure(command=self.gallery_canvas.yview)
        
        self.radio_button_frame = ttk.Frame(master, border=5,relief='solid',height=100)
        self.h_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Hemorrhage", variable=self.radio_var, value=1)
        self.n_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Normal", variable=self.radio_var, value=2)
        self.i_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Isquemic", variable=self.radio_var, value=3)
        self.u_radio_button = ttk.Radiobutton(self.radio_button_frame, text="Unknown", variable=self.radio_var, value=4)
        
        # Lay out widgets
        self.path_entry.grid(row=0, column=0, sticky="we")
        self.browse_button.grid(row=0, column=1, sticky="e")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.image_frame.grid(row=1, column=1, sticky="nsew", columnspan= 3, padx=1,pady=1, ipadx=1, ipady=1)

        self.browse_button_output.grid(row=4, column=1, sticky="we")
        self.path_entry_output.grid(row=4,column=0,sticky="we")

        self.size_label.grid(row=0, column=0, sticky="w")
        self.size_entry.grid(row=0, column=1, sticky="we")
        self.slope_entry.grid(row=1, column=1, sticky="we")
        self.slope_label.grid(row=1, column=0, sticky="w")
        self.intercept_entry.grid(row=2, column=1, sticky="we")
        self.intercept_label.grid(row=2, column=0, sticky="w")
        self.contrast_entry.grid(row=3, column=1, sticky="we")
        self.contrast_label.grid(row=3, column=0, sticky="w")
        self.settings_frame.grid(row=4, column=0, sticky="w", columnspan=1, rowspan=2)
        self.size_update_button.grid(row=7, column=4, sticky="e")

        self.selection_frame.grid(row=2, column=1, sticky="we", columnspan=2)
        self.bs_selection_button.grid(row=0, column=0, sticky="we")
        self.bg_selection_button.grid(row=0, column=1, sticky="we")
        self.lv_selection_button.grid(row=0, column=2, sticky="we")
        self.selection_frame.columnconfigure(0, weight=1)
        self.selection_frame.columnconfigure(1, weight=1)
        self.selection_frame.columnconfigure(2, weight=1)

        next_button.grid(row=3, column=3, sticky="e")
        prev_button.grid(row=3, column=1, sticky="w")
        
        self.next_gallery_button.grid(row=0, column=2, sticky="e")
        self.prev_gallery_button.grid(row=0, column=1, sticky="w")
        self.gallery_buttons_frame.grid(row=2, column=4, sticky="we")

        self.gallery_frame.grid(row=1, column=4,sticky='nswe', padx=5,pady=5, ipadx=5, ipady=5)
        
        self.gallery_frame.rowconfigure(0, weight=1)
        self.gallery_frame.columnconfigure(0, weight=1)
        
        self.radio_button_frame.grid(row=4, column=3, sticky="we", rowspan=2, columnspan=1)
        self.h_radio_button.grid(row=0, column=0, sticky="we", padx=25, pady=20)
        self.n_radio_button.grid(row=1, column=1, sticky="we", padx=25, pady=20)
        self.i_radio_button.grid(row=0, column=1, sticky="we", padx=25, pady=20)
        self.u_radio_button.grid(row=1, column=0, sticky="we", padx=25, pady=20)
        
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
        self.master.grid_rowconfigure(7,weight=1)

        self.gallery_buttons_frame.grid_columnconfigure(0,weight=1)
        self.gallery_buttons_frame.grid_columnconfigure(1,weight=1)
        self.gallery_buttons_frame.grid_columnconfigure(2,weight=1)
        self.gallery_buttons_frame.grid_columnconfigure(3,weight=1)
        
        self.bs_var.set('')
        self.bg_var.set('')
        self.lv_var.set('')
        
        self.prev_image = ''
        self.actual_image = ''
        self.prev_dir = ''

        self.save_button.grid(row=3, column=2, sticky="w")
        self.output_dir = 0
        self.output_file = 0
        self.gallery_index = 0
        self.max_gallery_index = 0

        self.slope_var.set(1)
        self.intercept_var.set(1)

        # Set up treeview columns
        self.path_entry.delete(0, tk.END)
        self.path_var.set(sep(os.getcwd()))
        
        # Populate treeview with root directory
        root_node = self.tree.insert("", "end", text=os.getcwd())
        self.populate_tree(root_node)
        self.delimiter = '/'
        
        self.contrast_var.set(1)
        self.slope_var.set(1)
        self.intercept_var.set(1)

    def get_directory_size(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for file in filenames:
                filepath = os.path.join(dirpath, file)
                total_size += os.path.getsize(filepath)
        return self.convert_size(total_size)

    def convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes/p, 2)
        return "%s %s" % (s, size_name[i])

    def populate_tree(self, parent, full_path: str= None):
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

            for directory in directory_list:
                d_full_path = sep(os.path.join(full_path, directory))
                if os.path.isdir(d_full_path):
                    node = self.tree.insert(parent, "end", text=directory,value=d_full_path)
                    self.populate_tree(node, d_full_path)
        except:
            print(Exception)
                
    def browse_files(self):
        directory = askdirectory()
        self.path_var.set(directory)
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, directory)
        if directory:
            for item in self.tree.get_children():
                self.tree.delete(item)
            root_node = self.tree.insert("", "end", text=directory)
            self.populate_tree(root_node)
        else:
            messagebox.showerror("Error", "Invalid path")

    def tree_double_click(self, event):
        item = self.tree.selection()[0]
        path = ' '.join(self.tree.item(item, "value"))
        
        if os.path.isdir(path):
            # Update directory size in treeview
            self.tree.set(item)

            # Clear image frame
            
            for widget in self.image_frame.winfo_children():
                widget.destroy()
            # Populate image frame with images from selected directory
            self.aux_path = path
            print(path)
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
  
    def browse_button_output_click(self):
        directory = askdirectory()
        self.path_var_output.set(directory)
        self.path_entry_output.delete(0, tk.END)
        self.path_entry_output.insert(0, directory)

    def save_button_click(self):
        try:
            isExist = os.path.exists(self.delimiter.join(self.path_var_output.get().split(self.delimiter)[:-1]))

            if not isExist:
                os.makedirs(self.delimiter.join(self.path_var_output.get().split(self.delimiter)[:-1]))
            self.image.convert('L').save(self.path_var_output.get())
            self.output_file += 1
        except:
            messagebox.showerror("Error", "Invalid path",)
    
    def bs_button_click(self, event):
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
        
        canva_height = self.image_frame.winfo_children()[0].winfo_children()[2].winfo_height()
        canva_width = self.image_frame.winfo_children()[0].winfo_children()[2].winfo_width()
        if self.bs_var.get() == '':
            self.bs_var.set(self.file_index)
            self.bs_selection_button.config(image=self.bs_selected_b_i)
            #self.image_frame.winfo_children()[0].winfo_children()[2].create_rectangle(0,0,canva_width,canva_height, outline= 'purple', width=10)  
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
              
    def bg_button_click(self, event):
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
        canva_height = self.image_frame.winfo_children()[0].winfo_children()[2].winfo_height()
        canva_width = self.image_frame.winfo_children()[0].winfo_children()[2].winfo_width()
        if self.bg_var.get() == '':
            self.bg_var.set(self.file_index)
            self.bg_selection_button.config(image=self.bg_selected_b_i)
            #self.image_frame.winfo_children()[0].winfo_children()[2].create_rectangle(0,0,canva_width,canva_height, outline= 'orange', width=10)
            #self.image_frame.config(bg='orange')
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

    def lv_button_click(self, event):
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
        canva_height = self.image_frame.winfo_children()[0].winfo_children()[2].winfo_height()
        canva_width = self.image_frame.winfo_children()[0].winfo_children()[2].winfo_width()

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
            #self.image_frame.config(bg='white')
            self.save_button.config(state='disabled')

    def next_button_click(self):
        self.file_index += 1
        self.manage_images()

    def prev_button_click(self):
        self.file_index -= 1
        self.manage_images()   

    def next_gallery_button_click(self):
        if self.gallery_index == 0:
            self.prev_gallery_button.config(state='normal')
        self.gallery_index += 1
        if self.gallery_index >= self.max_gallery_index:
            self.gallery_index = self.max_gallery_index
            self.next_gallery_button.config(state='disabled')       
        self.manage_gallery()
    
    def prev_gallery_button_click(self):
        self.gallery_index -= 1
        if self.gallery_index == 0:
            self.prev_gallery_button.config(state='disabled')
            if self.max_gallery_index != 0:
                self.next_gallery_button.config(state='normal')
        self.manage_gallery()

    def populate_images(self, path):
        # Get image files in directory
        image_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".dcm" ))]

        if len(image_files) == 0:
            messagebox.showerror("Error", "No images in directory")
            return
        
        image_files =  [[s,int(''.join(filter(str.isdigit, s)))] for s in image_files]
        image_files = sorted(image_files, key=lambda  t:t[1])
        image_files = [s[0] for s in image_files]

        # Populate image frame with images
        self.list_files = image_files
        self.max_gallery_index = len(image_files) // 9
        if self.max_gallery_index != 0:
            self.next_gallery_button.config(state='normal')
        
        self.file_index = 0
        
        full_path = os.path.join(path, image_files[0])
        
        self.manage_images()

    def update_size(self):
        self.size.set(self.size_entry.get())
        self.image_frame.config(width=self.size.get(), height=self.size.get())
        self.manage_images()

    def get_first_of_dicom_field_as_int(self, x):
        #get x[0] as in int is x is a 'pydicom.multival.MultiValue', otherwise get int(x)
        if type(x) == dicom.multival.MultiValue: 
            return int(x[0])
        else: 
            return int(x)

    def window_image(self, img, window_center,window_width, intercept, slope, rescale=True):
        img = (img*(slope*self.slope_var.get()) +(intercept+self.intercept_var.get())) #for translation adjustments given in the dicom file. 
        img_min = window_center - window_width//2 #minimum HU level
        img_max = window_center + window_width//2 #maximum HU level
        img[img<img_min] = img_min #set img_min for all HU levels less than minimum HU level
        img[img>img_max] = img_max #set img_max for all HU levels higher than maximum HU level
        if rescale: 
            img = (img - img_min) / (img_max - img_min)*255.0 
        return img

    def get_windowing(self,data):
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
            return dicom_fields
        return [self.get_first_of_dicom_field_as_int(x) for x in dicom_fields]
    
    def dcm_image(self, full_path):
        if '\\' in full_path:
            full_path = sep(full_path)
        ds = dicom.dcmread(full_path)
        image = ds.pixel_array
        window_center , window_width, intercept, slope = self.get_windowing(ds)
        output = self.window_image(image, window_center, window_width, intercept, slope, rescale = False)
        return output * self.contrast_var.get()

    def manage_images(self):
        # Get image files in directory
        # Populate image frame with images
        # clear image frame

        self.prev_image = self.actual_image
        #print('manage images =',self.image_frame.winfo_children())
        
        bs, bg, lv = -1, -1, -1
        if self.bs_var.get() != '': 
            #print('bs')
            bs = int(self.bs_var.get())
        if self.bg_var.get() != '': 
            #print('bg')
            bg = int(self.bg_var.get())    
        if self.lv_var.get() != '': 
            #print('lv')
            lv = int(self.lv_var.get())
        
        for widget in self.image_frame.winfo_children():
            #print(widget.winfo_children())
            #for widget2 in widget.winfo_children():
            #    print(widget2.winfo_children())
            widget.destroy()        
        
        full_path = sep(os.path.join(self.aux_path, self.list_files[self.file_index%len(self.list_files)]))
        
        if '.dcm' in full_path:
            output_image = self.dcm_image(full_path)
            image = Image.fromarray(output_image)
            
        else:
            image = Image.open(full_path)
        
        image = image.convert('HSV')
        image.thumbnail((int(self.size.get()), int(self.size.get())))
        self.image = image
        
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
        self.actual_image = full_path

        if self.prev_dir != self.actual_image.split(self.delimiter)[-2]:
                self.prev_dir = self.actual_image.split(self.delimiter)[-2]
                self.output_dir += 1

        if not '.jpg' in self.path_var_output.get().split(self.delimiter)[-1]:
            self.path_var_output.set(self.path_var_output.get()+self.delimiter+str(self.output_dir)+self.delimiter+str(self.output_file)+'.jpg')
        else:
            output_path = self.delimiter.join(self.path_var_output.get().split(self.delimiter)[:-2])
            self.path_var_output.set(output_path+self.delimiter+str(self.output_dir)+self.delimiter+str(self.output_file)+'.jpg')

    def gallery_scroll(self, event):
        print(event)
    
    def gallery_click(self, event, index):
        self.file_index = index
        self.manage_images()

    def manage_gallery(self):
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
        
        
        for i, path in enumerate(sublist):
            full_path = os.path.join(self.aux_path, path)
            if '.dcm' in full_path:
                output_image = self.dcm_image(full_path)
                image = Image.fromarray(output_image)   
            else:
                image = Image.open(full_path)
            image.thumbnail((100, 100))

            
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
            
            
                    
if __name__ == "__main__":
    root = tk.Tk()
    width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    root.maxsize(width, height)
    root.geometry('%dx%d+0+0' % (width,height))
    root.tk.call('tk', 'scaling', '-displayof', '.', 100.0/72.0)
    gui = FileBrowserGUI(root)
    root.mainloop()
