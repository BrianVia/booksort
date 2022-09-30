import os
import sys
import string
import epub_meta
import pdfx

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
        #if file is .epub
        bookPath = ""
        if file.endswith(".epub"):
            bookPath = getEpubTitleAndAuthorPath(file)
        if file.endswith(".pdf"):
            bookPath = getPdfTitleAndAuthorPath(file)
        

        # if bookpath is not none and doesn't contain unknown
        if bookPath and "Unknown" not in bookPath:
            print(bookPath)
            if not os.path.exists(outputPath + "/" + bookPath):
                os.makedirs(outputPath + "/" + bookPath)
            os.rename(file, outputPath + "/" + bookPath + "/" + bookPath)
        else:
            print("INFO: Moving " + getFileName(file) + " to issues folder")
            os.rename(file, issuesPath + "/" + getFileName(file))
            continue

def getFileName(filepath: string):
    return os.path.basename(filepath)

def getAllFiles(path: string):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            if '.epub' in file:
                files.append(os.path.join(r, file))
    print(files)
    return files


def getEpubTitleAndAuthorPath(filepath: string):
    try:
        print("Getting metadata for: " + filepath)
        data = epub_meta.get_epub_metadata(filepath)
        title = data['title'] or "Unknown"
        authors =", ".join(data['authors']) or "Unknown"
        return(title + " - " + authors + ".epub")
    except epub_meta.EPubException as e:
        print(e)
        return None

def getPdfTitleAndAuthorPath(filepath: string):
    try:
        print("Getting metadata for: " + filepath)
        data = pdfx.PDFx(filepath)
        title = data.get_title() or "Unknown"
        authors = data.get_authors() or "Unknown"
        return(title + " - " + authors + ".pdf")
    except pdfx.PDFxException as e:
        print(e)
        return None    


main()