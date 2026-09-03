import sys
import os

def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} input_file blob_name output_c output_h")
        sys.exit(1)
    in_file, blob_name, out_c, out_h = sys.argv[1:5]
    if not os.path.isfile(in_file):
        print(f"Input file not found: {in_file}")
        sys.exit(1)
    with open(in_file, 'rb') as f:
        data = f.read()
    arr = ', '.join(f'0x{b:02X}' for b in data)
    base = os.path.basename(out_h)
    with open(out_c, 'w') as f:
        f.write(f'#include "{base}"\n')
        f.write(f'const unsigned char {blob_name}[] = {{ {arr} }};\n')
        f.write(f'const unsigned int {blob_name}_size = {len(data)};\n')
    with open(out_h, 'w') as f:
        f.write(f'extern const unsigned char {blob_name}[];\n')
        f.write(f'extern const unsigned int {blob_name}_size;\n')

if __name__ == '__main__':
    main()
