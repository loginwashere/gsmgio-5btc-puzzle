from itertools import permutations, combinations
from multiprocessing import Pool, RLock
import json
import os
import numpy as np
import chardet
import base64
import re
import requests
import time
from bitcoinlib.keys import Key
from ecdsa import SigningKey, SECP256k1
import binascii

# Constants
dbbib = "dbbibfbhccbegbihabebeihbeggegebebbgehhebhhfbabfdhbeffcdbbfcccgbfbeeggecbedcibfbffgigbeeeabe"
faed = "faedggeedfcbdabhhggcadcfeddgfdgbgigaaedggiafaecghggcdaihehahbahigceifgbfgefgaifabifagaegeacgbbeagfggeeggafbacgfcdbeiffaafcidahgdeefghhcggaegdebhhegeghcegadfbdiagefcicggifdcgaaggfbigaicfbhecaecbceiaicebgbgiecdeggfgegaedggfiiciiififhggcgfgdcdggefcbeeigefibgibggghhfbcgifdehedfdagicdbhicgaiedaehahghhcihdghfhbiicecbiichihiiigiddgehhdfdchcbafgfbhaheagegecafehgcfggggcagfhhghbaihidiehhfdeggdgcihggggghadahigigbgecgedfcdggaccdehiicigfbffhggaeidbbeibbeiifdgfdhieeeieeecifdgdahdiggfhegfiaffiggbcbcehceabfbedbiibfbfdedeehgigfaaiggagbeiichiedifbehgbccahhbiibibbibdcbahaidhfahiihic"
base9_chars = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']


# Set the save directory
save_dir = r'F:\Users\Gary Barbour II\Downloads'
save_dir = r'D:\GSMG'

# Update file paths to save in the specified directory
permutations_file = os.path.join(save_dir, 'evaluated_permutations.json')
position_file = os.path.join(save_dir, 'last_position.json')
output_file = os.path.join(save_dir, 'DBBIBFAED_BITLENGTH_ANALYSIS_')
decrypt_file = os.path.join(save_dir, 'DBBIBFAED_DECRYPTIONS_')

#keywords = ["blue", "matrix", "yellow", "prime", "sum", "list", "and", "the", "door", "salvation", "zion", "her", "trinity"]
#keywords = ["blue", "matrix", "yellow", "prime", "list", "door", "salvation", "zion", "trinity", "bank"]
keywords = ["salvation", "zion", "trinity", "bank","looking", "bitcoin", "btc"]

#hexadecimal
divisible_by_4_mapping = {
    '0000': '0', '0001': '1', '0010': '2', '0011': '3', '0100': '4',
    '0101': '5', '0110': '6', '0111': '7', '1000': '8', '1001': '9',
    '1010': 'a', '1011': 'b', '1100': 'c', '1101': 'd', '1110': 'e',
    '1111': 'f'
}

#basically a-z, numbers may be punctuation etc.
divisible_by_5_mapping = {
    '00000': 'a', '00001': 'b', '00010': 'c', '00011': 'd', '00100': 'e',
    '00101': 'f', '00110': 'g', '00111': 'h', '01000': 'i', '01001': 'j',
    '01010': 'k', '01011': 'l', '01100': 'm', '01101': 'n', '01110': 'o',
    '01111': 'p', '10000': 'q', '10001': 'r', '10010': 's', '10011': 't',
    '10100': 'u', '10101': 'v', '10110': 'w', '10111': 'x', '11000': 'y',
    '11001': 'z', '11010': '0', '11011': '1', '11100': '2', '11101': '3',
    '11110': '4', '11111': '5'
}

#I was probably trying something specific, not used by default
divisible_by_5_mapping_custom = {
    '00000': 'a', '00001': '3', '00010': 'c', '00011': 'd', '00100': 'e',
    '00101': 'f', '00110': 'g', '00111': 'h', '01000': 'i', '01001': 'j',
    '01010': 'w', '01011': 'l', '01100': 'm', '01101': 'n', '01110': 'o',
    '01111': 'p', '10000': 'q', '10001': 'r', '10010': 's', '10011': 't',
    '10100': 'u', '10101': 'v', '10110': 'k', '10111': 'e', '11000': 'y',
    '11001': 'z', '11010': '0', '11011': 'l', '11100': '2', '11101': 'b',
    '11110': '4', '11111': '5'
}

