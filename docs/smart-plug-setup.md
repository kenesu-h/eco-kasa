# Smart Plug Setup
This documentation will tell you how to setup a Kasa smart plug for use with this
script.

When the instructions refer to "your computer", it's referring to the computer
you plan to run the script on (such as an RPi).

# Prerequisites
You need:
- an eco-kasa installation.

# Instructions
1. Plug your smart plug into any outlet.
2. Connect your computer to the plug's open wifi network.
3. `cd` into eco-kasa's directory and run `kasa --host 192.168.0.1` to make sure
   you can access the smart plug.
4. Make sure you know the exact name of the wifi network you want your smart plug
   to join.
5. Run `kasa --host 192.168.0.1 wifi join <wifi network name> --password <wifi password>`.
6. You should automatically be disconnected from the plug's open wifi network.
7. Double-check the wifi network the plug joined to make sure it's actually
   connected. If not, you might have to repeat these steps.