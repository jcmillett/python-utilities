import argparse
from fileinput import filename
import sys
import glob
import os
import mmap
import json

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Finds file names in source directory recursively, and then uses search directory to recursively search the content of the files for the files names found.")
    parser.add_argument(
        "sourcepath", type=str, nargs=1,
        help="The source directory to find files names")
    parser.add_argument(
        "searchpath", type=str, nargs=1,
        help="The search directory to search file contents")
    parser.add_argument(
        "--sourcetypes", type=str, nargs="*",
        default=["[!entry][!main][!spec].js"],
        help="The file types whose names should be searched (default: [!entry][!main][!spec].js)")
    parser.add_argument(
        "--searchtypes", type=str, nargs="*",
        default=[".jsp", ".tag"],
        help="The file types whose contents should be searched (default: .jsp .tag)")

    return parser


def main():
    parser = init_argparse()
    args = parser.parse_args()

    foundFiles = findFiles(args.sourcepath[0], args.sourcetypes)
    foundFileNames = getFileNames(foundFiles)
    searchFiles = findFiles(args.searchpath[0], args.searchtypes)

    print(f"Found {len(foundFiles)} files with extensions {args.sourcetypes}")
    print(f"Searching {len(searchFiles)} files with extensions {args.searchtypes}...")

    usageCounts = searchFilesForUsage(foundFileNames, searchFiles)

    print("File usage counts:")
    print(json.dumps(usageCounts, indent=4))

def findFiles(path, extensions):
    files = []

    for ext in extensions:
        files.extend(glob.glob(path + '/**/*' + ext, recursive=True))

    return files

def getFileNames(files):
    filenames = list(map(lambda filepath : os.path.basename(filepath), files))
    filenamesSorted = sorted(filenames, key=str.casefold)
    return filenamesSorted

def searchFilesForUsage(foundFileNames, searchFiles):
    fileUsageCounts = dict.fromkeys(foundFileNames, 0)
    foundFileNamesInBytes = list(map(lambda fileName: str.encode(fileName), foundFileNames))

    for searchFilePath in searchFiles:
        #print(f"Searching file {searchFilePath}")

        if os.stat(searchFilePath).st_size > 0:
            with open(searchFilePath, 'rb', 0) as file, \
                mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                for i, fileNameBytes in enumerate(foundFileNamesInBytes):
                    if s.find(fileNameBytes) > -1:
                        fileName = foundFileNames[i]

                        if fileName in fileUsageCounts:
                            fileUsageCounts[fileName] = fileUsageCounts[fileName] + 1
    
    return fileUsageCounts

if __name__ == "__main__":
    main()