#BASE64 charset, sans '=' padding bit
divisible_by_6_mapping = {
    '000000': 'A', '000001': 'B', '000010': 'C', '000011': 'D', '000100': 'E',
    '000101': 'F', '000110': 'G', '000111': 'H', '001000': 'I', '001001': 'J',
    '001010': 'K', '001011': 'L', '001100': 'M', '001101': 'N', '001110': 'O',
    '001111': 'P', '010000': 'Q', '010001': 'R', '010010': 'S', '010011': 'T',
    '010100': 'U', '010101': 'V', '010110': 'W', '010111': 'X', '011000': 'Y',
    '011001': 'Z', '011010': 'a', '011011': 'b', '011100': 'c', '011101': 'd',
    '011110': 'e', '011111': 'f', '100000': 'g', '100001': 'h', '100010': 'i',
    '100011': 'j', '100100': 'k', '100101': 'l', '100110': 'm', '100111': 'n',
    '101000': 'o', '101001': 'p', '101010': 'q', '101011': 'r', '101100': 's',
    '101101': 't', '101110': 'u', '101111': 'v', '110000': 'w', '110001': 'x',
    '110010': 'y', '110011': 'z', '110100': '0', '110101': '1', '110110': '2',
    '110111': '3', '111000': '4', '111001': '5', '111010': '6', '111011': '7',
    '111100': '8', '111101': '9', '111110': '+', '111111': '/'
}


# Generate all binary chunks needed for combinations
def generate_binary_chunks():
    chunks = []
    for bits in range(1, 5):  # For 1 to 4 bits
        for value in range(2**bits):
            chunks.append(format(value, f'0{bits}b'))
    return chunks

# Create combinations of base9 characters mapped to binary chunks
def create_base9_to_binary_combinations(base9_chars, binary_chunks):
    comb_sets = combinations(binary_chunks, len(base9_chars))
    mappings = []
    for comb in comb_sets:
        mapping = {base9_char: chunk for base9_char, chunk in zip(base9_chars, comb)}
        mappings.append(mapping)
    return mappings

#not used, function operates on numeric array not string array
def invert_bits_array(binary_data):
    # Flip each bit by toggling 0 to 1 and 1 to 0 directly
    return [1 - bit for bit in binary_data]

#inverts 1/0 in binary strings
def invert_bits(binary_string):
    # Invert each bit by replacing '1' with '0' and '0' with '1'
    return ''.join('1' if bit == '0' else '0' for bit in binary_string)


#created all permutations of base9 orderings for mixing letters in mapping
def mix_mapping(mapping):
    keys = list(mapping.keys())
    mixed_mappings = []
    # Generate all permutations of the digits 012345678
    digit_permutations = permutations('012345678')
    # Iterate through each permutation
    for digits in digit_permutations:
        # Create a new mapping using the current permutation as index
        mixed_mapping = {keys[int(digits[i])]: mapping[keys[i]] for i in range(len(keys))}
        # Add the mixed mapping to the list
        mixed_mappings.append(mixed_mapping)
    return mixed_mappings


# Load saved permutation states, depricated. everything is stored in output csv's now
def load_saved_permutations():
    if os.path.exists(permutations_file):
        with open(permutations_file, 'r') as f:
            try:
                print("Loaded previously evaluated permutations from file.")
                return json.load(f)
            except json.JSONDecodeError:
                print("Evaluated permutations file is empty or corrupted. Starting fresh.")
    print("No previously evaluated permutations found.")
    return {}

# Save evaluated permutations to a file, depricated. everything is stored in output csv's now
def save_permutations(permutations_dict):
    with open(permutations_file, 'w') as f:
        json.dump(permutations_dict, f)
    print("Saved evaluated permutations to file.")

# Load last processed position to continue from, NOT USED IN THIS VERSION - JUST SEND IT TO THE END
def load_last_position():
    if os.path.exists(position_file):
        with open(position_file, 'r') as f:
            try:
                data = json.load(f)
                print("Loaded last processing position from file.")
                return data
            except json.JSONDecodeError:
                print("Last position file is empty or corrupted. Starting from the beginning.")
    print("No last position file found. Starting from the beginning.")
    return None

