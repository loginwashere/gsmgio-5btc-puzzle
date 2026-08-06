def base10_to_baseY(num, base_to):
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # Supports up to base 36
    if num == 0:
        return "0"
    arr = []
    while num:
        num, remainder = divmod(num, base_to)
        arr.append(digits[remainder])
    arr.reverse()
    return ''.join(arr)

def baseX_to_baseY(num_str, base_from, base_to):
    try:
        base10_num = int(num_str, base_from)
        if base_to == 10:
            return str(base10_num)
        else:
            return base10_to_baseY(base10_num, base_to)
    except ValueError:
        return f"Invalid base {base_from} number: {num_str}"


def abc_to_base9(abc_str):
    mapping = {
        'a': '0',
        'b': '1',
        'c': '2',
        'd': '3',
        'e': '4',
        'f': '5',
        'g': '6',
        'h': '7',
        'i': '8',
    }

    result = []
    invalid_characters = []

    for idx, char in enumerate(abc_str):
        if char == ' ':
            continue
        if char in mapping:
            result.append(mapping[char])
        else:
            invalid_characters.append((idx, char))

    if invalid_characters:
        invalid_str = ", ".join([f"position {pos}: '{ch}'" for pos, ch in invalid_characters])
        return f"Invalid characters in input string at {invalid_str}"

    return ''.join(result)

def add_with_rotation_ascii(str1, str2):
    result = []
    len_str1 = len(str1)
    len_str2 = len(str2)
    for i in range(len_str2):
        sum_val = ord(str1[i % len_str1]) + ord(str2[i])
        result.append(chr(sum_val % 256))
    return ''.join(result)

def add_odd_even_reversed(str_val):
    """
    Adds odd-numbered characters to reversed even-numbered characters.
    """
    odd_chars = str_val[::2]
    even_chars_reversed = str_val[1::2][::-1]
    return add_with_rotation_ascii(odd_chars, even_chars_reversed)

# Test
input_str1 = "d b b i b f b h c c b e g b i h a b e b e i h b e g g e g e b e b b g e h h e b h h f b a b f d h b e f f c d b b f c c c g b f b e e g g e c b e d c i b f b f f g i g b e e e a b e "
input_str2 = "f a e d g g e e d f c b d a b h h g g c a d c f e d d g f d g b g i g a a e d g g i a f a e c g h g g c d a i h e h a h b a h i g c e i f g b f g e f g a i f a b i f a g a e g e a c g b b e a g f g g e e g g a f b a c g f c d b e i f f a a f c i d a h g d e e f g h h c g g a e g d e b h h e g e g h c e g a d f b d i a g e f c i c g g i f d c g a a g g f b i g a i c f b h e c a e c b c e i a i c e b g b g i e c d e g g f g e g a e d g g f i i c i i i f i f h g g c g f g d c d g g e f c b e e i g e f i b g i b g g g h h f b c g i f d e h e d f d a g i c d b h i c g a i e d a e h a h g h h c i h d g h f h b i i c e c b i i c h i h i i i g i d d g e h h d f d c h c b a f g f b h a h e a g e g e c a f e h g c f g g g g c a g f h h g h b a i h i d i e h h f d e g g d g c i h g g g g g h a d a h i g i g b g e c g e d f c d g g a c c d e h i i c i g f b f f h g g a e i d b b e i b b e i i f d g f d h i e e e i e e e c i f d g d a h d i g g f h e g f i a f f i g g b c b c e h c e a b f b e d b i i b f b f d e d e e h g i g f a a i g g a g b e i i c h i e d i f b e h g b c c a h h b i i b i b b i b d c b a h a i d h f a h i i h i c"

base_from = 9
base_to = 10 #CHANGE THIS TO YOUR DESIRED BASE

def add_single_mode(str_val):
    """
    Adds each even character with its subsequent odd character in single mode.
    If string length is odd, the last character is added as-is.
    """
    result = []
    len_val = len(str_val)
    
    for i in range(0, len_val - 1, 2): # change the loop step to 2
        sum_val = ord(str_val[i]) + ord(str_val[i+1])
        result.append(chr(sum_val % 256))
    
    # If the length is odd, add the last character
    if len_val % 2 == 1:
        result.append(str_val[-1])
        
    return ''.join(result)

def add_odd_even_reversed(str_val):
    """
    Adds odd-numbered characters to reversed even-numbered characters.
    """
    odd_chars = str_val[::2]
    even_chars_reversed = str_val[1::2][::-1]
    
    # Using min to ensure we don't go out of bounds
    length = min(len(odd_chars), len(even_chars_reversed))
    result = [chr((ord(odd_chars[i]) + ord(even_chars_reversed[i])) % 256) for i in range(length)]
    
    # If there are remaining characters in odd_chars, append them
    if len(odd_chars) > len(even_chars_reversed):
        result.extend(odd_chars[length:])
        
    return ''.join(result)

