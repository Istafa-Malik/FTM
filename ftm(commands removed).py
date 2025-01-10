import serial
import time

def process_buffer(buffer):
    """
    Process the 24-byte buffer and extract relevant data.
    """
    if len(buffer) != 24:
        print("Incomplete buffer received. Skipping...")
        return

    # Display full buffer in hexadecimal
    print("Buffer Received:", ' '.join(f'{byte:02X}' for byte in buffer))

    # Extract high and low byte values
    high_byte = (buffer[6] << 8) & 0xFF00
    low_byte = buffer[7] & 0xFF
    combined_value = high_byte | low_byte
    print(f"High Byte: {buffer[6]:02X}, Low Byte: {buffer[7]:02X}, Combined Value: {combined_value}")

    # Observe changes in the first and last bytes of the buffer
    print(f"First Byte: {buffer[0]:02X}, Last Byte: {buffer[23]:02X}")
    

def read_from_mcu(port):
    """
    Read 24-byte buffers from the microcontroller and process them.
    """
    try:
        with serial.Serial(port, baudrate=115200, timeout=1) as ser:
            print(f"Connected to {port}")
            time.sleep(2)  # Allow time for connection to establish

            while True:
                if ser.in_waiting >= 24:  # Wait until a full buffer is available
                    buffer = ser.read(24)  # Read exactly 24 bytes
                    process_buffer(buffer)

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    port = "COM4"  # Replace with the correct port
    read_from_mcu(port)