# Save current processing position to file, NOT USED IN THIS VERSION - JUST SEND IT TO THE END
def save_last_position(position_data):
    with open(position_file, 'w') as f:
        json.dump(position_data, f)
    #print(f"Saved current processing position: {position_data}")

# apply defined mapping of numBits (divisible_by) bits to chars
def map_bits_to_chars(binary_output, divisible_by):
    # Initialize an empty string to store the mapped characters
    mapped_chars = ''
    # Determine the mapping dictionary based on the divisible-by category
    if divisible_by == 4:
        mapping_dict = divisible_by_4_mapping
        chunk_size = 4        
        if len(binary_output) == 64:
            monitor_wallet_balance(binary_output)
    elif divisible_by == 5:
        mapping_dict = divisible_by_5_mapping
        chunk_size = 5
    elif divisible_by == 6:
        mapping_dict = divisible_by_6_mapping
        chunk_size = 6    
    elif divisible_by == 7:
        # Convert 7 bits to decimal and then to ASCII
        mapped_chars = ''.join(chr(int(binary_output[i:i+7], 2)) for i in range(0, len(binary_output), 7))
        return mapped_chars
    elif divisible_by == 8:
        # Convert 8 bits to decimal and then to ASCII
        mapped_chars = ''.join(chr(int(binary_output[i:i+8], 2)) for i in range(0, len(binary_output), 8))
        return mapped_chars
    else:
        # You can define mappings for other divisible-by categories in a similar manner
        return None  # For now, return None if divisible-by category is not supported
    # Group the binary output into chunks of chunk_size
    binary_chunks = [binary_output[i:i+chunk_size] for i in range(0, len(binary_output), chunk_size)]


    # Map each chunk to a character using the mapping dictionary PROBABLY MORE EFFICIENT OPTIONS FOR THIS
    for chunk in binary_chunks:
        if chunk not in mapping_dict:
            print(f"mapping error with: {chunk}")
        mapped_chars += mapping_dict.get(chunk, '?')  # Use '?' as a placeholder for unknown mappings

    return mapped_chars

# CURRENTLY USED IN 4BIT MAPPING ONLY TO CONVERT HEX TO OTHER AS AND WHERE POSSIBLE
def hex_to_ascii(hex_string):
    # Convert hex string to bytes, preserving all data without modification
    try:
        bytes_object = bytes.fromhex(hex_string)
    except ValueError:
        # Return None if the hex string is invalid
        return None

    # Try decoding using ASCII, UTF-8, and alternative EBCDIC encoding options
    try:
        return bytes_object.decode('ascii')
    except UnicodeDecodeError:
        pass

    try:
        return bytes_object.decode('utf-8')
    except UnicodeDecodeError:
        pass

    try:
        return bytes_object.decode('cp500')  # Use more widely supported EBCDIC encoding
    except UnicodeDecodeError:
        pass

    try:
        return bytes_object.decode('cp037')  # Another common EBCDIC variant
    except UnicodeDecodeError:
        pass

    # If decoding is unsuccessful with the above, return the raw bytes as a string of hex characters
    return hex_string  # This preserves the original hex representation without any conversion




def private_key_to_address(hex_key):
    try:
        # Convert hex key to bytes
        private_key_bytes = binascii.unhexlify(hex_key)
        
        # Initialize the private key from bytes
        signing_key = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        verifying_key = signing_key.get_verifying_key()
        
        # Generate the Bitcoin address (placeholder function, may require additional steps)
        btc_address = '1' + verifying_key.to_string().hex()[:33]  # Simplified example
        return btc_address
    
    except Exception as e:
        print(f"Error generating address: {e}")
        return None

def check_btc_balance(address):
    """
    Check the balance of a Bitcoin address using a public API.
    """
    try:
        response = requests.get(f'https://blockchain.info/q/addressbalance/{address}')
        response.raise_for_status()  # Raise error for bad status codes
        balance_satoshi = int(response.text)
        balance_btc = balance_satoshi / 1e8  # Convert from satoshi to BTC
        return balance_btc
    except requests.RequestException as e:
        print(f"Error checking balance: {e}")
        input("Press Enter to continue...")#DEBUG
        return None

