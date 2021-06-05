import gpiozero
import time



def do_things():
    print("OKEYYYYY")


button_test = gpiozero.Button(6)
button_test.when_pressed = do_things


while(1):
    print("now what ??")
    time.sleep(2)