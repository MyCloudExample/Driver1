obj-m += uart_final.o

KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

install:
	sudo insmod uart_final.ko

uninstall:
	sudo rmmod uart_final

logs:
	sudo dmesg -w | grep UART_FINAL