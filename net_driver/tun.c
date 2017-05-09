#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

#include <sys/ioctl.h>

#include <netinet/in.h> // to solve incomplete-type errors
#include <linux/if.h>
#include <linux/if_tun.h>


char* fake_ping_response(char *packet, size_t size) {
	char src_ip[4], dst_ip[4], identifier[2], sequence_number[2];

	memcpy(&src_ip, (packet+12), 4);
	memcpy(&dst_ip, (packet+16), 4);
	printf("Src IP: %d.%d.%d.%d\n", src_ip[0], src_ip[1], src_ip[2], src_ip[3]);
	printf("Dst IP: %d.%d.%d.%d\n", dst_ip[0], dst_ip[1], dst_ip[2], dst_ip[3]);

	memcpy(&identifier, (packet+24), 2);
	memcpy(&sequence_number, (packet+26), 2);

	char *response = (char *) malloc(size);

	if(response == NULL) {
		printf("Error allocating memory for response\n");
	} else {
		memset(response, 0, size);
		memcpy(response, packet, size);

		memcpy((response+12), &dst_ip, 4);
		memcpy((response+16), &src_ip, 4);
		response[8] = 255;
	}
	return response;
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

	return fd;
}

int main() {
	int tunfd;
	char setup[100], tun_name[IFNAMSIZ], host_ip[15], peer_ip[15];
	strcpy(tun_name, "tun0");

	// Allocate a tun interface without added bytes to the IP packet
	tunfd = tun_alloc(tun_name, IFF_TUN | IFF_NO_PI);
	if(tunfd < 0) {
		printf("File descriptor error: %d\n", tunfd);
		exit(1);
	}


	if(ioctl(tunfd, TUNSETPERSIST, 0) < 0) {
		printf("Error disabling tunsetpersist\n");
		exit(1);
	}

	// Setup interface
	sprintf(setup, "sudo ip link set %s mtu 500 up", tun_name);
	system(setup);
	/*sprintf(setup, "sudo ip link set %s mtu 40", tun_name);
	system(setup);*/

	sprintf(host_ip, "10.0.0.1"); // Should be taken from environment variable
	sprintf(peer_ip, "10.0.0.2"); // Should be taken from environment variable
	sprintf(setup, "sudo ip addr add %s dev %s peer %s", host_ip, tun_name, peer_ip);
	system(setup);
	//

	while(1) {
		size_t bytes_read;
		char buffer[500]; // MTU_SIZE
		bytes_read = read(tunfd, buffer, sizeof(buffer));
		if(bytes_read < 0) {
			printf("Error reading bytes");
			close(tunfd);
			exit(1);
		}

		printf("Read %d bytes\n", bytes_read);

		unsigned int protocol = buffer[9];
		if(protocol == 1) {
			unsigned int type = buffer[20];
			if(type == 8) {
				printf("Received a ping\n");
				char *response = fake_ping_response(&buffer[0], bytes_read);
				size_t bytes_written = write(tunfd, response, bytes_read);
				if(bytes_written > 0) {
					printf("Written %d bytes\n");
				}
			} else {
				printf("Type unknown\n");
			}
		}
		
		/*
		int i;
		for(i = 0; i < bytes_read; i++) {
			printf("0x%02x ", buffer[i]);
		}
		printf("\n");
		*/
	}

	close(tunfd);
	return 0;
}

/*
TODO:
	- Create  two threads
		- One will read the interface read(); and when a new message
			appears to be sent through it, it will redirect it to outgoing.py
		- One will be listening for an interrupt from incoming.py (which will send
			an interrupt whenever a packet is read from the sensor) and will redirect
			it to /dev/net/tun0 for outgoing
*/