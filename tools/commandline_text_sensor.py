from desmond.perception import sensor
from desmond import types

def main():
    print("-"*80)
    print(" Commandline Text Sensor for Desmond")
    print("   (enter blank line to quit)")
    print("-"*80)
    s = sensor.Sensor("Commandline")
    while True:
        text = input(">>> ")
        if not text:
            break
        payload = types.Text()
        payload.value = text
        s.emit(payload)

if __name__ == "__main__":
    main()
