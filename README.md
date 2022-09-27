# booksort
I needed a way to sort and organize my growing library of `.epub` and `.pdf` files on my server.  
Nothing seemed to be fitting the bill, LazyLibrarian seemed like overkill, I didn't want to use Calibre with an unorganized input directory.
So I opted to build it myself (with a little help from the internet)

## Usage
```
python3 <input-dir> <output dir>
```
where `input-dir` is the directory of epub files to sift through (unrecursively).
and `output-dir` is the directory you want them sorted to.

The output directory will then have structure
```
  <title-book-1> - <author-book-1>/
    <title-book-1> - <author-book-1>.epub
```

As this was how I wanted to sort my books.
