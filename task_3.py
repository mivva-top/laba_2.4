def search(data):
    result = []
    for i in data:
        if i % 7 == 0:
            result.append(i)
    return result

try:
    numbers = list(map(int, input("Введите числа через пробел: ").split()))
    multiples = search(numbers)

    with open("resource/count.txt", "w") as file:
        for num in numbers:
            file.write(str(num) + " ")
except ValueError:
    print("Ошибка: введите числа!")

x = 73 ** 2 + 29
temp_path = "resource/count_tmp.txt"

with open("resource/count.txt", "r") as file, open(temp_path, "w") as temp:
    for line in file:
        processed = []
        for j in line.split():
            num = int(j)
            if num % 7 == 0:
                num = num * 100 / x
            processed.append(str(num))
        temp.write(" ".join(processed) + "\n")

    with open(temp_path, "r") as temp_path, open("resource/count.txt", "w") as file:
        for line in temp_path:
            temp.write(line)
