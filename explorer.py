import os


class Explorer:
    def __init__(self):
        self.current_path = os.getcwd()

    def list_dir(self):
        return os.listdir(self.current_path)

    def change_dir(self, new_dir):
        if new_dir == "..":
            self.current_path = os.path.abspath(os.path.join(self.current_path, os.pardir))
        else:
            new_path = os.path.join(self.current_path, new_dir)
            if os.path.isdir(new_path):
                self.current_path = new_path

    def current_full_path(self):
        return os.path.abspath(self.current_path)
