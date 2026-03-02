from collections import UserDict
from datetime import datetime, timedelta


def input_error(func=None, *, usage=""):
    def decorator(f):
        def inner(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except KeyError:
                return "Contact not found."
            except ValueError as e:
                return str(e)
            except IndexError:
                msg = "Not enough arguments."
                if usage:
                    msg += f" Usage: {usage}"
                return msg
            except Exception as e:
                return f"An unexpected error occurred: {e}"
        return inner
    if func is not None:
        return decorator(func)
    return decorator


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value.strip())


class Phone(Field):
    def __init__(self, value):
        self.value = value  # uses the setter for validation

    @staticmethod
    def _validate(value):
        if not (isinstance(value, str) and value.isdigit() and len(value) == 10):
            raise ValueError(f"Phone number must be 10 digits, got: {value}")

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        Phone._validate(value)
        self._value = value


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        filtered = [p for p in self.phones if p.value != phone]
        if len(filtered) == len(self.phones):
            raise ValueError(f"Phone {phone} not found in record for {self.name.value}.")
        self.phones = filtered

    def edit_phone(self, old_phone, new_phone):
        for i, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return
        raise ValueError(f"Phone {old_phone} not found in record for {self.name.value}.")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones)
        birthday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "N/A"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming = []
        for record in self.data.values():
            if record.birthday is None:
                continue
            bday = record.birthday.value.date()
            bday_this_year = bday.replace(year=today.year)
            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)
            delta = (bday_this_year - today).days
            if 0 <= delta <= 6:
                congratulation_date = bday_this_year
                if congratulation_date.weekday() == 5:  # Saturday
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:  # Sunday
                    congratulation_date += timedelta(days=1)
                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y"),
                })
        return upcoming


def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return ("",)
    command = parts[0].lower()
    args = parts[1:]
    return command, *args


@input_error(usage="add [name] [phone]")
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error(usage="change [name] [old phone] [new phone]")
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise IndexError
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error(usage="phone [name]")
def show_phones(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    return '; '.join(p.value for p in record.phones)


@input_error
def show_all(args, book: AddressBook):
    if not book.data:
        return "No contacts saved."
    return '\n'.join(str(record) for record in book.data.values())


@input_error(usage="add-birthday [name] [DD.MM.YYYY]")
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError
    name, date, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(date)
    return "Birthday added."


@input_error(usage="show-birthday [name]")
def show_birthday(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday is None:
        return f"{name} has no birthday set."
    return record.birthday.value.strftime("%d.%m.%Y")


@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next week."
    return '\n'.join(
        f"{entry['name']}: {entry['congratulation_date']}" for entry in upcoming
    )


@input_error(usage="remove-contact [name]")
def remove_contact(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    name, *_ = args
    if book.find(name) is None:
        raise KeyError
    book.delete(name)
    return "Contact removed."


@input_error(usage="remove-phone [name] [phone]")
def remove_phone(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError
    name, phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.remove_phone(phone)
    return "Phone removed."


def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")

    commands = {
        "add": add_contact,
        "change": change_contact,
        "phone": show_phones,
        "all": show_all,
        "add-birthday": add_birthday,
        "show-birthday": show_birthday,
        "birthdays": birthdays,
        "remove-contact": remove_contact,
        "remove-phone": remove_phone,
    }

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ("close", "exit"):
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command in commands:
            print(commands[command](args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
