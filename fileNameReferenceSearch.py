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
        "--sourcetypes-no-recursive",
        action='store_false',
        help="Do not search recursively for source files")
    parser.add_argument(
        "--searchtypes", type=str, nargs="*",
        default=[".jsp", ".tag", ".html"],
        help="The file types whose contents should be searched (default: .jsp .tag)")

    return parser


def main():
    parser = init_argparse()
    args = parser.parse_args()

    foundFiles = findFiles(args.sourcepath[0], args.sourcetypes, args.sourcetypes_no_recursive)
    foundFileNames = getFileNames(foundFiles)
    searchFiles = findFiles(args.searchpath[0], args.searchtypes)

    print(f"Found {len(foundFiles)} files with extensions {args.sourcetypes}")
    for file in foundFiles:
        print(file)
    print(f"Searching {len(searchFiles)} files with extensions {args.searchtypes}...")

    usageCounts = searchFilesForUsage(foundFileNames, searchFiles)
    filteredCounts = {k: v for k, v in usageCounts.items() if v == 0}

    print(f"Found {len(filteredCounts)} files with no usages:")
    # print(json.dumps(filteredCounts, indent=4))
    for key in list(filteredCounts.keys()):
        print(f"- {key}")

def findFiles(path, extensions, recursive=True):
    print(f"Searching {path} for files with extensions {extensions}, recursive={recursive}")
    files = []

    for ext in extensions:
        if recursive:
            files.extend(glob.glob(path + '/**/*' + ext, recursive=recursive))
        else:
            files.extend(glob.glob(path + '/*' + ext))

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