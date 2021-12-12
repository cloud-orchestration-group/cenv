from contextlib import contextmanager

import os
import pathlib
import shutil
import threading
import oyaml


def get_files(path):
    files = []

    if isinstance(path, (list, tuple)):
        path_str = os.path.join(*path)
        path = list(path)
    else:
        path_str = path
        path = [ path ]

    if os.path.isdir(path_str):
        for name in os.listdir(path_str):
            files.extend(get_files([ *path, name ]))
    else:
        files = [ path ]

    return files


def create_dir(dir_path):
    pathlib.Path(dir_path).mkdir(mode = 0o700, parents = True, exist_ok = True)


def load_file(file_path, binary = False):
    operation = 'rb' if binary else 'r'
    content = None

    if os.path.exists(file_path):
        with open(file_path, operation) as file:
            content = file.read()
    return content

def load_yaml(file_path):
    content = load_file(file_path)
    if content:
        content = oyaml.safe_load(content)
    return content

def save_file(file_path, content, binary = False):
    operation = 'wb' if binary else 'w'

    with open(file_path, operation) as file:
        file.write(content)

    path_obj = pathlib.Path(file_path)
    path_obj.chmod(0o700)

def save_yaml(file_path, data):
    save_file(file_path, oyaml.dump(data))


@contextmanager
def filesystem_dir(base_path):
    directory = FileSystem(base_path)
    yield directory


class FileSystem(object):

    thread_lock = threading.Lock()


    def __init__(self, base_path):
        self.base_path = base_path
        pathlib.Path(self.base_path).mkdir(mode = 0o700, parents = True, exist_ok = True)


    def mkdir(self, directory):
        path = os.path.join(self.base_path, directory)
        pathlib.Path(path).mkdir(mode = 0o700, parents = True, exist_ok = True)
        return path

    def listdir(self, directory = None):
        if directory:
            path = os.path.join(self.base_path, directory)
        else:
            path = self.base_path

        return os.listdir(path)


    def path(self, file_name, directory = None):
        if file_name.startswith(self.base_path):
            return file_name

        if directory:
            path = self.mkdir(directory)
        else:
            path = self.base_path

        return os.path.join(path, file_name)

    def exists(self, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.exists(path):
            return True
        return False


    def open(self, file_name, directory = None, binary = False, readonly = False, write = False, append = False):
        path = self.path(file_name, directory)

        if readonly:
            operation = "rb" if binary else 'r'
        elif write:
            operation = 'wb' if binary else 'w'
        elif append:
            operation = 'ab' if binary else 'a'
        else:
            operation = 'r+b' if binary else 'r+'

        return open(path, operation)


    def load(self, file_name, directory = None, binary = False, return_handle = False):
        path = self.path(file_name, directory = directory)
        operation = 'rb' if binary else 'r'
        content = None

        with self.thread_lock:
            if os.path.exists(path):
                with open(path, operation) as file:
                    content = file.read()

        if return_handle:
            return self.open(file_name, directory, binary)
        return content

    def save(self, content, file_name, directory = None, extension = None, binary = False, return_handle = False):
        path = self.path(file_name, directory = directory)
        operation = 'wb' if binary else 'w'

        if extension:
            path = "{}.{}".format(path, extension)

        with self.thread_lock:
            with open(path, operation) as file:
                file.write(content)

            path_obj = pathlib.Path(path)
            path_obj.chmod(0o700)

        if return_handle:
            return self.open(file_name, directory, binary)
        return path

    def link(self, source_path, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
        os.symlink(source_path, path)
        return path

    def copy(self, source_path, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.isfile(path):
            os.remove(path)
        shutil.copy(source_path, path)
        return path

    def remove(self, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if path.startswith(self.base_path):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors = True)
            elif os.path.isfile(path):
                os.remove(path)

    def delete(self):
        shutil.rmtree(self.base_path, ignore_errors = True)
