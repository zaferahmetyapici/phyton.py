import random


def generate_operation_question(operation_name, difficulty="easy"):
    difficulty_key = (difficulty or "easy").lower()

    def random_by_digits(digit_count):
        if digit_count <= 1:
            return random.randint(1, 9)
        return random.randint(10, 99)

    if operation_name is None:
        operation_name = random.choice(["Addition", "Subtraction", "Multiplication", "Division"])
    operation = operation_name.lower()

    if difficulty_key == "easy":
        digits_a, digits_b = 1, 1
    elif difficulty_key == "normal":
        digits_a, digits_b = 2, 1
    else:
        if "mul" in operation or "times" in operation or "div" in operation:
            digits_a, digits_b = 2, 1
        else:
            digits_a, digits_b = 2, 2

    if "add" in operation:
        value_a = random_by_digits(digits_a)
        value_b = random_by_digits(digits_b)
        return f"{value_a} + {value_b} = ?", value_a + value_b

    if "sub" in operation:
        value_a = random_by_digits(digits_a)
        value_b = random_by_digits(digits_b)
        if value_a < value_b:
            value_a, value_b = value_b, value_a
        return f"{value_a} - {value_b} = ?", value_a - value_b

    if "mul" in operation or "times" in operation:
        value_a = random_by_digits(digits_a)
        value_b = random_by_digits(digits_b)
        return f"{value_a} × {value_b} = ?", value_a * value_b

    if "div" in operation:
        if difficulty_key == "easy":
            divisor = random.randint(1, 9)
            quotient = random.randint(1, max(1, 9 // divisor))
            dividend = divisor * quotient
        else:
            divisor = random.randint(2, 9)
            min_quotient = max(1, (10 + divisor - 1) // divisor)
            max_quotient = max(min_quotient, 99 // divisor)
            quotient = random.randint(min_quotient, max_quotient)
            dividend = divisor * quotient
        return f"{dividend} ÷ {divisor} = ?", quotient

    value_a = random_by_digits(1 if difficulty_key == "easy" else 2)
    value_b = random_by_digits(1)
    return f"{value_a} + {value_b} = ?", value_a + value_b


def generate_group_pattern(pattern_group, length=4, difficulty="easy"):
    ranges = {
        "easy": (1, 30),
        "normal": (30, 70),
        "hard": (60, 100),
    }
    range_low, range_high = ranges.get((difficulty or "easy").lower(), (1, 30))

    try:
        normalized = "".join(ch if ch.isdigit() or ch == "-" else "" for ch in (pattern_group or ""))
        values = [int(item) for item in normalized.split("-") if item]
        if values:
            chosen_base = random.choice(values)
            multiplier_min = max(1, (range_low + chosen_base - 1) // chosen_base)
            multiplier_max = max(1, range_high // chosen_base) - (length - 1)

            if multiplier_max >= multiplier_min:
                multiplier = random.randint(multiplier_min, multiplier_max)
            else:
                multiplier = multiplier_min
            return [chosen_base * (multiplier + index) for index in range(length)]
    except Exception:
        pass

    start_value = random.randint(range_low, max(range_low, range_high - (length - 1)))
    return [start_value + index for index in range(length)]
