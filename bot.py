import pickle
from pathlib import Path
from datetime import date, timedelta
from functools import reduce
from collections import UserDict


class DuplicatedPhoneError(Exception):
    ...


class Field:
    def __init__(self, value: str):
        self.__value = value

    def __str__(self):
        return str(self.__value)
    
    def _set_value(self, value: str):
        self.__value = value

    @property
    def value(self):
        return self.__value


class Name(Field):
    ...


class Phone(Field):
    def __init__(self, value: str) -> None:
        self.value = value
    
    @property
    def value(self):
        return super().value

    @value.setter
    def value(self, value: str):
        super()._set_value(self.__validate(value))

    def __validate(self, value: str) -> str:
        value = reduce((lambda a, b: a.replace(b, "")), "+()-", value)        
        if value.isdigit() and len(value) == 10:
            return value
        else:
            raise ValueError(f"Phone number'{value}' is incorrect. Phone number should consist of 10 digits.")


class Birthday(Field):
    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def value(self):
        return super().value

    @property
    def date(self):
        return date(self.__year, self.__month, self.__day)
        
    @value.setter
    def value(self, value: str):
        self.__year, self.__month, self.__day = self.__validate(value)
        super()._set_value(f"{self.__day}-{self.__month}-{self.__year}")

    def __validate(self, value: str) -> tuple:
        separator = "." if "." in value else "/" if "/" in value else "-"
        date_parts = value.split(separator)
        if len(date_parts) == 3:
            day, month, year = date_parts[:]
            if day.isdigit() and month.isdigit() and year.isdigit():
                if date(int(year), int(month), int(day)):
                    return int(year), int(month), int(day)
        raise ValueError(f"Birthday '{value}' format is incorrect. Use DD-MM-YYYY format")


class Record:
    def __init__(self, name: str, phone=None, birthday=None):
        self.name = Name(name)
        self.phones = [Phone(phone)] if phone else []
        self.birthday = Birthday(birthday) if birthday else "Not set"

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday}"
    
    def add_phone(self, phone: str): 
        existing_phone = self.find_phone(phone)
        if not existing_phone:
            self.phones.append(Phone(phone))
        else:
            raise DuplicatedPhoneError(self.name, phone)

    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def days_to_birthday(self) -> int:
        next_birthday = self.birthday.date.replace(year=date.today().year)
        if next_birthday < date.today():
            next_birthday = next_birthday.replace(year=next_birthday.year+1)
        delta = next_birthday - date.today()
        return delta.days

    def edit_phone(self, old_phone: str, new_phone: str):
        existing_phone = self.find_phone(old_phone)
        if existing_phone:
            idx = self.phones.index(existing_phone)
            self.phones[idx] = Phone(new_phone)
        else:
            raise ValueError(f"Phone number {old_phone} not found for contact {self.name}.")
                
    def remove_phone(self, phone: str):
        existing_phone = self.find_phone(phone)
        if existing_phone:
            self.phones.remove(existing_phone)
        else:
            raise ValueError(f"Phone number {phone} not found for contact {self.name}.")
                            
    def find_phone(self, phone: str):
        existing_phone = list(filter(lambda p: p.value == phone, self.phones))
        if len(existing_phone) > 0:
            return existing_phone[0]
        
    def has_phone(self, term: str) -> bool:
        phones = list(filter(lambda p: term in p.value, self.phones))
        return len(phones) > 0
        

class AddressBook(UserDict):
    def __init__(self, file_name):
        self.__file_name = file_name
        super().__init__()
        
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str, suppress_error=False) -> Record:
        if name in self.data.keys():
            return self.data[name]
        if not suppress_error:
            raise KeyError

    def delete(self, name: str):
        if name in self.data.keys():
            return self.data.pop(name)
    
    def __values(self):
        return list(self.data.values())
    
    def iterator(self, n=2):
        counter = 0
        values = self.__values()
        while counter < len(values):
            yield list(map(lambda record: str(record), values[counter: counter + n]))
            counter += n

    def __enter__(self):
        if Path(self.__file_name).exists():
            with open(self.__file_name, "rb") as fh:
                self.data = pickle.load(fh)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        with open(self.__file_name, "wb") as fh:
            pickle.dump(self.data, fh)
    
    def search_contacts(self, term):
        result = list(filter(lambda contact: term in contact.name.value.lower() or contact.has_phone(term), self.data.values()))
        return result


records = None

