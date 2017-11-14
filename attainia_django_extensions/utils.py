import ast
import os


def get_env_var_string_as_dict(env_var_name):
    """ Helper function to get a dictionary stored as an environment variable string """
    dict_str = os.getenv(env_var_name, "{}").replace('"', '')

    return ast.literal_eval(dict_str)

def get_env_var_string_as_list(env_var_name):
    """ Helper function to get a list stored as an environment variable string """
    list_str = os.getenv(env_var_name, "[]").replace('"', '')

    return ast.literal_eval(list_str)
