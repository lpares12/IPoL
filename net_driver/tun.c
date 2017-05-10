#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

#include <sys/ioctl.h>

#include <netinet/in.h> // to solve incomplete-type errors
#include <linux/if.h>
#include <linux/if_tun.h>

#include <sys/socket.h>
#include <sys/un.h>

/**
 * Called whenever a reading operation is possible from tun0 file descriptor.
 */
int sendPacket(int tunfd, int senderfd) {
	printf("Ready to receive from tun0\n");
	
	size_t bytes_tosend;
	char toSend[500]; // MTU_SIZE
	// Whenever a packet is sent through tun0, we intercept it
	bytes_tosend = read(tunfd, toSend, sizeof(toSend));
	if(bytes_tosend < 0) {
		printf("Error reading bytes");
		close(tunfd);
		return -1;
	}
	printf("Read %d bytes\n", bytes_tosend);

	// Sending size of the packet
	write(senderfd, (void *)&bytes_tosend, sizeof(bytes_tosend)); // size_t is 4 bytes at rpi
	// Sending the packet
	size_t bytes_written = write(senderfd, toSend, bytes_tosend);
	printf("Bytes written: %zu\n", bytes_written);

	return 0;
}

/**
 * Called whenever a reading operation is possible from receiver.py.
 */
void recvPacket(int tunfd) {
	printf("Ready to send to tun0\n");

	char response[500];
	size_t bytes_tosend;
	// Todo: read from receiver.py
	
	// Todo: Transfer to tun0 interface
	/*
	size_t bytes_written = write(tunfd, response, bytes_tosend);
	if(bytes_written > 0) {
		printf("Written %d bytes\n", bytes_written);
	}
	*/

}

/**
 * @param dev Name of the interface
 * @param flags Flags to be set
 * @return file descriptor or error code
 * 
 */
int tun_alloc(char *dev, int flags) {
	struct ifreq ifr;
	int fd, err;

	char *devPath = "/dev/net/tun";

	if((fd = open(devPath, O_RDWR)) < 0) {
		return -1; // if failed
	}

	memset(&ifr, 0, sizeof(ifr));

	// Fill the ifr struct
	ifr.ifr_flags = flags;
		// If a name was specified
	if(*dev) {
		strncpy(ifr.ifr_name, dev, IFNAMSIZ);
	}

	if((err = ioctl(fd, TUNSETIFF, (void *) &ifr)) < 0) {
		close(fd);
		return -2;
	}

	strcpy(dev, ifr.ifr_name);

	if(ioctl(fd, TUNSETPERSIST, 0) < 0) {
		printf("Error disabling tunsetpersist\n");
		close(fd);
		return -3;
	}

	return fd;
}

/**
 * Function to initialize the IPoL receiver.
 */
void startIPoLReceiver() {
	execlp("python", "python", "/tfg/net_driver/receiver.py", NULL);
}

void startIPoLSender() {
	execlp("python", "python", "/tfg/net_driver/sender.py", NULL);
}

int main() {
	int tunfd; // File descriptor for the tun0 interface
	int receiverfd; // File descriptor for the receiver.py
	int senderfd; // File descriptor for the sender.py
	int maxfd;
	char setup[100], tun_name[IFNAMSIZ], host_ip[15], peer_ip[15];
	fd_set fdset; // Used to know when tunfd or receiverfd are ready for reading
	struct timeval timev;

	///////
	// Init receiver and sender scripts
	int receiver_pid = fork();
	if(receiver_pid == 0) {
		startIPoLReceiver();
	}
	int sender_pid = fork();
	if(sender_pid == 0) {
		startIPoLSender();
	}
	///////

	sleep(1);

	///////
	// Connect with sending script
	struct sockaddr_un server_addr;
	char *server_path = "/tmp/ipol_send";
	if((senderfd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
		printf("Sender socket error\n");
		exit(1);
	}
	memset(&server_addr, 0, sizeof(server_addr));
	server_addr.sun_family = AF_UNIX;
	strncpy(server_addr.sun_path, server_path, sizeof(server_addr.sun_path)-1);

	if(connect(senderfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
		printf("Error connecting to server");
		exit(1);
	}
	///////


	///////
	// Setup interface 
	strcpy(tun_name, "tun0");
	// Allocate a tun interface without added bytes to the IP packet
	tunfd = tun_alloc(tun_name, IFF_TUN | IFF_NO_PI);
	if(tunfd < 0) {
		printf("File descriptor error: %d\n", tunfd);
		exit(1);
	}

	sprintf(setup, "sudo ip link set %s mtu 500 up", tun_name);
	system(setup);

	printf("IP: %s\n", getenv("HOST_IP"));
	printf("IP: %s\n", getenv("PEER_IP"));
	sprintf(host_ip, getenv("HOST_IP")); // Set in .bashrc
	sprintf(peer_ip, getenv("PEER_IP")); // Set in .bashrc
	sprintf(setup, "sudo ip addr add %s dev %s peer %s", host_ip, tun_name, peer_ip);
	system(setup);
	///////

	// maxfd = (tunfd > receiverfd)?tunfd:receiverfd;

	while(1) {
		FD_ZERO(&fdset);
		FD_SET(tunfd, &fdset);
		// FD_SET(receiverfd, &tunfdset);

		timev.tv_sec = 0;
		timev.tv_usec = 0;

		// select(maxfd+1
		if(select(tunfd+1, &fdset, NULL, NULL, &timev) < 0) {
			close(tunfd);
			exit(1);
		}

		if(FD_ISSET(tunfd, &fdset)) {
			sendPacket(tunfd, senderfd);
		}

		//if(FD_ISSET(receiverfd, &fdset)) {
		//	recvPacket();
		//}
	}

	close(tunfd);
	return 0;
}