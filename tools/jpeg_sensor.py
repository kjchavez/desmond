# Debugging sensor. Emits a jpeg.
import os
from desmond.perception import sensor
from desmond import types

def main():
    print("-"*80)
    print("Debug Image Sensor for Desmond")
    print("   Enter filenames.")
    print("   Enter blank line to quit")
    print("-"*80)
    s = sensor.Sensor("DebugImage")
    while True:
        text = input(">>> ")
        if not text:
            break
        if not os.path.exists(text):
            print("Invalid filename")
            continue

        payload = types.Image()
        with open(text, 'rb') as fp:
            payload.data = fp.read()
            payload.encoding = types.Image.JPEG

        s.emit(payload)

if __name__ == "__main__":
    main()
