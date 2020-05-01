from urllib.parse import urlparse

def main():
    linksFile = "C:\\Data\\AnalyzeLinks\\links.csv"
    resultFile = "C:\\Data\\AnalyzeLinks\\result.csv"

    file = open(linksFile, "r")
    resultFile = open(resultFile, "w+")
    for line in file.readlines():
        parsedUrl = urlparse(line)

        nextSlashPosition = parsedUrl.path.find("/", 1)
        category = parsedUrl.path[1:nextSlashPosition]

        fullLink = line

        wordPosition = parsedUrl.path.find("skandal")

        resultFile.write("{0},{1},{2},{3}".format(parsedUrl.netloc, category, wordPosition, fullLink))

    resultFile.close()
    file.close()

if __name__ == '__main__':
    main()