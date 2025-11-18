import tkinter as tk
from login_gui import LoginScreen

def main():
    root = tk.Tk()
    root.title("AI Restaurant Order & Delivery System")
    root.geometry("900x600")

    LoginScreen(root)

    root.mainloop()

if __name__ == "__main__":
    main()
