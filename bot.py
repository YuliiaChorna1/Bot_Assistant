from pathlib import Path
from functools import reduce

records = {}


def input_error(*expected_args):
    def input_error_wrapper(func):
        def inner(*args):
            try:
                return func(*args)
            except IndexError:
                return f"Please enter {' and '.join(expected_args)}"
            except KeyError:
                return f"The record for contact {args[0]} not found. Try another contact or use help."
            except ValueError:
                return f"Phone format '{args[1]}' is incorrect. Use digits only for phone number."
        return inner
    return input_error_wrapper

def normalize_phone(func):
    def inner(*args):
        phone: str = args[1].strip()
        phone = reduce((lambda a, b: a.replace(b, "")), "+()-", phone)
        if int(phone):
            new_args = list(args)
            new_args[1] = phone
            return func(*new_args)
    return inner

def capitalize_user_name(func):
    def inner(*args):
        new_args = list(args)
        new_args[0] = new_args[0].capitalize()
        return func(*new_args)
    return inner

def unknown_handler(*args):
    return f"Unknown command. Use help: \n{help_handler(*args)}"

def help_handler(*args):
    output = ""
    with open("help.txt") as file:
        output = "".join(file.readlines())
    return output

@input_error("name", "phone")
@normalize_phone
@capitalize_user_name
def add_handler(*args):
    user_name = args[0]
    user_phone = args[1]
    if user_name not in records.keys():
        records[user_name] = user_phone
        return f"New record for {user_name} with phone number {user_phone} added."

@input_error("name", "phone")
@normalize_phone
@capitalize_user_name
def change_handler(*args):
    user_name = args[0]
    new_phone = args[1]
    rec = records[user_name]
    if rec:
        records[user_name] = new_phone
        return f"Phone number for {user_name} changed to {new_phone}."

@input_error([])
def greeting_handler(*args):
    greeting = "How can I help you?"
    return greeting

@input_error("name")
@capitalize_user_name
def phone_handler(*args):
    user_name = args[0]
    phone = records[user_name]
    if phone:
        return phone
    
@input_error([])
def show_all_handler(*args):
    contacts = map(lambda item: f"name: {item[0]}, phone: {item[1]}", records.items())
    return "\n".join(contacts)

COMMANDS = {
            help_handler: "help",
            greeting_handler: "hello",
            add_handler: "add",
            change_handler: "change",
            phone_handler: "phone",
            show_all_handler: "show all",
            }
EXIT_COMMANDS = {"good bye", "close", "exit", "stop"}

def parser(text: str):
    for func, kw in COMMANDS.items():
        if text.startswith(kw):
            return func, text[len(kw):].strip().split()
    return unknown_handler, []

def main():
    while True:
        user_input = input(">>> ").lower()
        if user_input in EXIT_COMMANDS:
            print("Good bye!")
            break
        
        func, data = parser(user_input)
        print(func(*data))


if __name__ == "__main__":
    main()