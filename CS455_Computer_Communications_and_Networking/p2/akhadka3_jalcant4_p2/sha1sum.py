import hashlib
import sys

def main():
    # Get the file name from the command line argument
    if len(sys.argv) != 2:
        print("Try Again! with only one argument!!")
        sys.exit(1)

    filename = sys.argv[1]

    # Open file in binary mode
    with open(filename, 'rb') as f:
        # Read file in chunks to handle large files
        chunk_size = 4096
        sha1 = hashlib.sha1()
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            sha1.update(data)

    # Get the hexadecimal representation of the hash value
    hash_value = sha1.hexdigest()

    print(f"Hash Value: {hash_value}, Filename: {filename}")

main()