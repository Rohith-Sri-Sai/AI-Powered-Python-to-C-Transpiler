# examples/matrix_mult.py
def count_primes(limit):
    count = 0
    for num in range(2, limit):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count

def main():
    # A heavy calculation that takes Python a second or two
    result = count_primes(150000)
    print(result)

if __name__ == "__main__":
    main()