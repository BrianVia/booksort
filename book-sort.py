import os
import sys
import string
import epub_meta
import pdfx
import json

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
        bookPath = ""
        if file.endswith(".epub"):
            bookPath = getEpubTitleAndAuthorPath(file)
        if file.endswith(".pdf"):
            bookPath = getPdfTitleAndAuthorPath(file)

        extension = getFileExtension(file)
        

        # if bookpath is not none and doesn't contain unknown
        if bookPath and "Unknown" not in bookPath:
            print(bookPath)
            if not os.path.exists(outputPath + "/" + bookPath):
                os.makedirs(outputPath + "/" + bookPath)
            print("SUCCESS: Moving " + bookPath)
            os.rename(file, outputPath + "/" + bookPath + "/" + bookPath + extension)
        else:
            print("WARN: Moving " + getFileName(file) + " to issues folder")
            os.rename(file, issuesPath + "/" + getFileName(file))
            continue

def getFileName(filepath: string):
    return os.path.basename(filepath)

def getAllFiles(path: string):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            if file.endswith(".pdf") or file.endswith(".epub"):
                files.append(os.path.join(r, file))
    print(files)
    return files


def getEpubTitleAndAuthorPath(filepath: string):
    try:
        print("Getting metadata for: " + filepath)
        data = epub_meta.get_epub_metadata(filepath)
        title = data['title'] or "Unknown"
        authors =", ".join(data['authors']) or "Unknown"
        return(title + " - " + authors)
    except epub_meta.EPubException as e:
        print(e)
        return None

def getFileExtension(file):
    return os.path.splitext(file)[1]

def getPdfTitleAndAuthorPath(filepath: string):
    try:
        print("Getting metadata for: " + filepath)
        pdf = pdfx.PDFx(filepath)
        metadata = pdf.get_metadata()
        title = metadata.get("Title") or "Unknown"
        authors = metadata.get("Author") or "Unknown"
        print("Got metadata for " + filepath + ": " + title + " - " + authors)
        return(title + " - " + authors)
    except pdfx.exceptions.PDFInvalidError as e:
        print(e)
        return None
    except pdfx.exceptions.PDFExtractionError as e:
        print(e)
        return None
    except pdfx.exceptions.FileNotFoundError as e:
        print(e)
        return None
    

main()