def monitor_wallet_balance(private_key_hex):
    """
    Convert private key to address, check balance, and pause if non-zero.
    """
    address = private_key_to_address(private_key_hex)
    if address is None:
        #print("Invalid private key. Cannot generate address.")
        return
    
    #print(f"Generated address: {address}")
    while True:
        balance = check_btc_balance(address)
        if balance is not None:
            print(f"Balance for {address}: {balance} BTC")
            if balance > 0:
                print("Non-zero balance detected! Pausing program.")
                input("Press Enter to continue...")
                break
        #else:
        #    print("Failed to retrieve balance.")
        
        # Sleep to avoid rapid, repeated requests
        time.sleep(0.1)





def detect_and_decode(data):
    # Detect encoding with chardet
    result = chardet.detect(data)
    encoding = result['encoding']

    # Decode using the detected encoding, with 'ignore' for non-decodable bytes
    return data.decode(encoding, errors='ignore') if encoding else None

def validate_and_decode_base64(base64_string):
    if not base64_string: return None
    """
    Validates if the provided string is a valid Base64 encoded string.
    Returns the decoded version of the string if valid; otherwise, returns None.
    """
    if len(base64_string) % 4 != 0:
        return None

    base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
    if not base64_pattern.match(base64_string):
        return None

    try:
        # Decode Base64 to bytes
        decoded_bytes = base64.b64decode(base64_string, validate=True)
        
        # Attempt to decode to UTF-8 without throwing an error if it fails
        decoded_string = decoded_bytes.decode('utf-8', errors='strict')
        return decoded_string
    
    except (base64.binascii.Error, UnicodeDecodeError):
        # Return None if any decoding issue occurs
        return None



