obj-m += lum.o

all:
	make -C /lib/modules/4.9.24+/build M=$(PWD) modules
clean:
	make -C /lib/modules/4.9.24+/build M=$(PWD) clean

