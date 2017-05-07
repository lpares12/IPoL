*Install linux headers to compile kernel module at raspberry:*
$ uname -r // to get the installed kernel version
Search the linux headers file at: https://www.niksula.hut.fi/~mhiienka/Rpi/linux-headers-rpi/
$ sudo dpkg -i linux-headers-...
(if it fails because of dependencies, install them first and try again)



vi /var/log/messages