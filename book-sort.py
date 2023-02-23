import os
import string
import epub_meta
import pdfx

# MACOS paths
# export BOOKSORT_ISSUES_PATH=/Users/bvia/Development/Personal/booksort/issues
# export BOOKSORT_OUTPUT_PATH=/Users/bvia/Development/Personal/booksort/outputs
# export BOOKSORT_INPUT_PATH=/Users/bvia/Development/Personal/booksort/inputs

#Linux paths
# export BOOKSORT_ISSUES_PATH=/mnt/storage/Books/_issues
# export BOOKSORT_OUTPUT_PATH=/mnt/storage/Books/Organized
# export BOOKSORT_INPUT_PATH=/mnt/storage/Books/_unorganized

# Main function - reads environment variables and calls sort_books
def main():
    inputPath = os.environ["BOOKSORT_INPUT_PATH"]
    outputPath = os.environ["BOOKSORT_OUTPUT_PATH"]
    issuesPath = os.environ["BOOKSORT_ISSUES_PATH"]
    sort_books(inputPath, outputPath, issuesPath)
    

# python function to sort epub and pdf files into title-author folders by reading their metadata
def sort_books(inputPath: string, outputPath: string, issuesPath: string):
    files = getAllFiles(inputPath);
    print("INFO: Loaded " + files.count + " files.")
    for file in files:
        TitleAndAuthorString = ""
        if file.endswith(".epub"):
            TitleAndAuthorString = getEpubTitleAndAuthorPath(file)
        if file.endswith(".pdf"):
            TitleAndAuthorString = getPdfTitleAndAuthorPath(file)

        extension = getFileExtension(file)
        

        # if bookpath is not none and doesn't contain unknown
        if TitleAndAuthorString and "Unknown" not in TitleAndAuthorString:
            if not os.path.exists(outputPath + "/" + TitleAndAuthorString):
                os.makedirs(outputPath + "/" + TitleAndAuthorString)
            print("SUCCESS: Moving " + TitleAndAuthorString)
            os.rename(file, outputPath + "/" + TitleAndAuthorString + "/" + TitleAndAuthorString + extension)
            # My desired file output path is <BooksDir>/<Title> - <Author>/<Title> - <Author>.{pdf,epub,etc}
        else:
            print("WARN: Moving " + getFileName(file) + " to issues folder")
            os.rename(file, issuesPath + "/" + getFileName(file))
            continue

# Returns just the file name from a path
# ie, "/unsorted-books/Book.epub" -> "Book.epub"
def getFileName(filepath: string):
    return os.path.basename(filepath)


# Returns all files in a directory
def getAllFiles(path: string):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            if file.endswith(".pdf") or file.endswith(".epub"):
                files.append(os.path.join(r, file))
    print(files)
    return files


# Returns the title and author of an epub file in the format "Title - Author"
def getEpubTitleAndAuthorPath(filepath: string):
    try:
        print("INFO: Getting metadata for: " + filepath)
        data = epub_meta.get_epub_metadata(filepath)
        title = data['title'] or "Unknown"
        authors =", ".join(data['authors']) or "Unknown"
        print("INFO:  v c  Got metadata for " + filepath + ": " + title + " - " + authors)
        return(title + " - " + authors)
    except epub_meta.EPubException as e:
        print(e)
        return None

# Returns the file extension of a file
def getFileExtension(file):
    return os.path.splitext(file)[1]

# Returns the title and author of a pdf file in the format "Title - Author"
def getPdfTitleAndAuthorPath(filepath: string):
    issuesPath = os.environ["BOOKSORT_ISSUES_PATH"]
    file = filepath
    try:
        print("INFO: Getting metadata for: " + filepath)
        pdf = pdfx.PDFx(filepath)
        metadata = pdf.get_metadata()
        title = metadata.get("Title") or "Unknown"
        authors = metadata.get("Author") or "Unknown"
        print("INFO: Got metadata for " + filepath + ": " + title + " - " + authors)
        return(title + " - " + authors)
    except pdfx.exceptions.PDFInvalidError as e:
        print(e)
        print("ERROR: Moving " + getFileName(file) + " to issues folder")
        os.rename(file, issuesPath + "/" + getFileName(file))
        return None
    except pdfx.exceptions.PDFExtractionError as e:
        print(e)
        print("ERROR: Moving " + getFileName(file) + " to issues folder")
        os.rename(file, issuesPath + "/" + getFileName(file))
        return None
    except pdfx.exceptions.FileNotFoundError as e:
        print(e)
        print("ERROR: Moving " + getFileName(file) + " to issues folder")
        os.rename(file, issuesPath + "/" + getFileName(file))
        return None
    

main()