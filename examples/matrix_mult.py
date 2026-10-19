
# examples/matrix_mult.py

def matrix_multiply(a, b):
    n = len(a)
    result = [[0] * n for _ in range(n)]

    for i in range(n):
        for k in range(n):
            aik = a[i][k]
            for j in range(n):
                result[i][j] += aik * b[k][j]

    return result


def main():
    n = 100

    a = [[i + j for j in range(n)] for i in range(n)]
    b = [[i - j for j in range(n)] for i in range(n)]

    result = matrix_multiply(a, b)

    # Deterministic output for correctness checking.
    print(sum(map(sum, result)))


if __name__ == "__main__":
    main()