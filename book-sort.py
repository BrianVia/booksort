import string
import epub_meta
import os
import sys

def main():
    sort_books("/mnt/storage/Books/_unorganized/", "/mnt/storage/Books/")
    

# python function to sort epub and pdf files into title-author folders by reading their metadata
def sort_books(inputPath: string, outputPath: string):
    files = getAllFiles(inputPath);
    print(files)
    for file in files:
        bookPath = get_book_metadata(file)
        print(bookPath);
        if bookPath is not None:
            print(bookPath)
            if not os.path.exists(outputPath + "/" + bookPath):
                os.makedirs(outputPath + "/" + bookPath)
            os.rename(file, outputPath + "/" + bookPath + "/" + bookPath + ".epub")


def getAllFiles(path: string):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            if '.epub' in file:
                files.append(os.path.join(r, file))
    print(files)
    return files


def get_book_metadata(filepath: string):
    try:
        print("Getting metadata for: " + filepath)
        data = epub_meta.get_epub_metadata(filepath)
        title = data['title'] or "Unknown"
        authors =", ".join(data['authors'])
        return(title + " - " + authors)
    except epub_meta.EPubException as e:
        print(e)
        return None


main()