def process_combinations_and_permutations(combinations_chunk, last_position, evaluated_permutations):
    process_id = os.getpid()
    print(f"[Process {process_id}] Starting processing chunk with {len(combinations_chunk)} combinations.")

    # Determine starting position in case of resume
    start_position = last_position or {"combination_index": 0, "permutation_index": 0}

    # Main loop over combinations in the chunk
    for comb_index, combination in enumerate(combinations_chunk):
        # Skip to the saved combination index if resuming
        if comb_index < start_position["combination_index"]:
            print(f"[Process {process_id}] Skipping combination {comb_index} (already processed)")
            continue

        # Sort combination lengths to create a unique tuple key for evaluated permutations
        comb_tuple = tuple(sorted(len(value) for value in combination.values()))  
        # Ensure evaluated_permutations[comb_tuple] is a set for efficient lookups
        if comb_tuple not in evaluated_permutations:
            evaluated_permutations[comb_tuple] = set()
        else: continue

        # Loop over permutations within each combination
        for perm_index, perm in enumerate(permutations(combination)):
            # If resuming, skip to the saved permutation index within the combination
            if (comb_index == start_position["combination_index"] and
                    perm_index < start_position["permutation_index"]):
                continue  # Skip already processed permutations within the saved combination

            """# Save progress intermittently
            if perm_index % 1000 == 0:
                current_position = {"combination_index": comb_index, "permutation_index": perm_index}
                save_last_position(current_position)
                #print(f"[Process {process_id}] Saved progress at combination {comb_index}, permutation {perm_index}")#"""


            # Generate binary strings for dbbib and faed based on current permutation
            permutation = {base9_chars[i]: combination[char] for i, char in enumerate(perm)}
            # Check if this permutation has already been evaluated

            # Generate perm_tuple by sorting the lengths of the binary values in permutation
            perm_tuple = tuple(sorted(len(value) for value in permutation.values()))

            #if perm_tuple in evaluated_permutations[comb_tuple]:
            #    continue  # Skip if permutation has been evaluated


            # Generate binary strings by concatenating the binary values directly from `permutation`
            binary_string_dbbib = ''.join(permutation[char] for char in dbbib if char in permutation)
            binary_string_faed = ''.join(permutation[char] for char in faed if char in permutation)
            # Calculate the lengths of the binary strings once
            len_dbbib = len(binary_string_dbbib)
            len_faed = len(binary_string_faed)


            # Initialize a dictionary to hold only valid lengths
            #lengths = {}

            # Check for each bit length and process immediately if valid
            if len_dbbib % 4 == 0 and len_faed % 4 == 0:# Convert to integer arrays where each element is a single bit (0 or 1)
                dbbib_len, faed_len = len_dbbib // 4, len_faed // 4
                if dbbib_len % 2 == 0 and faed_len % 2 == 0:
                    #binary_data_dbbib = [int(bit) for bit in binary_string_dbbib]
                    #binary_data_faed = [int(bit) for bit in binary_string_faed]
                    save_result(4, permutation, evaluated_permutations, comb_tuple, perm_tuple)
                    decrypt_results(4, binary_string_dbbib, binary_string_faed, dbbib_len, faed_len, permutation)

            if len_dbbib % 5 == 0 and len_faed % 5 == 0:
                dbbib_len, faed_len = len_dbbib // 5, len_faed // 5
                save_result(5, permutation, evaluated_permutations, comb_tuple, perm_tuple)
                decrypt_results(5, binary_string_dbbib, binary_string_faed, dbbib_len, faed_len, permutation)

            if len_dbbib % 6 == 0 and len_faed % 6 == 0:
                dbbib_len, faed_len = len_dbbib // 6, len_faed // 6
                save_result(6, permutation, evaluated_permutations, comb_tuple, perm_tuple)
                decrypt_results(6, binary_string_dbbib, binary_string_faed, dbbib_len, faed_len, permutation)

            if len_dbbib % 7 == 0 and len_faed % 7 == 0:
                dbbib_len, faed_len = len_dbbib // 7, len_faed // 7
                save_result(7, permutation, evaluated_permutations, comb_tuple, perm_tuple)
                decrypt_results(7, binary_string_dbbib, binary_string_faed, dbbib_len, faed_len, permutation)

            if len_dbbib % 8 == 0 and len_faed % 8 == 0:
                dbbib_len, faed_len = len_dbbib // 8, len_faed // 8
                save_result(8, permutation, evaluated_permutations, comb_tuple, perm_tuple)
                decrypt_results(8, binary_string_dbbib, binary_string_faed, dbbib_len, faed_len, permutation)

            """# Filter valid bit lengths and write each valid result immediately
            for bit, (dbbib_len, faed_len) in lengths.items():
                if int(dbbib_len) == dbbib_len and int(faed_len) == faed_len:
                    # Create the human-readable string for this result
                    human_readable_result = f"{bit}bit, DBBI: {dbbib_len}, FAED: {faed_len}, map: {perm_tuple}, order: {perm}"
                    
                    # Write the result directly to the file
                    with open(output_file, 'a') as f:
                        f.write(f"{bit}, {dbbib_len}, {faed_len}, {perm_tuple}, \"{human_readable_result}\"\n")
                    
                    # Mark permutation as evaluated to avoid duplicates
                    evaluated_permutations[comb_tuple][perm_tuple] = True
                    print(f"{bit} bit: DBBIB {dbbib_len}, FAED {faed_len}, map {perm_tuple}, order: {perm}")#"""

    print(f"[Process {process_id}] Finished processing chunk.")


# Define global variables and lock
lock = None  # will be initialized in initializer

def initialize_lock(l):
    global lock
    lock = l

import chardet

def reverse_bits_of_string(input_string, encoding='ascii'):
    if not input_string: return None
    # Encode the input string into bytes
    try:
        byte_data = input_string.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        print(f"Encoding '{encoding}' failed, attempting UTF-8 instead.")
        encoding = 'utf-8'
        byte_data = input_string.encode(encoding)

    # Convert each byte to its binary representation, concatenate into a single bit string
    bit_string = ''.join(f'{byte:08b}' for byte in byte_data)
    
    # Reverse the entire bit string
    reversed_bit_string = bit_string[::-1]
    
    # Convert the reversed bit string back to bytes
    reversed_bytes = int(reversed_bit_string, 2).to_bytes(len(byte_data), byteorder='big')
    
    # Attempt to decode back to a string using the initial encoding
    try:
        return reversed_bytes.decode(encoding)
    except UnicodeDecodeError:
        # Use chardet to detect encoding if the initial decode fails
        detected_encoding = chardet.detect(reversed_bytes)['encoding']
        if detected_encoding:
            try:
                return reversed_bytes.decode(detected_encoding)
            except UnicodeDecodeError:
                pass
        # If all decoding attempts fail, return a hex representation of the bytes as a fallback
        return None#reversed_bytes.hex()




