from pynput import keyboard
import time

print("Testing hotkey...")
print("Press Ctrl+Space to test")

ctrl_pressed = False
space_pressed = False

def on_press(key):
    global ctrl_pressed, space_pressed
    try:
        if hasattr(key, 'char') and key.char == ' ':
            space_pressed = True
            print("Space pressed")
        elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed = True
            print("Ctrl pressed")
        
        if ctrl_pressed and space_pressed:
            print("Hotkey detected!")
            ctrl_pressed = False
            space_pressed = False
    except Exception as e:
        print(f"Error: {e}")

def on_release(key):
    global ctrl_pressed, space_pressed
    try:
        if hasattr(key, 'char') and key.char == ' ':
            space_pressed = False
        elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed = False
    except Exception as e:
        pass

listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release
)
listener.start()

print("Listening... Press Ctrl+C to exit")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    listener.stop()
    print("\nExiting...")