def input_error(*expected_args):
    def input_error_wrapper(func):
        def inner(*args):
            try:
                return func(*args)
            except IndexError:
                return f"Please enter {' and '.join(expected_args)}"
            except KeyError:
                return f"The record for contact {args[0]} not found. Try another contact or use help."
            except ValueError as error:
                if error.args:
                    return error.args[0]
                return f"Phone format '{args[1]}' is incorrect. Use digits only for phone number."
            except DuplicatedPhoneError as phone_error:
                return f"Phone number {phone_error.args[1]} already exists for contact {phone_error.args[0]}."
            except AttributeError:
                return f"Contact {args[0]} doesn't have birthday yet."
        return inner
    return input_error_wrapper

def capitalize_user_name(func):
    def inner(*args):
        new_args = list(args)
        new_args[0] = new_args[0].capitalize()
        return func(*new_args)
    return inner

def unknown_handler(*args):
    return f"Unknown command. Use <help>"

def help_handler():
    help_txt = ""
    def inner(*args):
        nonlocal help_txt
        if not help_txt:
            with open("help.txt") as file:            
                help_txt = "".join(file.readlines())
        return help_txt
    return inner

@capitalize_user_name
@input_error("name", "phone")
def add_handler(*args):
    user_name = args[0]
    user_phones = args[1:]
    record = records.find(user_name, True)
    if not record:
        record = Record(user_name)
        for user_phone in user_phones:
            record.add_phone(user_phone)
        records.add_record(record)
        return f"New record added for {user_name} with phone number{'s' if len(user_phones) > 1 else ''}: {'; '.join(user_phones)}."
    else:
        response = []
        for user_phone in user_phones:
            record.add_phone(user_phone)
            response.append(f"New phone number {user_phone} for contact {user_name} added.")
        return "\n".join(response)

@capitalize_user_name
@input_error("name", "old_phone", "new_phone")
def change_handler(*args):
    user_name = args[0]
    old_phone = args[1]
    new_phone = args[2]
    record = records.find(user_name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number for {user_name} changed from {old_phone} to {new_phone}."

@capitalize_user_name    
@input_error("name")
def birthday_handler(*args):
    user_name = args[0]
    user_birthday = args[1] if len(args) > 1 else None
    record = records.find(user_name)
    if record:
        if user_birthday:
            record.add_birthday(user_birthday)
            return f"Birthday {user_birthday} for contact {user_name} added."
        else:
            return f"{record.days_to_birthday()} days to the next {user_name}'s birthday ({record.birthday})."

@capitalize_user_name    
@input_error("name")
def delete_handler(*args):
    user_name = args[0]
    user_phones = args[1:]
    if len(user_phones) >= 1:
        record = records.find(user_name)
        if record:
            response = []
            for user_phone in user_phones:
                record.remove_phone(user_phone)
                response.append(f"Phone number {user_phone} for contact {user_name} removed.")
            return "\n".join(response)
    else:
        if records.delete(user_name):
            return f"Record for contact {user_name} deleted."
        return f"Record for contact {user_name} not found."


@input_error([])
def greeting_handler(*args):
    greeting = "How can I help you?"
    return greeting

@capitalize_user_name
@input_error("name")
def phone_handler(*args):
    user_name = args[0]
    record = records.find(user_name)
    if record:
        return "; ".join(p.value for p in record.phones)

@input_error("term")
def search_handler(*args):
    term: str = args[0]
    contacts = records.search_contacts(term)
    if contacts:
        return "\n".join(str(contact) for contact in contacts)
    return f"No contacts found for '{term}'."

@input_error([])
def show_all_handler(*args):
    return records.iterator()

COMMANDS = {
            help_handler(): "help",
            greeting_handler: "hello",
            add_handler: "add",
            change_handler: "change",
            phone_handler: "phone",
            search_handler: "search",
            birthday_handler: "birthday",
            show_all_handler: "show all",
            delete_handler: "delete"
            }
EXIT_COMMANDS = {"good bye", "close", "exit", "stop", "g"}

def parser(text: str):
    for func, kw in COMMANDS.items():
        if text.startswith(kw):
            return func, text[len(kw):].strip().split()
    return unknown_handler, []

def main():
    global records
    with AddressBook("address_book.pkl") as book:
        records = book
        while True:
            user_input = input(">>> ").lower()
            if user_input in EXIT_COMMANDS:
                print("Good bye!")
                break
            
            func, data = parser(user_input)
            result = func(*data)
            if isinstance(result, str):
                print(result)
            else:
                for i in result:                
                    print ("\n".join(i))
                    input("Press enter to show more records")


if __name__ == "__main__":
    main()