def decrypt_results(numBits, binary_string_dbbib, binary_string_faed, dbbib_len, faed_len, permutation):#, binary_string_dbbib, binary_string_faed):


    binary_output_reversed_dbbib = binary_string_dbbib[::-1]
    binary_output_reversed_faed = binary_string_faed[::-1]

    if numBits == 4:
        dbbib_len //= 2
        faed_len //= 2
        map_bits_output_dbbib = hex_to_ascii(map_bits_to_chars(binary_string_dbbib, numBits))
        map_bits_output_faed = hex_to_ascii(map_bits_to_chars(binary_string_faed, numBits))
        map_bits_output_reversed_dbbib = hex_to_ascii(map_bits_to_chars(binary_output_reversed_dbbib, numBits))
        map_bits_output_reversed_faed = hex_to_ascii(map_bits_to_chars(binary_output_reversed_faed, numBits))

        # Check if alphanumeric and save each valid pair
        if map_bits_output_dbbib.isalnum():
            save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_dbbib, map_bits_output_faed)
            
        if map_bits_output_reversed_dbbib.isalnum():
            save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_reversed_dbbib, map_bits_output_reversed_faed)
   
        if map_bits_output_dbbib and map_bits_output_faed:
            if any(keyword in map_bits_output_dbbib.lower() for keyword in keywords) or any(keyword in map_bits_output_faed.lower() for keyword in keywords):
                save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_dbbib, map_bits_output_faed)    
                 
        if map_bits_output_reversed_dbbib and map_bits_output_reversed_faed:
            if any(keyword in map_bits_output_reversed_dbbib.lower() for keyword in keywords) or any(keyword in map_bits_output_reversed_faed.lower() for keyword in keywords):
                save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_reversed_dbbib, map_bits_output_reversed_faed) 

    else:
        map_bits_output_dbbib = (map_bits_to_chars(binary_string_dbbib, numBits))
        map_bits_output_faed = (map_bits_to_chars(binary_string_faed, numBits))
        map_bits_output_reversed_dbbib = (map_bits_to_chars(binary_output_reversed_dbbib, numBits))
        map_bits_output_reversed_faed = (map_bits_to_chars(binary_output_reversed_faed, numBits))

        if map_bits_output_dbbib and map_bits_output_faed:
            if any(keyword in map_bits_output_dbbib.lower() for keyword in keywords) or any(keyword in map_bits_output_faed.lower() for keyword in keywords):
                save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_dbbib, map_bits_output_faed)    
                
        if map_bits_output_reversed_dbbib and map_bits_output_reversed_faed:
            if any(keyword in map_bits_output_reversed_dbbib.lower() for keyword in keywords) or any(keyword in map_bits_output_reversed_faed.lower() for keyword in keywords):
                save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_reversed_dbbib, map_bits_output_reversed_faed) 

        if numBits > 5:
            
            map_bits_output_dbbib_base64 = validate_and_decode_base64(map_bits_output_dbbib)
            map_bits_output_faed_base64 = validate_and_decode_base64(map_bits_output_faed)
            map_bits_output_reversed_dbbib_base64 = validate_and_decode_base64(map_bits_output_reversed_dbbib)
            map_bits_output_reversed_faed_base64 = validate_and_decode_base64(map_bits_output_reversed_faed)

            check_base64_outputs(numBits, dbbib_len, faed_len, permutation, map_bits_output_dbbib_base64, map_bits_output_faed_base64)
            check_base64_outputs(numBits, dbbib_len, faed_len, permutation, map_bits_output_reversed_dbbib_base64, map_bits_output_reversed_faed_base64)



