fruits = ["Apples", "Bananas", "Pears"]

book1 = {"title": "Great Expectations", "author": "Charles Dickens"}
book2 = {"title": "Bleak House", "author": "Charles Dickens"}
book3 = {"title": "An Book By No Author"}
book4 = {"title": "Moby Dick", "author": "Herman Melville"}

books = [book1, book2, book3, book4]

# --- List 1: Sci-Fi Books ---
scifi_books = [
    {"title": "Dune", "author": "Frank Herbert"},
    {"title": "The Matrix", "author": "Wachowskis"}
]

# --- List 2: History Books ---
history_books = [
    {"title": "Sapiens", "author": "Yuval Noah Harari"},
    {"title": "SPQR", "author": "Mary Beard"}
]

for i in fruits:
    print(i)

fruit_shouted = []
for j in fruits:
    fruit_shouted.append(j.upper())

#print("now in out shide of fruit shouted")
print(fruit_shouted)

fruit_shouted2 = [fruit.upper() for fruit in fruits]
print(f" 1: print print shouted 2: {fruit_shouted2}")

# create directory
fruit_mapping = {fruit: fruit.upper() for fruit in fruits}
print(f" 2: dictionary is {fruit_mapping}")

#some fileters
fruit_with_a = {fruit: fruit.upper() for fruit in fruits if fruit.startswith('A')}
print(f" 3: fruit with a {fruit_with_a}")

#now Books 
for book in books:
    print(f" ---- what I am printing : {book} ")

print_title = [k ['title'] for k in books]
print(f" 4. print title {print_title}")

# And this version will convert it into a set, removing duplicates

listof_authors = set([book.get('author') for book in books if book.get('author')])
print(f"5. list of authors : {listof_authors}")

def number_generator():
    for i in range(1, 6):
        yield i

gen = number_generator()
for number in gen:
    print (f"6. number generation : {number}")


class booksdisplay:
    def __init__(self, book_list):
        self.books = book_list
    
    def get_all_books(self):
        return [i.get("title") for i in self.books]

    # This tells Python what to display when someone prints the object directly
    def __str__(self):
        return f"BooksDisplay Manager holding {len(self.books)} books"

manager = booksdisplay(books)    
print(f"7. Book manager : {manager}")

# To this:
print(f"77. all biooks Book manager : {manager.get_all_books()}")


class bookManager():
    def __init__(self, book_list2):
        self.buk = book_list2
    
    def get_all_books(self):
        return [i.get("title") for i in self.books]
        
sci_manager = bookManager(scifi_books)
print(f"Sci books are : {sci_manager}")

hisory_manager = bookManager(history_books)
print(f" History books are in stock : {history_books}")

Scii_manager = bookManager(scifi_books)
print(f" scifi books are in stock : {Scii_manager}")