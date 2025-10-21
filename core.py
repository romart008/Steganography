from abc import ABC, abstractmethod
from PIL import Image
import queue
from decimal import Decimal, getcontext
import numpy as np


#region ABS Class
class SteganographyMedia(ABC):
    def __init__(self, filepath):
        self.filepath = filepath
        self.raw_data = None
        self.metadata = None
        self._load()

    @abstractmethod
    def _load(self):
        """Method for loading data from file"""
        raise NotImplementedError

    @abstractmethod
    def save(self, output_path):
        """Method for saving data into a file"""
        raise NotImplementedError

    def hide(self, message, password):
        """Main method that controlls hiding process"""
        print(f"Hiding '{message}' in {self.filepath} using password '{password}'...")

    def extract(self, password):
        """Main method that controlls extracting process"""
        print(f"Extracting message from {self.filepath} using password '{password}'...")

#region Image

class ImageMedia(SteganographyMedia):

    def _load(self):
        try:
            with Image.open(self.filepath) as img:
                img = img.convert("RGB")
                self.metadata = {'size': img.size, 'mode': img.mode}
                self.raw_data = bytearray(img.tobytes())
        except Exception as e:
            print(f"Failed to load image: {e}")

    def save(self, container: bytearray, output_path: str):
        if container is None:
            print("No data to save.")
            return
        if output_path is None:
            output_path = self.filepath

        print(f"Saving modified image to {output_path}")
        try:
            img = Image.frombytes(self.metadata['mode'], self.metadata['size'], bytes(container))
            img.save(output_path, 'PNG')
        except Exception as e:
            print(f"Failed to save image: {e}")

    #region Hide
    def hide(self, message: str, password_prime: int, stop_sequence: str, message_encryption: str, hide_method: str, p: int, depth:int, output:str):
        print("--- Starting Hiding Process ---")
        
        #   Dissasemble message
        message_bits = list(self._message_to_bitstream(message))
        stop_bits = list(self._message_to_bitstream(stop_sequence))
        
        
        #   Cypher message
        encrypted_bits = np.concatenate((self._message_encryption(message_bits, message_encryption, password_prime),self._message_encryption(stop_bits, message_encryption, password_prime)))

        #   Hide message
        success = self._message_hide(encrypted_bits, hide_method, p, depth, output)
        
        if success:
            print("--- Hiding Process Finished Successfully ---")
        else:
            print("--- Hiding Process Failed ---")

    #region Message
    def _message_to_bitstream(self, text: str):
        """Convert string to bits"""
        for char in text:
            binary_char = format(ord(char), '08b')
            for bit in binary_char:
                yield int(bit)

    def _generate_key_stream(self, prime_number: int, total_bits: int):
        """Generate a bit list from square root of prime number"""
        precision_needed = (total_bits) + 10
        getcontext().prec = precision_needed

        root_decimal = Decimal(prime_number).sqrt()
        root_digits_str = str(root_decimal).split('.')[1]

        bit_count = 0
        for digit_char in root_digits_str:
            if bit_count >= total_bits:
                break
            
            digit = int(digit_char)
            binary_digit_str = bin(digit)[2:]
            
            for bit_char in binary_digit_str:
                if bit_count >= total_bits:
                    break
                yield int(bit_char)
                bit_count += 1

    def _xor_encrypt_stream(self, message_bits: list, key_bitstream):
        """Complete XOR encoding"""
        encrypted = []
        for msg_bit, key_bit in zip(message_bits, key_bitstream):
            encrypted.append(msg_bit ^ key_bit)
        return np.array(encrypted)

    def _message_encryption(self, message_bits: list, message_encryption: str, password_prime: int):
        if message_encryption == 'Binary XOR':
            key_stream = self._generate_key_stream(password_prime, len(message_bits))
            encrypted_bits = self._xor_encrypt_stream(message_bits, key_stream)
            return encrypted_bits
        elif message_encryption == 'None':
            return message_bits
        else:
            print('Invalid Encryption method, or it is now finished yet')

    #region Container
    def build_hiding_matrix(self, p: int):
        """
        Create matrix H with size (p, 2**p - 1) for .
        """
        n = 2**p - 1
        
        columns = []
        for i in range(1, n + 1):
            col_str = format(i, f'0{p}b')
            columns.append([int(bit) for bit in col_str])
    
        matrix_h = np.array(columns, dtype=np.uint8)
        #print(matrix_h)
        return matrix_h
    
    def _LSB_container(self, depth: int):
        raw = np.unpackbits(np.frombuffer(self.raw_data, dtype=np.uint8))
        container = raw.reshape(-1,8)[:, -depth:].flatten()
        return container
        
    def _LSB_return(self, depth: int, container: np.array):
        raw = np.unpackbits(np.frombuffer(self.raw_data, dtype=np.uint8))
        new_img = raw.reshape(-1,8) ; container = container.reshape(-1,depth)
        new_img[:, -depth:] = container
        return bytearray(np.packbits(new_img))

    
    def _message_hide(self, bits_to_hide: list, hide_method, p: int, depth: int, output:str):
        if hide_method == 'LSB':
            container = self._LSB_container(depth)
            container = self._hide_bits_in_data(bits_to_hide, p, container)
            new_img = self._LSB_return(depth, container)
            self.save(new_img, output)
            if new_img:
                return True
            else:
                return False
        else:
            print('Invalid Hiding method, or it is now finished yet')

    def _hide_bits_in_data(self, bits_to_hide: np.array, p: int, container: np.array):
        """
        Hide bits in self.raw_data.
        Return True if succeed, False - if failed.
        """
        n = 2**p - 1

        if (len(bits_to_hide) + p - 1) // p > len(container) // n:
            print("Not enough space to hide message")
            return None

        matrix_h = self.build_hiding_matrix(p)

        padding_needed = (p - len(bits_to_hide) % p) % p
        if padding_needed > 0:
            bits_to_hide = np.pad(bits_to_hide, (0, padding_needed), 'constant')
        chunks = len(bits_to_hide) // p

        msg_chunks = bits_to_hide.reshape(-1,p)
        con_chunks = container[:chunks*n].reshape(-1,n)

        for i in range(chunks):
            nat_msg = matrix_h.T @ con_chunks[i] %2
            error = nat_msg ^ msg_chunks[i]
            if not np.any(error):
                continue
            idx = np.argmax((matrix_h == error).all(axis = 1))
            con_chunks[i][idx] ^= 1

        return np.concatenate((con_chunks.flatten(), container[chunks * n:]))
    
    #region Extract
    def extract(self, password_prime: int, stop_sequence: str, message_encryption: str, hide_method: str, p: int, depth:int):
        stop_sequence = list(self._message_to_bitstream(stop_sequence))
        
        message = self._message_exraction(stop_sequence, hide_method, depth, p, message_encryption, password_prime)

        return self._message_decryption(message, message_encryption, password_prime)

    def _message_exraction(self, stop_sequence: str, hide_method: str, depth: int, p: int, message_encryption: str, password_prime: str):
        if hide_method == 'LSB':
            container = self._LSB_container(depth)
            if message_encryption == "Binary XOR":
                stop_sequence = self._message_encryption(stop_sequence,message_encryption,password_prime)
            return self._find_message(stop_sequence, p, container, message_encryption, password_prime)
        
    def _message_assemble(self, message: str):
        chars = []
        for i in range(0, len(message), 8):
            bit_chunk = message[i:i+8]
            byte_string = "".join(map(str, bit_chunk))
            byte_value = int(byte_string, 2)
            chars.append(chr(byte_value))
        return "".join(chars)
        
    def _message_decryption(self, message: str, message_encryption: str, password_prime: str):
        if message_encryption == 'Binary XOR':
            msg = self._message_encryption(message, message_encryption, password_prime)
            return self._message_assemble(msg)
        elif message_encryption == 'None':
            return self._message_assemble(message)

    def _find_message(self, stop_sequence: str, p: int, container: np.array, message_encryption: str, password_prime: str):
        n = 2**p - 1
        
        stop = np.array(stop_sequence)

        matrix_h = self.build_hiding_matrix(p)

        con_chunks = container[:len(container) //n * n].reshape(-1,n)

        decrypted_con = (con_chunks @ matrix_h %2).flatten()

        len_s = len(stop)
        len_c = len(decrypted_con)

        message = []

        for i in range(0, len_c - len_s + 1):
            window = decrypted_con[i : i + len_s]
            if np.array_equal(window, stop):
                message = decrypted_con[:i]

        return message

        
# img = ImageMedia('TestData/testimage1.png')
# img.hide('Felines, also known as cats, are probably the best things on earth', 5, '66666', 'Binary XOR', 'LSB', 4, 1, 'output.png')

# img = ImageMedia('output.png')
# msg = img.extract(5, '66666', 'Binary XOR', 'LSB', 4, 1)
# print(msg)