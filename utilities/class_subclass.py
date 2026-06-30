class LibraryItem:
    title: str
    year: int

    def __init__(self, title: str, year: int):
        self.title = title
        self.year = year

    def get_info(self) -> str:
        return f"{self.title} ({self.year})"

class Book(LibraryItem):
    author: str

    def __init__(self, title: str, year: int, author: str):
        super().__init__(title, year)
        self.author = author

    def get_info(self) -> str:
        return f"'{self.title}' by {self.author} ({self.year})"

    @classmethod
    def from_string(cls, info: str) -> 'Book':
        title, author, year = info.split(', ')
        return cls(title, int(year), author)

# Using the class method and the subclass
book = Book.from_string("The Catcher in the Rye, J.D. Salinger, 1951")
print(book.get_info())