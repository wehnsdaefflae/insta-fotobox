# coding=utf-8

from escpos.printer import Usb


def print_text(text: str):
    """
    send text to printer using escpos

    :param text:
    :return:
    """
    p = Usb(0x043d, 0x0124, usb_args=1)
    p.text(text)
    p.cut()


def main():
    print_text("Hello World!")


if __name__ == "__main__":
    main()