def check_base64_outputs(numBits, dbbib_len, faed_len, permutation, map_bits_output_dbbib, map_bits_output_faed):
    if map_bits_output_dbbib and map_bits_output_faed:
        #if map_bits_output_dbbib.isalnum():
        save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_dbbib, map_bits_output_faed)

        #if any(keyword in map_bits_output_dbbib.lower() for keyword in keywords) or any(keyword in map_bits_output_faed.lower() for keyword in keywords):
        #    save_result_decrypt(numBits, dbbib_len, faed_len, permutation, map_bits_output_dbbib, map_bits_output_faed)


def save_result(bit, permutation, evaluated_permutations, comb_tuple, perm_tuple):
    # Create a local lock for each write operation
    global lock
    
    #human_readable_result = f"{bit}bit, DBBI: {dbbib_len} chars, FAED: {faed_len} chars, map: {permutation}, order: {perm}"

    # Define file name based on numBits
    output_file_full = f'{output_file}{bit}.csv'

    with lock:  # Acquire the lock locally before each write
        with open(output_file_full, 'a') as f:
            f.write(f"{permutation}\n")
    
    # After evaluating, add perm_tuple to mark it as evaluated
    evaluated_permutations[comb_tuple].add(perm_tuple)
    #print(f"{bit} bit: DBBIB {dbbib_len}, FAED {faed_len}, map {permutation}, order: {perm}")

def save_result_decrypt(bit, dbbib_len, faed_len, permutation, map_bits_output_dbbib, map_bits_output_faed):
    global lock
    
    # Define file name based on numBits
    decrypt_file_full = f'{decrypt_file}{bit}.csv'
    
    # Create the human-readable result
    human_readable_result = (
        f"{bit}bit, DBBI ({dbbib_len}):,\n{map_bits_output_dbbib},\n"
        f"FAED ({faed_len}):,\n{map_bits_output_faed},\n"
        f"map: {permutation}\n"
    )

    # Write the result to the specified file
    with lock:
        with open(decrypt_file_full, 'a', encoding='utf-8') as f:
            f.write(f"\"{human_readable_result}\"\n")
    
    # Mark permutation as evaluated
    #evaluated_permutations[comb_tuple] += perm_tuple#[tuple(permutation.values())] = True
    print(f"{map_bits_output_dbbib}\n{map_bits_output_faed}\n")





# Main function for parallel execution
def main():
    #from multiprocessing import Pool
    global lock
    lock = RLock()  # Initialize a single RLock
    # Generate all possible combinations for base9-to-binary mappings
    binary_chunks = generate_binary_chunks()
    all_combinations = create_base9_to_binary_combinations(base9_chars, binary_chunks)
    print(f"Generated {len(all_combinations)} base9-to-binary combinations.")
    # Load previously saved permutations and last position
    evaluated_permutations = load_saved_permutations()
    last_position = 0#load_last_position()

    # Define the number of processes based on available CPU cores
    num_workers = 10  # Adjust based on CPU core count
    # Split all_combinations into `num_workers` chunks
    combination_chunks = [list(chunk) for chunk in np.array_split(all_combinations, num_workers)]

    # Now each chunk in combination_chunks should have approximately len(all_combinations) / num_workers elements
    print(f"Total combinations: {len(all_combinations)}")
    print(f"Number of chunks: {len(combination_chunks)}")
    print(f"Size of each chunk: {[len(chunk) for chunk in combination_chunks]}")

    print(f"Processing {len(all_combinations)} combinations on {num_workers} cores.")

    # Initialize Pool with lock initializer
    with Pool(processes=num_workers, initializer=initialize_lock, initargs=(lock,)) as pool:
        worker_args = [(chunk, last_position, evaluated_permutations) for chunk in combination_chunks]
        pool.starmap(process_combinations_and_permutations, worker_args)

    with open(output_file, 'a') as f:
        f.write("PROCESS COMPLETED SUCCESSFULLY\n")
    # Save evaluated permutations after processing all chunks
    save_permutations(evaluated_permutations)

    # Clear last position after successful run
    if os.path.exists(position_file):
        os.remove(position_file)
        print("Removed last position file after successful run.")

if __name__ == '__main__':
    main()