def calculate_ioc(text):
    freq = {}
    
    # Count each character's frequency
    for char in text:
        if char in freq:
            freq[char] += 1
        else:
            freq[char] = 1
    
    total_chars = len(text)
    
    # Calculate the numerator using the formula: n(n-1) for each character
    numerator = sum([count * (count - 1) for count in freq.values()])
    
    ioc = numerator / (total_chars * (total_chars - 1))
    
    return ioc



converted_number1 = abc_to_base9(input_str1)
converted_number2 = abc_to_base9(input_str2)

result_number1 = baseX_to_baseY(converted_number1, base_from, base_to)
result_number2 = baseX_to_baseY(converted_number2, base_from, base_to)

if "Invalid" not in result_number1 and "Invalid" not in result_number2:
    # Intertwine Mode
    sum_result_intertwine = add_with_rotation_ascii(str(result_number1), str(result_number2))
    distinct_characters_intertwine = len(set(sum_result_intertwine))
    
    # Intertwine with reversed first string
    sum_result_reversed = add_with_rotation_ascii(str(result_number1[::-1]), str(result_number2))
    distinct_characters_reversed = len(set(sum_result_reversed))
    
    # Single Mode for result_number1
    sum_result_single1 = add_single_mode(str(result_number1))
    distinct_characters_single1 = len(set(sum_result_single1))
    
    # Single Mode for result_number2
    sum_result_single2 = add_single_mode(str(result_number2))
    distinct_characters_single2 = len(set(sum_result_single2))
    
    # Odd-Even Mode for result_number1
    sum_result_odd_even1 = add_odd_even_reversed(str(result_number1))
    distinct_characters_odd_even1 = len(set(sum_result_odd_even1))
    
    # Odd-Even Mode for result_number2
    sum_result_odd_even2 = add_odd_even_reversed(str(result_number2))
    distinct_characters_odd_even2 = len(set(sum_result_odd_even2))
    
    ioc_intertwine = calculate_ioc(sum_result_intertwine)
    ioc_reversed = calculate_ioc(sum_result_reversed)
    ioc_single1 = calculate_ioc(sum_result_single1)
    ioc_single2 = calculate_ioc(sum_result_single2)
    ioc_odd_even1 = calculate_ioc(sum_result_odd_even1)
    ioc_odd_even2 = calculate_ioc(sum_result_odd_even2)

    char_count_intertwine = len(sum_result_intertwine)
    char_count_reversed = len(sum_result_reversed)
    char_count_single1 = len(sum_result_single1)
    char_count_single2 = len(sum_result_single2)
    char_count_odd_even1 = len(sum_result_odd_even1)
    char_count_odd_even2 = len(sum_result_odd_even2)
    
    print(f"Result for dbbid as base {base_to} is: {result_number1}")
    print(f"\nResult for faed as base {base_to} is: {result_number2}")
    print(f"\nSum (Intertwine with dbbib), IOC {ioc_intertwine}, len: {char_count_intertwine}, {distinct_characters_intertwine} distinct chars is: {sum_result_intertwine}")
    #print(f"Number of distinct characters in the sum result (Intertwine): {distinct_characters_intertwine}")
    print(f"\nSum (Intertwine with dbbib string reversed), IOC {ioc_reversed}, len: {char_count_reversed}, {distinct_characters_reversed} distinct chars is: {sum_result_reversed}")
    #print(f"Number of distinct characters in the sum result (Intertwine with dbbib string reversed): {distinct_characters_reversed}")
    print(f"\nSum (Single for dbbib), IOC {ioc_single1}, len: {char_count_single1}, {distinct_characters_single1} distinct chars is: {sum_result_single1}")
    #print(f"Number of distinct characters in the sum result (Single for dbbib): {distinct_characters_single1}")
    print(f"\nSum (Single for faed), IOC {ioc_single2}, len: {char_count_single2}, {distinct_characters_single2} distinct chars is: {sum_result_single2}")
    #print(f"Number of distinct characters in the sum result (Single for faed): {distinct_characters_single2}")
    print(f"\nSum (Odd-Even for dbbib), IOC {ioc_odd_even1}, len: {char_count_odd_even1}, {distinct_characters_odd_even1} distinct chars is: {sum_result_odd_even1}")
    #print(f"Number of distinct characters in the sum result (Odd-Even for dbbib): {distinct_characters_odd_even1}")
    print(f"\nSum (Odd-Even for faed), IOC {ioc_odd_even2}, len: {char_count_odd_even2}, {distinct_characters_odd_even2} distinct chars is: {sum_result_odd_even2}")
    #print(f"Number of distinct characters in the sum result (Odd-Even for faed): {distinct_characters_odd_even2}")    
    print(f"\n(Results for base {base_to} conversion)")
else:
    if "Invalid" in result_number1:
        print(result_number1)
    if "Invalid" in result_number2:
        print(result_number2)




