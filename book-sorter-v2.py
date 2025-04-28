#!/usr/bin/env python3
"""
Organize ebooks by <Title> - <Author>.

Default behaviour   : hard-link (like  `cp -lnr`)
Other modes         : --mode copy   | --mode symlink
Source directory    : /mnt/storage/Downloads/Completed Downloads
Destination root    : /mnt/storage/Books/Organized

Designed for cron; runs idempotently (skips files already linked).
Requires calibre's `ebook-meta` CLI and the Python 'unidecode' package.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from unicodedata import normalize
import json, diskcache, google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SRC_ROOT  = Path("/mnt/storage/Downloads/Completed Downloads")
DST_ROOT  = Path("/mnt/storage/Books/Organized")
VALID_EXT = {".epub", ".mobi", ".azw3", ".pdf"}
VERBOSE = False  # Global flag for verbose output

CACHE = diskcache.Cache('/tmp/gemini_title_cache')   # or anywhere writable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = genai.GenerativeModel("gemini-pro-vision-lite-2")  # Flash Lite 2.0

MAX_DIR_CHARS = 120     # keep the previous limit

slug_rx   = re.compile(r"[^\w\s-]")
space_rx  = re.compile(r"[\s_]+")

def slug(text: str) -> str:
    text = normalize("NFKD", text).encode("ascii", "ignore").decode()
    return space_rx.sub(" ", slug_rx.sub("", text).strip())

def smart_slug(title: str, author: str) -> str:
    """
    Ask Gemini Flash Lite 2.0 for a short, clean folder name.
    Falls back to purely local slug() if the call fails.
    """
    raw = f"{title} - {author}"
    if not raw:
        return raw

    # 1) cache hit?
    if raw in CACHE:
        return CACHE[raw]

    try:
        prompt = (
            "Produce a concise, filesystem-safe folder name in ASCII no longer "
            "than 100 characters for the following book:\n\n"
            f"Title: {title}\nAuthor(s): {author}\n\n"
            "Return **only** the folder name, no punctuation or quotes."
        )
        resp = MODEL.generate_content(prompt, safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
        ])
        suggestion = resp.text.strip()
        # basic sanitation in case the model sneaks punctuation
        suggestion = slug(suggestion)[:MAX_DIR_CHARS]
        # store + return
        CACHE[raw] = suggestion
        return suggestion
    except GoogleAPIError:
        # network, quota, etc.
        return slug(raw)[:MAX_DIR_CHARS]

def ebook_meta(path: Path) -> tuple[str | None, str | None]:
    try:
        out = subprocess.check_output(["ebook-meta", str(path)], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: ebook-meta failed for {path}: {e}", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"Error: Unexpected exception in ebook-meta for {path}: {e}", file=sys.stderr)
        return None, None
    
    t = re.search(r"^Title\s*:\s*(.+)$", out, re.M)
    a = re.search(r"^Author\(s\)\s*:\s*(.+)$", out, re.M)
    return (t.group(1).strip() if t else None,
            a.group(1).strip() if a else None)

def fallback_meta(path: Path) -> tuple[str | None, str | None]:
    m = re.match(r"(.+?)\s*-\s*(.+?)\.[^.]+$", path.name)
    return (m.group(1), m.group(2)) if m else (None, None)

def should_ignore(path: Path) -> bool:
    """Check if a path should be ignored based on name."""
    return "Masterclass" in str(path)

def ensure_link(src: Path, dst: Path, mode: str):
    if dst.exists():
        # If the destination already exists, assume it's correct and return.
        # This handles idempotency.
        if VERBOSE:
            print(f"Skipping: {dst} already exists")
        return

    # Destination does not exist. Create link/copy based on mode.
    try:
        if mode == "copy":
            # Ensure source exists before copying
            if not src.exists():
                 print(f"Warning: Source file {src} not found, cannot copy to {dst}", file=sys.stderr)
                 return
            shutil.copy2(src, dst)
            if VERBOSE:
                print(f"Copied: {src} to {dst}")
        elif mode == "symlink":
            # Let symlink_to raise FileNotFoundError if src is gone
            dst.symlink_to(src)
            if VERBOSE:
                print(f"Symlinked: {src} to {dst}")
        else:  # hard-link (default)
            # Let link raise FileNotFoundError if src is gone
            os.link(src, dst)
            if VERBOSE:
                print(f"Hardlinked: {src} to {dst}")

    except OSError as e:
        # Specifically handle cross-device link error for hardlink mode
        if mode == "hardlink" and e.errno == 18: # errno 18 is EXDEV (Cross-device link)
            print(f"Info: Cross-device link attempt for {src}. Falling back to copy.", file=sys.stderr)
            try:
                # Ensure source exists before copying
                if not src.exists():
                     print(f"Warning: Source file {src} not found, cannot copy to {dst}", file=sys.stderr)
                     return
                shutil.copy2(src, dst)
                if VERBOSE:
                    print(f"Fallback copied: {src} to {dst}")
            except Exception as copy_e:
                print(f"Error: Fallback copy failed for {src} to {dst}: {copy_e}", file=sys.stderr)
        # Handle potential FileNotFoundError if src disappeared between checks
        elif e.errno == 2: # errno 2 is ENOENT (No such file or directory)
            print(f"Warning: Source file {src} not found during {mode} operation for {dst}.", file=sys.stderr)
        else:
            # Log other unexpected OSErrors
            print(f"Error: Unexpected OSError during {mode} operation for {src} -> {dst}: {e}", file=sys.stderr)
            # Depending on desired behavior, you might want to re-raise e here

    except Exception as e:
        # Catch other potential errors (e.g., permissions)
        print(f"Error: Failed to process {src} -> {dst} (mode: {mode}): {e}", file=sys.stderr)

def process_one(file_path: Path, mode: str):
    try:
        # Skip files with Masterclass in the name
        if should_ignore(file_path):
            if VERBOSE:
                print(f"Ignoring Masterclass file: {file_path}")
            return
            
        # Print which file we're processing if in verbose mode
        if VERBOSE:
            print(f"Processing: {file_path}")
            
        title, author = ebook_meta(file_path)
        if not title or not author:
            title, author = fallback_meta(file_path)
            if VERBOSE and (title and author):
                print(f"Using fallback metadata for {file_path}: '{title}' by '{author}'")
                
        # If we still don't have metadata, put in Unsorted with a warning
        if not title or not author:
            if VERBOSE:
                print(f"Warning: No metadata found for {file_path}, moving to Unsorted", file=sys.stderr)
                
        dir_name = smart_slug(title, author) if title and author else "Unsorted"
        dest_dir = DST_ROOT / dir_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / file_path.name
        ensure_link(file_path, dest_file, mode)
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)

def main():
    global VERBOSE
    parser = argparse.ArgumentParser(description="Organize ebooks")
    parser.add_argument("--mode", choices=["hardlink", "copy", "symlink"],
                        default="hardlink",
                        help="File operation (default = hardlink)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print verbose output")
    parser.add_argument("--files", nargs="+", 
                        help="Specific files to process (default: all in source directory)")
    args = parser.parse_args()
    
    VERBOSE = args.verbose
    mode = "hardlink" if args.mode == "hardlink" else args.mode

    # If specific files are provided, process only those
    if args.files:
        for file_path in args.files:
            file_path = Path(file_path)
            # Skip files with Masterclass in the name
            if should_ignore(file_path):
                if VERBOSE:
                    print(f"Ignoring Masterclass file: {file_path}")
                continue
                
            if file_path.is_file() and file_path.suffix.lower() in VALID_EXT:
                process_one(file_path, mode)
            else:
                print(f"Skipping {file_path}: Not a valid ebook file", file=sys.stderr)
    else:
        # Process all files in the source directory
        for fp in SRC_ROOT.rglob("*"):
            # Skip files and directories with Masterclass in the name
            if should_ignore(fp):
                if VERBOSE:
                    print(f"Ignoring Masterclass path: {fp}")
                continue
                
            if fp.is_file() and fp.suffix.lower() in VALID_EXT:
                process_one(fp, mode)

if __name__ == "__main__":
    if not SRC_ROOT.exists():
        sys.exit(f"Source path {SRC_ROOT} not found")
    main()
