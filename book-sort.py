import string
import epub_meta
import os
import sys

#
# export BOOKSORT_ISSUES_PATH=/Users/bvia/Development/Personal/booksort/issues
# export BOOKSORT_OUTPUT_PATH=/Users/bvia/Development/Personal/booksort/outputs
# export BOOKSORT_INPUT_PATH=/Users/bvia/Development/Personal/booksort/inputs

def main():
    inputPath = os.environ["BOOKSORT_INPUT_PATH"]
    outputPath = os.environ["BOOKSORT_OUTPUT_PATH"]
    issuesPath = os.environ["BOOKSORT_ISSUES_PATH"]
    sort_books(inputPath, outputPath, issuesPath)
    

# python function to sort epub and pdf files into title-author folders by reading their metadata
def sort_books(inputPath: string, outputPath: string, issuesPath: string):
    files = getAllFiles(inputPath);
    print(files)
    for file in files:
        bookPath = getBookTitleAndAuthor(file)
        # if bookpath is not none and doesn't contain unknown
        if bookPath and "Unknown" not in bookPath:
            print(bookPath)
            if not os.path.exists(outputPath + "/" + bookPath):
                os.makedirs(outputPath + "/" + bookPath)
            os.rename(file, outputPath + "/" + bookPath + "/" + bookPath + ".epub")
        else:
            print("Moving " + file + " to issues folder")
            os.rename(file, issuesPath + "/" + file)
            continue


def getAllFiles(path: string):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            if '.epub' in file:
                files.append(os.path.join(r, file))
    print(files)
    return files


def getBookTitleAndAuthor(filepath: string):
    try:
        print("Getting metadata for: " + filepath)
        data = epub_meta.get_epub_metadata(filepath)
        title = data['title'] or "Unknown"
        authors =", ".join(data['authors']) or "Unknown"
        return(title + " - " + authors)
    except epub_meta.EPubException as e:
        print(e)
        return None


main()