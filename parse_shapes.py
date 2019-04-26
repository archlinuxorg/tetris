import re
import pickle


def parseShapesFile(in_file, out_file):
    data = re.sub('\s*', '', open(in_file, "r").read())
    data = re.findall('shape\{(?:(?:[01]*;)+)\}', data)
    data = [re.findall('([01]+);', sh) for sh in data]
    data = [genShapePrototypes([[int(digit) for digit in row] for row in sh]) for sh in data]
    pickle.dump(data, out_file, pickle.HIGHEST_PROTOCOL)


def genShapePrototypes(raw_shape):
    width = len(raw_shape[0])
    result = []
    result.append(raw_shape)
    result.append([[row[i] for row in reversed(raw_shape)] for i in range(0, width)])
    result.append([[item for item in reversed(row)] for row in reversed(result[0])])
    result.append([[item for item in reversed(row)] for row in reversed(result[1])])
    return result

parseShapesFile("shapes", open("prototypes", "w"))

