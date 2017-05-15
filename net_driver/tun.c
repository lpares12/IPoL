#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

#include <sys/ioctl.h>

#include <netinet/in.h> // to solve incomplete-type errors
#include <linux/if.h>
#include <linux/if_tun.h>

// For the unix sockets
#include <sys/socket.h>
#include <sys/un.h>
// To change the priority
#include <sys/time.h>
#include <sys/resource.h>

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
		close(senderfd);
		return -1;
	}
	printf("Read %d bytes\n", bytes_tosend);

	// Sending the packet
	size_t bytes_written = write(senderfd, toSend, bytes_tosend);
	if(bytes_written != bytes_tosend) {
		printf("Wrote less bytes than expected\n");
		return -2;
	}

	return 0;
}

/**
 * Called whenever a reading operation is possible from receiver.py.
 */
int recvPacket(int tunfd, int receiverfd) {
	printf("Ready to send to tun0\n");

	char response[500];
	size_t bytes_tosend;

	// Read from receiver.py
	bytes_tosend = read(receiverfd, response, sizeof(response));
	if(bytes_tosend <= 0) {
		printf("Received %d bytes from receiver. This is a disconnection.\n", bytes_tosend);
		close(tunfd);
		close(receiverfd);
		return -1;
	}
	else {
		printf("Received %d bytes from other host\n", bytes_tosend);

		// Transfer to tun0
		size_t bytes_written = write(tunfd, response, bytes_tosend);
		if(bytes_written > 0) {
			printf("Written %d bytes\n", bytes_written);
		}
	}

	return 0;
}

/**
 * Listen for connections on unix socket and connect to receiver.py
 * Returns the file descriptor of receiver.py
 * Note: receiver must be running and trying to connect!
 */
int connectWithReceiver() {
	int serverfd, receiverfd, len;
	struct sockaddr_un server_addr, client_addr;
	
	if((serverfd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
		printf("Receiver socket error\n");
		exit(1);
	}
	server_addr.sun_family = AF_UNIX;
	strcpy(server_addr.sun_path, "/tmp/ipol_recv");
	unlink(server_addr.sun_path);
	len = strlen(server_addr.sun_path) + sizeof(server_addr.sun_family);
	bind(serverfd, (struct sockaddr*)&server_addr, len);
	listen(serverfd, 1);
	len = sizeof(struct sockaddr_un);
	receiverfd = accept(serverfd, (struct sockaddr*)&client_addr, &len);

	if(receiverfd < 0) {
		printf("Error getting a connection from receiver\n");
		exit(1);
	}
	return receiverfd;
}

/**
 * Connects to the sender.py unix socket.
 * Returns the file descriptor of the connection with sender.py
 * Note: sender server must be initialized
 */
int connectWithSender() {
	int senderfd;
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
		printf("Error connecting to server\n");
		exit(1);
	}
	return senderfd;
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
		printf("Error %d", err);
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
 * Method to initialize the IPoL receiver.
 */
void startIPoLReceiver() {
	execlp("python", "python", "/tfg/net_driver/receiver.py", NULL);
}

/**
 * Method to initialize the IPoL sender.
 */
void startIPoLSender() {
	execlp("python", "python", "/tfg/net_driver/sender.py", NULL);
}

int main() {
	int tunfd; // File descriptor for the tun0 interface
	int receiverfd; // File descriptor for the receiver.py
	int senderfd; // File descriptor for the sender.py
	int maxfd; // For the select method
	char setup[100], tun_name[IFNAMSIZ], host_ip[15], peer_ip[15];
	fd_set fdset; // Used to know when tunfd or receiverfd are ready for reading
	struct timeval timev;

	setpriority(PRIO_PROCESS, 0, -20);

	remove("/tmp/ipol.log"); // Delete the old logger if exists

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

	receiverfd = connectWithReceiver();
	senderfd = connectWithSender();

	///////
	// Setup interface 
	strcpy(tun_name, "tun0");
	// Allocate a tun interface (without added bytes to the IP packet)
	tunfd = tun_alloc(tun_name, IFF_TUN | IFF_NO_PI);
	if(tunfd < 0) {
		printf("File descriptor error: %d\n", tunfd);
		exit(1);
	}

	sprintf(setup, "sudo ip link set %s mtu 500 up", tun_name);
	system(setup);

	sprintf(host_ip, getenv("HOST_IP")); // Set in .bashrc
	sprintf(peer_ip, getenv("PEER_IP")); // Set in .bashrc
	sprintf(setup, "sudo ip addr add %s dev %s peer %s", host_ip, tun_name, peer_ip);
	system(setup);
	///////

	maxfd = (tunfd > receiverfd)?tunfd:receiverfd;

	while(1) {
		FD_ZERO(&fdset);
		FD_SET(tunfd, &fdset);
		FD_SET(receiverfd, &fdset);

		timev.tv_sec = 0;
		timev.tv_usec = 0;

		if(select(maxfd+1, &fdset, NULL, NULL, &timev) < 0) {
			close(tunfd);
			close(receiverfd);
			close(senderfd);
			exit(1);
		}

		if(FD_ISSET(tunfd, &fdset)) {
			if(sendPacket(tunfd, senderfd) < 0)
			{
				close(tunfd);
				close(senderfd);
				close(receiverfd);
				return 0;
			}
		}

		if(FD_ISSET(receiverfd, &fdset)) {
			if(recvPacket(tunfd, receiverfd) < 0)
			{
				close(tunfd);
				close(senderfd);
				close(receiverfd);
				return 0;
			}
		}
	}

	close(receiverfd);
	close(senderfd);
	close(tunfd);
	return 0;
}